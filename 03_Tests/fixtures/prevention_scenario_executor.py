"""Execute MVP Test 5 Prevention scenarios with evidence-backed enforcement."""

from __future__ import annotations

import hashlib
import json
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

SOURCE_OUTER_RESULT = PROJECT_ROOT / "04_Evidence/mvp_test_4/official/runs/RUN-5ae1b61a-6e14-442e-a471-9188e78cb01f/executor_result.json"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def actual_fix_contract(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "executor": {"path": plan["executor"]["path"], "sha256": plan["executor"]["sha256"]},
        "validators": [{
            "validator_id": spec["validator_id"], "path": spec["path"],
            "sha256": spec["sha256"], "criteria": spec.get("criteria"),
        } for spec in plan["required_validators"]],
    }


def actual_fix_signature(plan: dict[str, Any]) -> str:
    return stable_hash(actual_fix_contract(plan))


def source_chain() -> dict[str, Any]:
    outer = read_json(SOURCE_OUTER_RESULT)
    source_dir = Path(outer["scenario_evidence_dirs"]["B"])
    events_path = source_dir / "events.jsonl"
    events = read_events(events_path)
    fingerprint = next(event["payload"] for event in events if event["type"] == "FAILURE_FINGERPRINT")
    decision = next(event["payload"] for event in events if event["type"] == "RETRY_DECISION")
    fail_plan_path = source_dir / "scenario_plan_1_0.json"
    fixed_plan_path = source_dir / "scenario_plan_1_1.json"
    fail_plan, fixed_plan = read_json(fail_plan_path), read_json(fixed_plan_path)
    evidences = [read_json(path) for path in sorted(source_dir.glob("EVD-*.json"))]
    fail_evidence = next(item for item in evidences if item["validation_result"] == "FAIL")
    pass_evidence = next(item for item in evidences if item["validation_result"] == "PASS")
    return {
        "source_dir": source_dir, "events_path": events_path, "events": events,
        "fingerprint": fingerprint, "decision": decision,
        "fail_evidence": fail_evidence, "pass_evidence": pass_evidence,
        "fail_plan_path": fail_plan_path, "fixed_plan_path": fixed_plan_path,
        "fail_plan": fail_plan, "fixed_plan": fixed_plan,
        "source_actual_fix_signature": actual_fix_signature(fixed_plan),
    }


def evidence_ref(kind: str, path: Path) -> dict[str, Any]:
    return {"kind": kind, "path": str(path), "sha256": sha256_file(path)}


def make_record(chain: dict[str, Any]) -> dict[str, Any]:
    failure, fail_evidence, pass_evidence = chain["fingerprint"], chain["fail_evidence"], chain["pass_evidence"]
    source_dir = chain["source_dir"]
    return {
        "prevention_id": new_id("PREV"), "status": "CANDIDATE",
        "failure_fingerprint": failure["fingerprint"], "failure_class": failure["failure_class"],
        "problem_description": failure["normalized_reason"],
        "root_cause": "validator criteria mode=fail caused the synthetic criteria mismatch",
        "root_cause_status": "CONFIRMED",
        "root_cause_evidence_refs": [
            evidence_ref("SOURCE_EVENTS", chain["events_path"]), evidence_ref("FAIL_PLAN", chain["fail_plan_path"]),
            evidence_ref("FIXED_PLAN", chain["fixed_plan_path"]),
            evidence_ref("FAIL_EVIDENCE", source_dir / f"{fail_evidence['evidence_id']}.json"),
            evidence_ref("PASS_EVIDENCE", source_dir / f"{pass_evidence['evidence_id']}.json"),
        ],
        "fix_description": "use the corrected validator and expected-value criteria before execution",
        "fix_signature": chain["source_actual_fix_signature"],
        "source_fail_run_id": fail_evidence["run_id"], "source_pass_run_id": pass_evidence["run_id"],
        "source_evidence_ids": [fail_evidence["evidence_id"], pass_evidence["evidence_id"]],
        "source_evidence": [
            evidence_ref(fail_evidence["evidence_id"], source_dir / f"{fail_evidence['evidence_id']}.json"),
            evidence_ref(pass_evidence["evidence_id"], source_dir / f"{pass_evidence['evidence_id']}.json"),
        ],
        "applicable_scope": {"failure_class": failure["failure_class"], "validator_id": failure["fingerprint_inputs"]["identity"]},
        "created_from": "MVP-TEST-4 Scenario B verified FAIL-to-PASS chain",
        "verification_status": "SOURCE_CHAIN_VERIFIED", "created_at": utc_now(),
    }


def validate_candidate(record: dict[str, Any], chain: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    required = {"prevention_id", "status", "failure_fingerprint", "failure_class", "root_cause", "root_cause_evidence_refs", "fix_signature", "source_fail_run_id", "source_pass_run_id", "source_evidence_ids", "source_evidence", "verification_status"}
    if not required.issubset(record): reasons.append("candidate fields incomplete")
    if record.get("status") != "CANDIDATE" or record.get("verification_status") != "SOURCE_CHAIN_VERIFIED": reasons.append("candidate status contract invalid")
    if record.get("root_cause_status") != "CONFIRMED": reasons.append("root cause is not confirmed")
    refs = record.get("root_cause_evidence_refs", [])
    if {ref.get("kind") for ref in refs if isinstance(ref, dict)} != {"SOURCE_EVENTS", "FAIL_PLAN", "FIXED_PLAN", "FAIL_EVIDENCE", "PASS_EVIDENCE"}: reasons.append("root cause evidence references incomplete")
    for ref in refs:
        try:
            path = Path(ref["path"])
            if not path.is_file() or sha256_file(path) != ref.get("sha256"): reasons.append("root cause evidence reference invalid")
        except (KeyError, TypeError, OSError): reasons.append("root cause evidence reference invalid")
    fail_evidence, pass_evidence = chain["fail_evidence"], chain["pass_evidence"]
    if record.get("source_fail_run_id") != fail_evidence.get("run_id") or not (chain["source_dir"] / "runs" / str(record.get("source_fail_run_id"))).is_dir(): reasons.append("source FAIL Run invalid")
    if record.get("source_pass_run_id") != pass_evidence.get("run_id") or not (chain["source_dir"] / "runs" / str(record.get("source_pass_run_id"))).is_dir(): reasons.append("source PASS Run invalid")
    if record.get("source_evidence_ids") != [fail_evidence["evidence_id"], pass_evidence["evidence_id"]]: reasons.append("source Evidence IDs invalid")
    for link in record.get("source_evidence", []):
        try:
            path = Path(link["path"])
            if not path.is_file() or sha256_file(path) != link.get("sha256"): reasons.append("source Evidence hash invalid")
        except (KeyError, TypeError, OSError): reasons.append("source Evidence hash invalid")
    if not (fail_evidence.get("validation_result") == "FAIL" and fail_evidence.get("gate") == "BLOCK" and fail_evidence.get("run_id") == record.get("source_fail_run_id")): reasons.append("source FAIL Evidence contract invalid")
    if not (pass_evidence.get("validation_result") == "PASS" and pass_evidence.get("gate") == "PROCEED" and pass_evidence.get("run_id") == record.get("source_pass_run_id")): reasons.append("source PASS Evidence contract invalid")
    if record.get("failure_fingerprint") != chain["fingerprint"].get("fingerprint"): reasons.append("source fingerprint invalid")
    if record.get("fix_signature") != chain["source_actual_fix_signature"]: reasons.append("source actual fix signature invalid")
    fail_validator, fixed_validator = chain["fail_plan"]["required_validators"][0], chain["fixed_plan"]["required_validators"][0]
    if fail_validator.get("criteria") == fixed_validator.get("criteria") or fail_validator.get("sha256") == fixed_validator.get("sha256"): reasons.append("source actual fix change missing")
    if not chain["decision"].get("change_reason_ref") or chain["decision"].get("decision") != "ALLOW_NEW_RUN": reasons.append("source fix decision invalid")
    return not reasons, sorted(set(reasons))


def target_plan(record: dict[str, Any], chain: dict[str, Any]) -> dict[str, Any]:
    fixed = chain["fixed_plan"]
    return {
        "task_id": "TASK-MVP5-SIMILAR-B", "plan_version": "1.1", "order_id": "Order-033",
        "change_reason_ref": "Order-033-Prevention-Preapply", "write_owner": "Codex",
        "write_scope": ["04_Evidence/mvp_test_5/scenarios"], "shared_resources": [], "depends_on": [],
        "steps": [{"step_id": "PREVENTION-B-001", "action": "execute with verified fix preapplied"}],
        "executor": dict(fixed["executor"]), "required_validators": [dict(spec) for spec in fixed["required_validators"]],
        "completion_criteria": ["verified Prevention is applied before execution and target passes"],
        "permissions": {"subprocess": "approved fixture paths only", "network": False},
        "prevention_application": {"prevention_id": record["prevention_id"], "failure_fingerprint": record["failure_fingerprint"], "fix_signature": record["fix_signature"]},
    }


def prevention_search(directory: Path, requested_fingerprint: str, record: dict[str, Any], chain: dict[str, Any], plan: dict[str, Any], task_id: str) -> dict[str, Any]:
    exact = requested_fingerprint == record.get("failure_fingerprint")
    is_eligible, eligibility_reasons = validate_candidate(record, chain)
    source_signature, target_signature = chain["source_actual_fix_signature"], actual_fix_signature(plan)
    fix_contract_valid = source_signature == record.get("fix_signature") == target_signature
    outcome = "MATCH" if exact and is_eligible and fix_contract_valid else "NOT_ELIGIBLE" if exact else "NO_MATCH"
    payload = {
        "requested_fingerprint": requested_fingerprint, "search_scope": "verified Prevention candidates", "outcome": outcome,
        "selected_prevention_id": record.get("prevention_id") if outcome == "MATCH" else None,
        "eligibility_checked": True, "eligible": is_eligible, "eligibility_reasons": eligibility_reasons,
        "exact_fingerprint_match": exact, "source_actual_fix_signature": source_signature,
        "target_actual_fix_signature": target_signature, "fix_contract_valid": fix_contract_valid, "fix_preapplied": outcome == "MATCH",
    }
    EventStore(directory / "events.jsonl").append("PREVENTION_SEARCH", task_id=task_id, run_id=new_id("SEARCH"), plan_version="1.1", actor_role="Prevention", payload=payload)
    return payload


def execute_target(directory: Path, record: dict[str, Any], requested_fingerprint: str, chain: dict[str, Any] | None = None) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    chain = chain or source_chain()
    plan, plan_path = target_plan(record, chain), directory / "target_plan.json"
    write_json(plan_path, plan)
    search_result = prevention_search(directory, requested_fingerprint, record, chain, plan, "TASK-MVP5-SIMILAR-B")
    before_events = read_events(directory / "events.jsonl")
    before_starts = sum(event["type"] == "RUN_STARTED" for event in before_events)
    before_runs = len([path for path in (directory / "runs").iterdir() if path.is_dir()]) if (directory / "runs").is_dir() else 0
    before_evidence = len(list(directory.glob("EVD-*.json")))
    result, calls = None, 0
    if search_result["outcome"] == "MATCH" and search_result["eligible"] and search_result["fix_contract_valid"]:
        calls, result = 1, run_task(plan_path, PROJECT_ROOT, directory)
    after_events = read_events(directory / "events.jsonl")
    enforcement = {
        "run_task_call_count": calls,
        "run_started_delta": sum(event["type"] == "RUN_STARTED" for event in after_events) - before_starts,
        "run_directory_delta": (len([path for path in (directory / "runs").iterdir() if path.is_dir()]) if (directory / "runs").is_dir() else 0) - before_runs,
        "runtime_evidence_delta": len(list(directory.glob("EVD-*.json"))) - before_evidence,
    }
    return {"search": search_result, "plan": plan, "plan_path": str(plan_path), "result": result, "enforcement": enforcement}


def main() -> int:
    result_path = Path(sys.argv[1]).resolve()
    scenario_root = result_path.parents[2].parent / "scenarios" / new_id("SCN")
    scenario_root.mkdir(parents=True)
    chain, record = source_chain(), None
    record = make_record(chain)
    a_dir = scenario_root / "a_create_candidate"
    write_json(a_dir / "prevention_record.json", record)
    write_json(a_dir / "source_chain_evidence.json", {
        "failure_fingerprint": record["failure_fingerprint"], "source_fail_run_id": record["source_fail_run_id"],
        "source_pass_run_id": record["source_pass_run_id"], "source_evidence": record["source_evidence"],
        "root_cause_evidence_refs": record["root_cause_evidence_refs"], "source_actual_fix_signature": chain["source_actual_fix_signature"],
    })
    b_dir = scenario_root / "b_exact_match_preapply"
    outcome_b = execute_target(b_dir, record, record["failure_fingerprint"], chain)
    result_b = outcome_b["result"]
    write_json(b_dir / "prevention_apply_evidence.json", {
        "search": outcome_b["search"], "enforcement": outcome_b["enforcement"], "target_plan_path": outcome_b["plan_path"],
        "target_plan_sha256": sha256_file(Path(outcome_b["plan_path"])), "prevention_id": record["prevention_id"],
        "fix_signature": record["fix_signature"], "target_run_id": result_b["run_id"] if result_b else None,
        "validation": result_b["validation"] if result_b else "NOT_RUN", "gate": result_b["gate"] if result_b else "BLOCK",
    })
    c_dir = scenario_root / "c_different_fingerprint"
    outcome_c = execute_target(c_dir, record, stable_hash({"different": record["failure_fingerprint"]}), chain)
    write_json(c_dir / "search_evidence.json", {"search": outcome_c["search"], "enforcement": outcome_c["enforcement"]})
    d_dir = scenario_root / "d_unverified_fix"
    unverified = dict(record)
    unverified.update({"prevention_id": new_id("PREV"), "root_cause_status": "HYPOTHESIS", "verification_status": "NOT_VERIFIED", "source_evidence_ids": [record["source_evidence_ids"][0]], "root_cause_evidence_refs": []})
    write_json(d_dir / "unverified_record.json", unverified)
    outcome_d = execute_target(d_dir, unverified, record["failure_fingerprint"], chain)
    write_json(d_dir / "search_evidence.json", {"search": outcome_d["search"], "enforcement": outcome_d["enforcement"]})
    evidence_links = [{"path": str(path), "sha256": sha256_file(path)} for path in sorted(scenario_root.rglob("*")) if path.is_file()]
    output = {
        "mvp_test_id": "MVP-TEST-5", "mvp_test_name": "Prevention", "test_plan_id": "MVP-TEST-5-PREVENTION", "test_plan_version": "1.1",
        "scenario_root": str(scenario_root), "scenario_evidence_dirs": {"A": str(a_dir), "B": str(b_dir), "C": str(c_dir), "D": str(d_dir)},
        "prevention_record": record, "search_results": {"B": outcome_b["search"], "C": outcome_c["search"], "D": outcome_d["search"]},
        "enforcement": {"B": outcome_b["enforcement"], "C": outcome_c["enforcement"], "D": outcome_d["enforcement"]},
        "target_result": result_b, "scenario_evidence": evidence_links,
        "source_outer_result": {"path": str(SOURCE_OUTER_RESULT), "sha256": sha256_file(SOURCE_OUTER_RESULT)},
        "source_actual_fix_signature": chain["source_actual_fix_signature"], "target_actual_fix_signature": actual_fix_signature(outcome_b["plan"]),
    }
    write_json(result_path, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
