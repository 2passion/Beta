"""Execute MVP Test 4 Bottleneck scenarios with the existing Common Harness."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
CORE_ROOT = PROJECT_ROOT / "02_Core"
if not (CORE_ROOT / "beta_core").is_dir():
    raise RuntimeError(f"unable to locate 02_Core/beta_core from executor file: {THIS_FILE}")
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from beta_core.cli import run_task
from beta_core.event_store import EventStore
from beta_core.model import new_id, sha256_file, utc_now


ID_PATTERN = re.compile(r"\b(?:RUN|EVT)-[0-9a-fA-F-]{36}\b")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")


def read_events(directory: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def normalize_reason(reason: str, runtime_root: Path | None = None) -> str:
    normalized = reason
    if runtime_root is not None:
        normalized = normalized.replace(str(runtime_root), "<RUNTIME_ROOT>")
    normalized = ID_PATTERN.sub("<ID>", normalized)
    return " ".join(normalized.split()).casefold()


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def fingerprint_inputs(
    failure_class: str,
    failing_component: str,
    normalized_reason: str,
    identity: str,
    criteria: Any,
    plan_version: str,
) -> dict[str, Any]:
    return {
        "failure_class": failure_class,
        "failing_component": failing_component,
        "normalized_reason": normalized_reason,
        "identity": identity,
        "relevant": {"criteria": criteria, "plan_version": plan_version},
    }


def fix_signature(plan: dict[str, Any]) -> str:
    relevant = {
        "executor": plan["executor"],
        "validators": plan["required_validators"],
        "steps": plan["steps"],
        "completion_criteria": plan["completion_criteria"],
    }
    return stable_hash(relevant)


def task_plan(
    scenario: str,
    version: str,
    executor_path: Path,
    validator_path: Path,
    criteria: dict[str, Any],
    change_reason_ref: str,
) -> dict[str, Any]:
    return {
        "task_id": f"TASK-MVP4-{scenario}",
        "plan_version": version,
        "order_id": "Order-025",
        "change_reason_ref": change_reason_ref,
        "write_owner": "Codex",
        "write_scope": ["04_Evidence/mvp_test_4/scenarios"],
        "shared_resources": [],
        "depends_on": [],
        "steps": [{"step_id": f"BOTTLENECK-{scenario}-001", "action": "execute deterministic scenario"}],
        "executor": {
            "path": executor_path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256_file(executor_path),
        },
        "required_validators": [{
            "validator_id": "VAL-BOTTLENECK-CHECK",
            "path": validator_path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256_file(validator_path),
            "criteria": criteria,
        }],
        "completion_criteria": ["deterministic scenario result is independently validated"],
        "permissions": {"subprocess": "approved fixture paths only", "network": False},
    }


def validation_reason(event: dict[str, Any]) -> str:
    payload = event["payload"]
    for source in (payload.get("stdout", ""), payload.get("stderr", "")):
        if not source:
            continue
        try:
            decoded = json.loads(source)
        except json.JSONDecodeError:
            return source
        if isinstance(decoded, dict) and isinstance(decoded.get("reason"), str):
            return decoded["reason"]
    return f"validator exited with code {payload.get('exit_code')}"


def record_failure(directory: Path, result: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    events = read_events(directory)
    run_id = result["run_id"]
    execution_errors = [event for event in events if event["run_id"] == run_id and event["type"] == "EXECUTION_ERROR"]
    validations = [event for event in events if event["run_id"] == run_id and event["type"] == "VALIDATION_RESULT"]
    if execution_errors:
        failure_class = "EXECUTION_ERROR"
        component = "executor"
        event = execution_errors[-1]
        reason = f"executor exited with code {event['payload'].get('exit_code')}"
        identity = plan["executor"]["sha256"]
        criteria: Any = None
    elif validations:
        event = validations[-1]
        status = event["payload"].get("status")
        failure_class = "VALIDATION_ERROR" if status == "ERROR" else "VALIDATION_FAIL"
        component = "validator"
        reason = validation_reason(event)
        identity = event["payload"].get("validator_id", "VAL-UNKNOWN")
        criteria = plan["required_validators"][0].get("criteria")
    else:
        raise RuntimeError("scenario did not produce a root failure")
    normalized = normalize_reason(reason, directory)
    inputs = fingerprint_inputs(failure_class, component, normalized, identity, criteria, plan["plan_version"])
    payload = {
        "failure_class": failure_class,
        "fingerprint": stable_hash(inputs),
        "normalized_reason": normalized,
        "source_run_id": run_id,
        "plan_version": plan["plan_version"],
        "fingerprint_inputs": inputs,
    }
    EventStore(directory / "events.jsonl").append(
        "FAILURE_FINGERPRINT",
        task_id=plan["task_id"],
        run_id=run_id,
        plan_version=plan["plan_version"],
        actor_role="Bottleneck",
        payload=payload,
    )
    return payload


def record_retry_decision(
    directory: Path,
    plan: dict[str, Any],
    failure: dict[str, Any],
    prior_run_ids: list[str],
    candidate_plan: dict[str, Any] | None,
    new_run_limit: int,
) -> dict[str, Any]:
    old_signature = fix_signature(plan)
    new_signature = fix_signature(candidate_plan) if candidate_plan else old_signature
    change_reason_ref = candidate_plan.get("change_reason_ref") if candidate_plan else None
    version_changed = bool(candidate_plan and candidate_plan["plan_version"] != plan["plan_version"])
    fix_changed = bool(candidate_plan and new_signature != old_signature)
    has_reason = isinstance(change_reason_ref, str) and bool(change_reason_ref.strip())
    candidate_version = candidate_plan["plan_version"] if candidate_plan else plan["plan_version"]
    existing_events = read_events(directory)
    observed_new_version_run_count = sum(
        event["type"] == "RUN_STARTED"
        and event.get("task_id") == plan["task_id"]
        and event.get("plan_version") == candidate_version
        for event in existing_events
    )
    below_limit = observed_new_version_run_count < new_run_limit
    allowed = version_changed and fix_changed and has_reason and below_limit
    payload = {
        "fingerprint": failure["fingerprint"],
        "prior_matching_run_ids": prior_run_ids,
        "change_reason_ref": change_reason_ref,
        "decision": "ALLOW_NEW_RUN" if allowed else "BLOCK_BLIND_RETRY",
        "reason": "new plan version, tracked reason, and relevant fix" if allowed else "same fingerprint with no relevant plan or fix change",
        "from_plan_version": plan["plan_version"],
        "to_plan_version": candidate_version,
        "prior_fix_signature": old_signature,
        "candidate_fix_signature": new_signature,
        "version_changed": version_changed,
        "fix_changed": fix_changed,
        "run_limit": new_run_limit,
        "observed_new_version_run_count": observed_new_version_run_count,
        "below_limit": below_limit,
    }
    EventStore(directory / "events.jsonl").append(
        "RETRY_DECISION",
        task_id=plan["task_id"],
        run_id=new_id("DECISION"),
        plan_version=payload["to_plan_version"],
        actor_role="Bottleneck",
        payload=payload,
    )
    return payload


def record_decision_evidence(directory: Path, name: str, value: dict[str, Any]) -> Path:
    path = directory / name
    write_json(path, {"created_at": utc_now(), **value})
    return path


def runtime_state(directory: Path) -> dict[str, int]:
    events = read_events(directory) if (directory / "events.jsonl").is_file() else []
    run_root = directory / "runs"
    return {
        "run_started": sum(event["type"] == "RUN_STARTED" for event in events),
        "run_directories": sum(path.is_dir() for path in run_root.iterdir()) if run_root.is_dir() else 0,
        "runtime_evidence": len(list(directory.glob("EVD-*.json"))),
    }


def execute_decision_controlled_retry(
    directory: Path,
    baseline_plan: dict[str, Any],
    baseline_path: Path,
    candidate_plan: dict[str, Any],
    candidate_path: Path,
    new_run_limit: int,
    evidence_name: str,
) -> dict[str, Any]:
    write_json(baseline_path, baseline_plan)
    baseline_result = run_task(baseline_path, PROJECT_ROOT, directory)
    failure = record_failure(directory, baseline_result, baseline_plan)
    write_json(candidate_path, candidate_plan)
    decision = record_retry_decision(
        directory,
        baseline_plan,
        failure,
        [baseline_result["run_id"]],
        candidate_plan,
        new_run_limit,
    )
    before_candidate = runtime_state(directory)
    candidate_result = None
    run_task_call_count = 0
    if decision["decision"] == "ALLOW_NEW_RUN":
        candidate_result = run_task(candidate_path, PROJECT_ROOT, directory)
        run_task_call_count = 1
    after_candidate = runtime_state(directory)
    enforcement = {
        "run_task_call_count": run_task_call_count,
        "run_started_delta": after_candidate["run_started"] - before_candidate["run_started"],
        "run_directory_delta": after_candidate["run_directories"] - before_candidate["run_directories"],
        "runtime_evidence_delta": after_candidate["runtime_evidence"] - before_candidate["runtime_evidence"],
    }
    record_decision_evidence(
        directory,
        evidence_name,
        {
            "failed_result": baseline_result,
            "failure": failure,
            "decision": decision,
            "candidate_result": candidate_result,
            "enforcement": enforcement,
        },
    )
    return {
        "baseline_result": baseline_result,
        "failure": failure,
        "decision": decision,
        "candidate_result": candidate_result,
        "enforcement": enforcement,
    }


def retry_count(directory: Path, kind: str, task_id: str, plan_version: str) -> dict[str, Any]:
    events = read_events(directory) if (directory / "events.jsonl").is_file() else []
    starts = [
        event for event in events
        if event["type"] == "RUN_STARTED"
        and event.get("task_id") == task_id
        and event.get("plan_version") == plan_version
    ]
    if kind == "VALIDATOR_ERROR":
        counted = [
            event for event in events
            if event["type"] == "VALIDATION_RESULT"
            and event.get("task_id") == task_id
            and event.get("plan_version") == plan_version
            and event.get("payload", {}).get("status") == "ERROR"
        ]
    elif kind == "EXECUTION_ERROR":
        counted = [
            event for event in events
            if event["type"] == "EXECUTION_ERROR"
            and event.get("task_id") == task_id
            and event.get("plan_version") == plan_version
        ]
    else:
        counted = starts
    run_root = directory / "runs"
    run_directories = sorted(path for path in run_root.iterdir() if path.is_dir()) if run_root.is_dir() else []
    evidence_files = sorted(directory.glob("EVD-*.json"))
    return {
        "event_count": len(counted),
        "run_started_count": len(starts),
        "run_directory_count": len(run_directories),
        "runtime_evidence_count": len(evidence_files),
        "source_run_ids": [event["run_id"] for event in starts],
    }


def execute_with_fixture_limit(
    kind: str,
    directory: Path,
    plan_path: Path,
    plan: dict[str, Any],
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for _ in range(limit + 1):
        observed = retry_count(directory, kind, plan["task_id"], plan["plan_version"])
        allowed = observed["event_count"] < limit
        decision_run_id = new_id("LIMIT-DECISION")
        payload = {
            "kind": kind,
            "fixture_limit": limit,
            "observed_event_count": observed["event_count"],
            "observed_run_started_count": observed["run_started_count"],
            "observed_run_directory_count": observed["run_directory_count"],
            "observed_runtime_evidence_count": observed["runtime_evidence_count"],
            "prior_run_ids": observed["source_run_ids"],
            "requested_attempt_number": observed["event_count"] + 1,
            "decision": "ALLOW_NEW_RUN" if allowed else "BLOCK_LIMIT",
            "user_gate_required_reason": None if allowed else f"{kind} fixture limit exceeded",
            "user_gate_workflow_started": False,
        }
        EventStore(directory / "events.jsonl").append(
            "RETRY_LIMIT_DECISION",
            task_id=plan["task_id"],
            run_id=decision_run_id,
            plan_version=plan["plan_version"],
            actor_role="Bottleneck",
            payload=payload,
        )
        decisions.append({"decision_run_id": decision_run_id, **payload})
        if not allowed:
            break
        results.append(run_task(plan_path, PROJECT_ROOT, directory))
    record_decision_evidence(
        directory,
        "retry_limit_evidence.json",
        {"kind": kind, "fixture_limit": limit, "decisions": decisions, "runtime_results": results},
    )
    return decisions, results


def execute_scenarios(scenario_root: Path) -> dict[str, Any]:
    fixture_root = THIS_FILE.parent
    executor_success = fixture_root / "executor_success.py"
    executor_error = fixture_root / "executor_error.py"
    validator_success = fixture_root / "validator_success.py"
    validator_fail = fixture_root / "validator_fail.py"
    limits = json.loads((fixture_root / "bottleneck_retry_limits.json").read_text(encoding="utf-8"))
    directories = {
        "A": scenario_root / "a_validation_fail_blind_block",
        "B": scenario_root / "b_changed_plan_new_run",
        "C": scenario_root / "c_validator_error_blind_block",
        "D": scenario_root / "d_execution_error_blind_block",
        "E": scenario_root / "e_distinct_failure",
        "LIMIT": scenario_root / "retry_limits",
    }

    fail_criteria = {"mode": "fail"}
    plan_a = task_plan("A", "1.0", executor_success, validator_fail, fail_criteria, "Order-025-Scenario-A-Baseline")
    path_a = directories["A"] / "scenario_plan_1_0.json"
    write_json(path_a, plan_a)
    result_a = run_task(path_a, PROJECT_ROOT, directories["A"])
    failure_a = record_failure(directories["A"], result_a, plan_a)
    decision_a = record_retry_decision(directories["A"], plan_a, failure_a, [result_a["run_id"]], None, limits["plan_version_product_run_max_attempts"])
    record_decision_evidence(directories["A"], "blind_retry_evidence.json", {"source_result": result_a, "failure": failure_a, "decision": decision_a})

    plan_b1 = task_plan("B", "1.0", executor_success, validator_fail, fail_criteria, "Order-025-Scenario-B-Baseline")
    plan_b2 = task_plan("B", "1.1", executor_success, validator_success, {"expected_value": "phase1-ok"}, "Order-025-Scenario-B-Fix")
    path_b1 = directories["B"] / "scenario_plan_1_0.json"
    path_b2 = directories["B"] / "scenario_plan_1_1.json"
    scenario_b = execute_decision_controlled_retry(
        directories["B"],
        plan_b1,
        path_b1,
        plan_b2,
        path_b2,
        limits["plan_version_product_run_max_attempts"],
        "new_run_evidence.json",
    )
    result_b1 = scenario_b["baseline_result"]
    failure_b = scenario_b["failure"]
    decision_b = scenario_b["decision"]
    result_b2 = scenario_b["candidate_result"]

    plan_c = task_plan("C", "1.0", executor_success, validator_fail, {"mode": "error"}, "Order-025-Scenario-C-Baseline")
    path_c = directories["C"] / "scenario_plan_1_0.json"
    write_json(path_c, plan_c)
    result_c = run_task(path_c, PROJECT_ROOT, directories["C"])
    failure_c = record_failure(directories["C"], result_c, plan_c)
    decision_c = record_retry_decision(directories["C"], plan_c, failure_c, [result_c["run_id"]], None, limits["plan_version_product_run_max_attempts"])
    record_decision_evidence(directories["C"], "blind_retry_evidence.json", {"source_result": result_c, "failure": failure_c, "decision": decision_c})

    plan_d = task_plan("D", "1.0", executor_error, validator_success, {"expected_value": "phase1-ok"}, "Order-025-Scenario-D-Baseline")
    path_d = directories["D"] / "scenario_plan_1_0.json"
    write_json(path_d, plan_d)
    result_d = run_task(path_d, PROJECT_ROOT, directories["D"])
    failure_d = record_failure(directories["D"], result_d, plan_d)
    decision_d = record_retry_decision(directories["D"], plan_d, failure_d, [result_d["run_id"]], None, limits["plan_version_product_run_max_attempts"])
    record_decision_evidence(directories["D"], "blind_retry_evidence.json", {"source_result": result_d, "failure": failure_d, "decision": decision_d})

    comparison = {
        "left_failure_class": failure_a["failure_class"],
        "left_fingerprint": failure_a["fingerprint"],
        "right_failure_class": failure_d["failure_class"],
        "right_fingerprint": failure_d["fingerprint"],
        "decision": "DISTINCT_FAILURE",
        "blind_retry_blocked": False,
    }
    EventStore(directories["E"] / "events.jsonl").append(
        "FAILURE_COMPARISON",
        task_id="TASK-MVP4-E",
        run_id=new_id("COMPARE"),
        plan_version="1.0",
        actor_role="Bottleneck",
        payload=comparison,
    )
    record_decision_evidence(directories["E"], "comparison_evidence.json", comparison)

    limit_directories = {
        "VALIDATOR_ERROR": directories["LIMIT"] / "validator_error",
        "EXECUTION_ERROR": directories["LIMIT"] / "execution_error",
        "PRODUCT_NEW_RUN": directories["LIMIT"] / "product_new_run",
    }
    limit_specs = {
        "VALIDATOR_ERROR": (
            task_plan("LIMIT-VALIDATOR", "1.0", executor_success, validator_fail, {"mode": "error"}, "Order-027-Retry-Limit-Validator"),
            limits["validator_error_max_attempts"],
        ),
        "EXECUTION_ERROR": (
            task_plan("LIMIT-EXECUTION", "1.0", executor_error, validator_success, {"expected_value": "phase1-ok"}, "Order-027-Retry-Limit-Execution"),
            limits["execution_error_max_attempts"],
        ),
        "PRODUCT_NEW_RUN": (
            task_plan("LIMIT-PRODUCT", "1.0", executor_success, validator_success, {"expected_value": "phase1-ok"}, "Order-027-Retry-Limit-Product"),
            limits["plan_version_product_run_max_attempts"],
        ),
    }
    limit_records: list[dict[str, Any]] = []
    limit_results: dict[str, list[dict[str, Any]]] = {}
    for kind, (limit_plan, limit) in limit_specs.items():
        plan_path = limit_directories[kind] / "scenario_plan_1_0.json"
        write_json(plan_path, limit_plan)
        decisions, results = execute_with_fixture_limit(kind, limit_directories[kind], plan_path, limit_plan, limit)
        limit_records.extend(decisions)
        limit_results[kind] = results

    return {
        "directories": {key: str(path.resolve()) for key, path in directories.items()},
        "results": {"A": result_a, "B_FAIL": result_b1, "B_FIX": result_b2, "C": result_c, "D": result_d},
        "failures": {"A": failure_a, "B": failure_b, "C": failure_c, "D": failure_d},
        "decisions": {"A": decision_a, "B": decision_b, "C": decision_c, "D": decision_d, "E": comparison},
        "retry_limits": limit_records,
        "retry_limit_directories": {key: str(value.resolve()) for key, value in limit_directories.items()},
        "retry_limit_results": limit_results,
    }


def main() -> int:
    output_path = Path(sys.argv[1]).resolve()
    outer_evidence_dir = output_path.parents[2]
    scenario_root = outer_evidence_dir.parent / "scenarios" / new_id("SCN")
    scenario = execute_scenarios(scenario_root)
    output = {
        "mvp_test_id": "MVP-TEST-4",
        "mvp_test_name": "Bottleneck",
        "test_plan_id": "MVP-TEST-4-BOTTLENECK",
        "test_plan_version": "1.2",
        "created_at": utc_now(),
        "scenario_root": str(scenario_root.resolve()),
        "scenario_evidence_dirs": scenario["directories"],
        "scenario_results": scenario["results"],
        "failure_fingerprints": scenario["failures"],
        "retry_decisions": scenario["decisions"],
        "retry_limits": scenario["retry_limits"],
        "retry_limit_directories": scenario["retry_limit_directories"],
        "retry_limit_results": scenario["retry_limit_results"],
    }
    write_json(output_path, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
