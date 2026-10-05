"""Independent MVP Test 4 Validator for failure fingerprints and retry decisions."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ID_PATTERN = re.compile(r"\b(?:RUN|EVT)-[0-9a-fA-F-]{36}\b")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def read_events(directory: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def event_payloads(events: list[dict[str, Any]], event_type: str) -> list[dict[str, Any]]:
    return [event["payload"] for event in events if event.get("type") == event_type]


def runtime_evidence(directory: Path) -> list[dict[str, Any]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(directory.glob("EVD-*.json"))]


def run_directories(directory: Path) -> list[Path]:
    root = directory / "runs"
    return sorted(path for path in root.iterdir() if path.is_dir()) if root.is_dir() else []


def has_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        if any(key in {"run_id", "event_id", "time", "timestamp", "runtime_root", "absolute_path"} for key in value):
            return True
        return any(has_forbidden_key(item) for item in value.values())
    if isinstance(value, list):
        return any(has_forbidden_key(item) for item in value)
    return False


def validate_failure(label: str, payload: dict[str, Any] | None, expected_class: str, failures: list[str]) -> str | None:
    if payload is None:
        failures.append(f"Scenario {label} FAILURE_FINGERPRINT missing")
        return None
    inputs = payload.get("fingerprint_inputs")
    require(isinstance(inputs, dict), f"Scenario {label} fingerprint inputs missing", failures)
    if not isinstance(inputs, dict):
        return None
    require(not has_forbidden_key(inputs), f"Scenario {label} fingerprint includes volatile field", failures)
    require(inputs.get("failure_class") == expected_class, f"Scenario {label} failure class mismatch", failures)
    require(payload.get("failure_class") == expected_class, f"Scenario {label} payload failure class mismatch", failures)
    require(inputs.get("normalized_reason") == payload.get("normalized_reason"), f"Scenario {label} normalized reason mismatch", failures)
    require(not ID_PATTERN.search(str(inputs.get("normalized_reason", ""))), f"Scenario {label} normalized reason includes Run/Event ID", failures)
    expected = stable_hash(inputs)
    require(payload.get("fingerprint") == expected, f"Scenario {label} fingerprint mismatch", failures)
    return payload.get("fingerprint")


def validate_blind_block(
    label: str,
    directory: Path,
    expected_class: str,
    failures: list[str],
) -> tuple[str | None, list[dict[str, Any]]]:
    events = read_events(directory)
    starts = [event for event in events if event["type"] == "RUN_STARTED"]
    validations = event_payloads(events, "VALIDATION_RESULT")
    fingerprints = event_payloads(events, "FAILURE_FINGERPRINT")
    decision_events = [event for event in events if event["type"] == "RETRY_DECISION"]
    decisions = [event["payload"] for event in decision_events]
    require(len(starts) == 1, f"Scenario {label} blind retry must not create a second RUN_STARTED", failures)
    require(len(fingerprints) == 1, f"Scenario {label} must have one failure fingerprint", failures)
    require(len(decisions) == 1, f"Scenario {label} must have one retry decision", failures)
    fingerprint = validate_failure(label, fingerprints[0] if fingerprints else None, expected_class, failures)
    if decisions:
        decision = decisions[0]
        require(decision.get("fingerprint") == fingerprint, f"Scenario {label} retry fingerprint mismatch", failures)
        require(decision.get("decision") == "BLOCK_BLIND_RETRY", f"Scenario {label} blind retry must BLOCK", failures)
        require(decision.get("change_reason_ref") is None, f"Scenario {label} blind retry reason must be null", failures)
        require(not decision.get("version_changed"), f"Scenario {label} version must not change", failures)
        require(not decision.get("fix_changed"), f"Scenario {label} fix must not change", failures)
        require(decision.get("prior_matching_run_ids") == [starts[0]["run_id"]], f"Scenario {label} prior Run link mismatch", failures)
        require(decision.get("below_limit") is True, f"Scenario {label} Retry Limit precondition missing", failures)
        blocked_attempt_id = decision_events[0]["run_id"]
        require(not (directory / "runs" / blocked_attempt_id).exists(), f"Scenario {label} blocked retry Run directory must be absent", failures)
        require(not any(event["type"] == "RUN_STARTED" and event["run_id"] == blocked_attempt_id for event in events), f"Scenario {label} blocked retry must not RUN_STARTED", failures)
        require(not any(item.get("run_id") == blocked_attempt_id for item in runtime_evidence(directory)), f"Scenario {label} blocked retry Runtime Evidence must be absent", failures)
    require(any(event["type"] == "GATE_DECISION" and event["payload"].get("decision") == "BLOCK" for event in events), f"Scenario {label} Gate BLOCK missing", failures)
    require((directory / "blind_retry_evidence.json").is_file(), f"Scenario {label} blind retry Evidence missing", failures)
    source_run_ids = {event["run_id"] for event in starts}
    actual_run_ids = {path.name for path in run_directories(directory)}
    require(actual_run_ids == source_run_ids, f"Scenario {label} actual Run directory set mismatch", failures)
    evidence = runtime_evidence(directory)
    expected_evidence_count = 0 if expected_class == "EXECUTION_ERROR" else 1
    require(len(evidence) == expected_evidence_count, f"Scenario {label} Runtime Evidence presence contract mismatch", failures)
    if evidence:
        require({item.get("run_id") for item in evidence} == source_run_ids, f"Scenario {label} Runtime Evidence Run link mismatch", failures)
    return fingerprint, events


def fix_signature(plan: dict[str, Any]) -> str:
    return stable_hash({
        "executor": plan["executor"],
        "validators": plan["required_validators"],
        "steps": plan["steps"],
        "completion_criteria": plan["completion_criteria"],
    })


def main() -> int:
    result_path = Path(sys.argv[1]).resolve()
    criteria = json.loads(sys.argv[2])
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        project_root = Path(__file__).resolve().parents[2]
        allowed_root = (result_path.parents[3] / "scenarios").resolve()
        directories = {key: Path(value).resolve() for key, value in result["scenario_evidence_dirs"].items()}
        failures: list[str] = []

        require(result.get("mvp_test_id") == criteria.get("mvp_test_id"), "MVP Test ID mismatch", failures)
        require(result.get("mvp_test_name") == criteria.get("mvp_test_name"), "MVP Test name mismatch", failures)
        require(result.get("test_plan_id") == criteria.get("test_plan_id"), "Test Plan ID mismatch", failures)
        require(result.get("test_plan_version") == criteria.get("test_plan_version"), "Test Plan version mismatch", failures)
        require(set(directories) == {"A", "B", "C", "D", "E", "LIMIT"}, "Scenario directory set mismatch", failures)
        for key, directory in directories.items():
            require(directory.is_relative_to(allowed_root), f"Scenario {key} path outside allowed root", failures)

        fp_a, events_a = validate_blind_block("A", directories["A"], "VALIDATION_FAIL", failures)
        validation_a = event_payloads(events_a, "VALIDATION_RESULT")
        require(len(validation_a) == 1 and validation_a[0].get("status") == "FAIL", "Scenario A must distinguish Validation FAIL", failures)
        require(len(event_payloads(events_a, "VALIDATION_STARTED")) == 1, "Scenario A Validator execution count mismatch", failures)
        require(any(event["type"] == "EVIDENCE_RECORDED" for event in events_a), "Scenario A failed Evidence not preserved", failures)

        events_b = read_events(directories["B"])
        starts_b = [event for event in events_b if event["type"] == "RUN_STARTED"]
        vals_b = event_payloads(events_b, "VALIDATION_RESULT")
        fp_b_payloads = event_payloads(events_b, "FAILURE_FINGERPRINT")
        decisions_b = event_payloads(events_b, "RETRY_DECISION")
        fp_b = validate_failure("B", fp_b_payloads[0] if fp_b_payloads else None, "VALIDATION_FAIL", failures)
        require(fp_b == fp_a, "Scenario A/B same failure must have same fingerprint", failures)
        require(len(starts_b) == 2, "Scenario B must have baseline and new Run", failures)
        require({event["plan_version"] for event in starts_b} == {"1.0", "1.1"}, "Scenario B plan versions mismatch", failures)
        require(len(vals_b) == 2 and {item.get("status") for item in vals_b} == {"FAIL", "PASS"}, "Scenario B must preserve FAIL then PASS", failures)
        require(any(event["type"] == "GATE_DECISION" and event["plan_version"] == "1.0" and event["payload"].get("decision") == "BLOCK" for event in events_b), "Scenario B baseline Gate BLOCK missing", failures)
        require(any(event["type"] == "GATE_DECISION" and event["plan_version"] == "1.1" and event["payload"].get("decision") == "PROCEED" for event in events_b), "Scenario B fixed Gate PROCEED missing", failures)
        require(len(decisions_b) == 1, "Scenario B retry decision missing", failures)
        plan_b1 = json.loads((directories["B"] / "scenario_plan_1_0.json").read_text(encoding="utf-8"))
        plan_b2 = json.loads((directories["B"] / "scenario_plan_1_1.json").read_text(encoding="utf-8"))
        if decisions_b:
            decision_b = decisions_b[0]
            require(decision_b.get("decision") == "ALLOW_NEW_RUN", "Scenario B changed plan must allow New Run", failures)
            require(decision_b.get("change_reason_ref") == "Order-025-Scenario-B-Fix", "Scenario B change reason mismatch", failures)
            require(decision_b.get("version_changed") is True, "Scenario B version change missing", failures)
            require(decision_b.get("fix_changed") is True, "Scenario B actual fix change missing", failures)
            require(decision_b.get("prior_fix_signature") == fix_signature(plan_b1), "Scenario B prior fix signature mismatch", failures)
            require(decision_b.get("candidate_fix_signature") == fix_signature(plan_b2), "Scenario B candidate fix signature mismatch", failures)
            require(decision_b.get("prior_fix_signature") != decision_b.get("candidate_fix_signature"), "Scenario B reason-only change must not allow", failures)
        require((directories["B"] / "new_run_evidence.json").is_file(), "Scenario B New Run Evidence missing", failures)
        evidence_b = runtime_evidence(directories["B"])
        require(len(evidence_b) == 2, "Scenario B old/new Evidence count mismatch", failures)
        require({path.name for path in run_directories(directories["B"])} == {event["run_id"] for event in starts_b}, "Scenario B actual Run directory set mismatch", failures)
        require({item.get("run_id") for item in evidence_b} == {event["run_id"] for event in starts_b}, "Scenario B Runtime Evidence Run link mismatch", failures)
        if decisions_b:
            allow_event = next(event for event in events_b if event["type"] == "RETRY_DECISION")
            fixed_start = next(event for event in starts_b if event["plan_version"] == "1.1")
            require(events_b.index(allow_event) < events_b.index(fixed_start), "Scenario B ALLOW_NEW_RUN must precede run_task", failures)
            require(not (directories["B"] / "runs" / allow_event["run_id"]).exists(), "Scenario B decision must not masquerade as a Run", failures)

        fp_c, events_c = validate_blind_block("C", directories["C"], "VALIDATION_ERROR", failures)
        validation_c = event_payloads(events_c, "VALIDATION_RESULT")
        require(len(validation_c) == 1 and validation_c[0].get("status") == "ERROR", "Scenario C must distinguish Validator ERROR", failures)
        require(fp_c != fp_a, "Validation FAIL and Validator ERROR fingerprints must differ", failures)

        fp_d, events_d = validate_blind_block("D", directories["D"], "EXECUTION_ERROR", failures)
        require(len(event_payloads(events_d, "EXECUTION_ERROR")) == 1, "Scenario D Execution ERROR missing", failures)
        require(not event_payloads(events_d, "VALIDATION_STARTED"), "Scenario D Validator must not execute after Executor ERROR", failures)
        require(fp_d not in {fp_a, fp_c}, "Execution ERROR fingerprint must differ from validation failures", failures)

        events_e = read_events(directories["E"])
        comparisons = event_payloads(events_e, "FAILURE_COMPARISON")
        require(len(comparisons) == 1, "Scenario E comparison missing", failures)
        if comparisons:
            comparison = comparisons[0]
            require(comparison.get("left_fingerprint") == fp_a, "Scenario E left fingerprint mismatch", failures)
            require(comparison.get("right_fingerprint") == fp_d, "Scenario E right fingerprint mismatch", failures)
            require(comparison.get("left_fingerprint") != comparison.get("right_fingerprint"), "Scenario E different failures must differ", failures)
            require(comparison.get("decision") == "DISTINCT_FAILURE" and comparison.get("blind_retry_blocked") is False, "Scenario E must not falsely block distinct failure", failures)
        require(not event_payloads(events_e, "RETRY_DECISION"), "Scenario E must not create a blind retry decision", failures)

        limit_path = (project_root / criteria["retry_limit_fixture_path"]).resolve()
        require(sha256_file(limit_path) == criteria["retry_limit_fixture_sha256"], "Retry Limit fixture hash mismatch", failures)
        limits = json.loads(limit_path.read_text(encoding="utf-8"))
        limit_directories = {key: Path(value).resolve() for key, value in result["retry_limit_directories"].items()}
        require(set(limit_directories) == {"VALIDATOR_ERROR", "EXECUTION_ERROR", "PRODUCT_NEW_RUN"}, "Retry Limit directory set mismatch", failures)
        limit_events: list[dict[str, Any]] = []
        limit_counts: dict[str, dict[str, int]] = {}
        for kind, key in (("VALIDATOR_ERROR", "validator_error_max_attempts"), ("EXECUTION_ERROR", "execution_error_max_attempts"), ("PRODUCT_NEW_RUN", "plan_version_product_run_max_attempts")):
            directory = limit_directories[kind]
            require(directory.is_relative_to(directories["LIMIT"]), f"{kind} Retry Limit path outside allowed root", failures)
            events = read_events(directory)
            starts = [event for event in events if event["type"] == "RUN_STARTED"]
            decisions = [event for event in events if event["type"] == "RETRY_LIMIT_DECISION"]
            payloads = [event["payload"] for event in decisions]
            limit_events.extend(payloads)
            limit = limits[key]
            if kind == "VALIDATOR_ERROR":
                counted = [event for event in events if event["type"] == "VALIDATION_RESULT" and event["payload"].get("status") == "ERROR"]
                expected_evidence = limit
                require(not event_payloads(events, "EXECUTION_ERROR"), "Validator ERROR limit must not contain Execution ERROR", failures)
            elif kind == "EXECUTION_ERROR":
                counted = [event for event in events if event["type"] == "EXECUTION_ERROR"]
                expected_evidence = 0
                require(not event_payloads(events, "VALIDATION_STARTED"), "Execution ERROR limit must not run Validator", failures)
            else:
                counted = starts
                expected_evidence = limit
                require(len([event for event in events if event["type"] == "GATE_DECISION" and event["payload"].get("decision") == "PROCEED"]) == limit, "Product New Run limit PASS count mismatch", failures)
            actual_run_ids = {path.name for path in run_directories(directory)}
            start_run_ids = {event["run_id"] for event in starts}
            evidence = runtime_evidence(directory)
            index_path = directory / "evidence_index.jsonl"
            index_records = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines()] if index_path.is_file() else []
            require(len(counted) == limit, f"{kind} actual Event count must equal fixture limit", failures)
            require(len(starts) == limit, f"{kind} actual RUN_STARTED count must equal fixture limit", failures)
            require(actual_run_ids == start_run_ids and len(actual_run_ids) == limit, f"{kind} actual Run directory count mismatch", failures)
            require(len(evidence) == expected_evidence, f"{kind} Runtime Evidence presence contract mismatch", failures)
            require(len(index_records) == expected_evidence, f"{kind} Evidence index count mismatch", failures)
            require({item.get("run_id") for item in evidence} == ({event["run_id"] for event in starts} if expected_evidence else set()), f"{kind} Runtime Evidence Run links mismatch", failures)
            require(len(decisions) == limit + 1, f"{kind} Retry Limit decision count mismatch", failures)
            for attempt, decision_event in enumerate(decisions, start=1):
                payload = decision_event["payload"]
                expected_observed = attempt - 1
                require(payload.get("observed_event_count") == expected_observed, f"{kind} self-reported Event count mismatch", failures)
                require(payload.get("observed_run_started_count") == expected_observed, f"{kind} self-reported RUN_STARTED count mismatch", failures)
                require(payload.get("observed_run_directory_count") == expected_observed, f"{kind} self-reported Run directory count mismatch", failures)
                require(payload.get("fixture_limit") == limit, f"{kind} fixture limit mismatch", failures)
                require(payload.get("requested_attempt_number") == attempt, f"{kind} requested attempt number mismatch", failures)
                require(payload.get("user_gate_workflow_started") is False, f"{kind} must not start USER-GATE workflow", failures)
                expected_decision = "ALLOW_NEW_RUN" if attempt <= limit else "BLOCK_LIMIT"
                require(payload.get("decision") == expected_decision, f"{kind} limit decision mismatch", failures)
                require(not (directory / "runs" / decision_event["run_id"]).exists(), f"{kind} decision must not create a Run directory", failures)
                require(not any(event["type"] == "RUN_STARTED" and event["run_id"] == decision_event["run_id"] for event in events), f"{kind} decision must not create RUN_STARTED", failures)
                require(not any(item.get("run_id") == decision_event["run_id"] for item in evidence), f"{kind} decision must not create Runtime Evidence", failures)
                if attempt <= limit:
                    require(attempt <= len(starts), f"{kind} ALLOW decision missing corresponding RUN_STARTED", failures)
                    if attempt <= len(starts):
                        require(events.index(decision_event) < events.index(starts[attempt - 1]), f"{kind} ALLOW decision must precede run_task", failures)
            require((directory / "retry_limit_evidence.json").is_file(), f"{kind} Retry Limit Evidence missing", failures)
            limit_counts[kind] = {
                "fixture_limit": limit,
                "actual_event_count": len(counted),
                "actual_run_started_count": len(starts),
                "actual_run_directory_count": len(actual_run_ids),
                "actual_runtime_evidence_count": len(evidence),
                "blocked_excess_run_count": sum(path.name == decisions[-1]["run_id"] for path in run_directories(directory)),
            }

        evidence_links = []
        for key, directory in directories.items():
            for path in sorted(item for item in directory.rglob("*") if item.is_file()):
                evidence_links.append({"scenario": key, "path": str(path.resolve()), "sha256": sha256_file(path)})
        require(bool(evidence_links), "Scenario Evidence links missing", failures)

        output = {
            "mvp_test_id": criteria["mvp_test_id"],
            "mvp_test_name": criteria["mvp_test_name"],
            "test_plan_id": criteria["test_plan_id"],
            "test_plan_version": criteria["test_plan_version"],
            "validation_status": "PASS" if not failures else "FAIL",
            "scenario_root": str(allowed_root),
            "failure_classes": {"A": "VALIDATION_FAIL", "C": "VALIDATION_ERROR", "D": "EXECUTION_ERROR"},
            "fingerprints": {"A": fp_a, "B": fp_b, "C": fp_c, "D": fp_d},
            "retry_decisions": {
                "A": event_payloads(events_a, "RETRY_DECISION"),
                "B": decisions_b,
                "C": event_payloads(events_c, "RETRY_DECISION"),
                "D": event_payloads(events_d, "RETRY_DECISION"),
            },
            "retry_limits": limit_events,
            "retry_limit_counts": limit_counts,
            "scenario_internal_runs": {
                key: [event["run_id"] for event in read_events(directory) if event["type"] == "RUN_STARTED"]
                if (directory / "events.jsonl").is_file() else []
                for key, directory in directories.items()
            },
            "scenario_evidence": evidence_links,
            "failures": failures,
        }
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
        return 0 if not failures else 1
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"validation_status": "ERROR", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
