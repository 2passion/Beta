"""Independent validator for MVP Test 6 User Gate enforcement."""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
FIXTURES = PROJECT_ROOT / "03_Tests/fixtures"
if str(FIXTURES) not in sys.path:
    sys.path.insert(0, str(FIXTURES))

from prevention_scenario_executor import actual_fix_signature, source_chain, validate_candidate


AUTO_KEYS = (
    "existing_contract", "io_clear", "fixture_runtime_pass", "bounded_change_scope",
    "postflight_possible", "idempotent", "reason_and_stop_defined", "within_approved_scope",
)
BASE_AUTO_KEYS = AUTO_KEYS[:-1]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_events(directory: Path) -> list[dict[str, Any]]:
    path = directory / "events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def snapshot(directory: Path) -> dict[str, str]:
    if not directory.is_dir():
        return {}
    return {
        path.relative_to(directory).as_posix(): sha256_file(path)
        for path in sorted(directory.rglob("*")) if path.is_file()
    }


def changed_count(before: dict[str, str], after: dict[str, str]) -> int:
    return sum(before.get(key) != after.get(key) for key in set(before) | set(after))


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def scope_match(context: dict[str, Any]) -> bool:
    approval, request = context.get("approval"), context.get("request")
    if not isinstance(approval, dict) or not isinstance(request, dict):
        return False
    approved, requested = approval.get("approved_scope"), request.get("requested_scope")
    return (
        approval.get("approval_status") == "APPROVED"
        and bool(approval.get("approval_id"))
        and isinstance(approved, list) and bool(approved)
        and isinstance(requested, list) and bool(requested)
        and all(isinstance(item, str) and item for item in approved + requested)
        and set(requested).issubset(set(approved))
    )


def recompute_gate(context: dict[str, Any]) -> dict[str, Any]:
    conditions = {key: context.get(key) is True for key in BASE_AUTO_KEYS}
    conditions["within_approved_scope"] = scope_match(context)
    holds = (
        ("routing_mismatch", "ROUTING_MISMATCH"),
        ("ssot_conflict", "SSOT_CONFLICT"),
        ("required_evidence_missing", "REQUIRED_EVIDENCE_MISSING"),
        ("validator_error", "VALIDATOR_ERROR"),
        ("new_unverified_failure", "NEW_ROOT_CAUSE_UNCONFIRMED"),
    )
    for key, reason in holds:
        if context.get(key):
            return {"decision": "HOLD", "reason_code": reason, "side_effect_allowed": False, "conditions": conditions}
    if all(conditions.values()):
        return {"decision": "AUTO", "reason_code": "ALL_AUTO_CONDITIONS_MET", "side_effect_allowed": True, "conditions": conditions}
    if all(conditions[key] for key in BASE_AUTO_KEYS) and not conditions["within_approved_scope"]:
        return {"decision": "APPROVAL_REQUIRED", "reason_code": "APPROVAL_SCOPE_REQUIRED", "side_effect_allowed": False, "conditions": conditions}
    return {"decision": "HOLD", "reason_code": "AUTO_CONDITIONS_INCOMPLETE", "side_effect_allowed": False, "conditions": conditions}


def runtime_counts(directory: Path) -> dict[str, int]:
    events = read_events(directory)
    return {
        "run_started": sum(event.get("type") == "RUN_STARTED" for event in events),
        "run_directories": len([path for path in (directory / "runs").iterdir() if path.is_dir()]) if (directory / "runs").is_dir() else 0,
        "runtime_evidence": len(list(directory.glob("EVD-*.json"))),
    }


def validate_routing(label: str, route: dict[str, Any], directory: Path, failures: list[str]) -> None:
    matched = route.get("expected_to") == route.get("actual_executor") and route.get("action") == "WRITE"
    expected_result = "MATCH" if matched else "HOLD"
    require(route.get("routing_result") == expected_result, f"Scenario {label} routing independent recomputation mismatch", failures)
    require(route.get("mismatch_reason") == (None if matched else "ROUTING_MISMATCH"), f"Scenario {label} routing reason mismatch", failures)
    require(route.get("identity_source") == "ORDER_EXECUTION_CONTEXT", f"Scenario {label} identity source mismatch", failures)
    before, after = route.get("before_snapshot"), route.get("after_snapshot")
    require(isinstance(before, dict) and isinstance(after, dict), f"Scenario {label} routing snapshots missing", failures)
    if isinstance(before, dict) and isinstance(after, dict):
        require(route.get("beta_write_delta") == changed_count(before, after), f"Scenario {label} beta write delta mismatch", failures)
        current = snapshot(directory)
        require(all(current.get(path) == digest for path, digest in after.items()), f"Scenario {label} routing after snapshot mismatch", failures)
    if matched:
        require(route.get("writer_call_count") == 1, f"Scenario {label} writer call count mismatch", failures)
        require(route.get("run_task_call_count") == 1, f"Scenario {label} run_task call count mismatch", failures)
        require(route.get("downstream_call_count") == 1, f"Scenario {label} downstream call count mismatch", failures)
        require(route.get("beta_write_delta", 0) > 0, f"Scenario {label} expected actual writes", failures)
        require(runtime_counts(directory) == {"run_started": 1, "run_directories": 1, "runtime_evidence": 1}, f"Scenario {label} runtime linkage mismatch", failures)
    else:
        require(all(route.get(key) == 0 for key in ("writer_call_count", "run_task_call_count", "downstream_call_count", "beta_write_delta")), f"Scenario {label} routing mismatch side effects must be zero", failures)
        require(not (directory / "FORBIDDEN-WRITE.json").exists(), f"Scenario {label} forbidden downstream write exists", failures)
        require(runtime_counts(directory) == {"run_started": 0, "run_directories": 0, "runtime_evidence": 0}, f"Scenario {label} mismatch runtime side effects", failures)


def validate_execution_gate(
    name: str,
    decision: dict[str, Any],
    gate: dict[str, Any],
    directory: Path,
    failures: list[str],
) -> None:
    current_files = snapshot(directory)
    current_runtime = runtime_counts(directory)
    require(gate.get("decision") == decision.get("decision"), f"Decision {name} gate label mismatch", failures)
    require(Path(gate.get("execution_dir", "")).resolve() == directory, f"Decision {name} execution path mismatch", failures)
    require(gate.get("after_snapshot") == current_files, f"Decision {name} filesystem delta mismatch", failures)
    expected_write_delta = changed_count(gate.get("before_snapshot", {}), current_files)
    require(gate.get("managed_write_delta") == expected_write_delta, f"Decision {name} managed write delta mismatch", failures)
    require(gate.get("run_started_delta") == current_runtime["run_started"], f"Decision {name} RUN_STARTED delta mismatch", failures)
    require(gate.get("run_directory_delta") == current_runtime["run_directories"], f"Decision {name} Run directory delta mismatch", failures)
    require(gate.get("runtime_evidence_delta") == current_runtime["runtime_evidence"], f"Decision {name} Runtime Evidence delta mismatch", failures)
    if decision.get("decision") != "AUTO":
        zero_fields = (
            "routing_entry_call_count", "writer_call_count", "run_task_call_count",
            "downstream_call_count", "run_started_delta", "run_directory_delta",
            "runtime_evidence_delta", "managed_write_delta",
        )
        no_actual_side_effect = not current_files and current_runtime == {
            "run_started": 0, "run_directories": 0, "runtime_evidence": 0,
        }
        require(all(gate.get(key) == 0 for key in zero_fields) and no_actual_side_effect, f"Decision {name} non-AUTO execution side effects", failures)
    else:
        require(gate.get("routing_entry_call_count") == 1, f"Decision {name} AUTO must enter routing once", failures)


def validate_recovery(name: str, item: dict[str, Any], failures: list[str]) -> None:
    chain = source_chain()
    record, plan = item.get("prevention_record"), item.get("target_plan")
    if not isinstance(record, dict) or not isinstance(plan, dict):
        failures.append(f"Recovery {name} Test 5 inputs missing")
        return
    eligible, reasons = validate_candidate(record, chain)
    fingerprint_applicable = item.get("requested_fingerprint") == record.get("failure_fingerprint")
    try:
        scope_ok = plan["required_validators"][0]["validator_id"] == record["applicable_scope"]["validator_id"]
        fix_ok = chain["source_actual_fix_signature"] == record.get("fix_signature") == actual_fix_signature(plan)
        postflight = bool(plan.get("required_validators"))
    except (KeyError, TypeError, IndexError):
        scope_ok = fix_ok = postflight = False
    allowed = fingerprint_applicable and eligible and scope_ok and fix_ok and postflight
    expected = {
        "fingerprint_applicable": fingerprint_applicable,
        "prevention_verified": eligible,
        "eligibility_reasons": reasons,
        "scope_match": scope_ok,
        "fix_contract_valid": fix_ok,
        "postflight_possible": postflight,
        "decision": "AUTO_RECOVERY_ALLOWED" if allowed else "HOLD",
        "reason_code": None if allowed else "NEW_ROOT_CAUSE_UNCONFIRMED",
    }
    require(all(item.get(key) == value for key, value in expected.items()), f"Recovery {name} independent eligibility mismatch", failures)
    require(item.get("automatic_fix_count") == 0 and item.get("unauthorized_new_run_count") == 0, f"Recovery {name} executed unauthorized side effect", failures)
    require(item.get("reused_asset") == "03_Tests/fixtures/prevention_scenario_executor.py", f"Recovery {name} did not reuse Test 5 asset", failures)


result_path = Path(sys.argv[1]).resolve()
criteria = json.loads(sys.argv[2])
failures: list[str] = []
try:
    result = read_json(result_path)
    dirs = {key: Path(value).resolve() for key, value in result["scenario_dirs"].items()}
    root = Path(result["scenario_root"]).resolve()
    require(result.get("mvp_test_id") == criteria.get("mvp_test_id"), "MVP Test ID mismatch", failures)
    require(result.get("mvp_test_name") == criteria.get("mvp_test_name"), "MVP Test name mismatch", failures)
    require(result.get("test_plan_id") == criteria.get("test_plan_id"), "Test Plan ID mismatch", failures)
    require(result.get("test_plan_version") == criteria.get("test_plan_version"), "Test Plan version mismatch", failures)
    require(set(dirs) == set("ABCDEF"), "Scenario set mismatch", failures)
    for label, directory in dirs.items():
        require(directory.is_relative_to(root), f"Scenario {label} path outside root", failures)
    delta_dirs = {key: Path(value).resolve() for key, value in result["delta_dirs"].items()}
    require(set(delta_dirs) == {"D1", "D2_before", "D2_after", "D3", "D4", "D5", "D6"}, "Delta scenario set mismatch", failures)
    for label, directory in delta_dirs.items():
        require(directory.is_relative_to(root), f"Delta {label} path outside root", failures)

    for key in ("A", "B_before", "B_after", "C", "D", "G", "F"):
        expected = recompute_gate(result["contexts"][key])
        actual = result["decisions"][key]
        require(all(actual.get(field) == expected[field] for field in expected), f"Decision {key} independent recomputation mismatch", failures)

    gate_map = {
        "D1": "A", "D2_before": "B_before", "D2_after": "B_after",
        "D3": "D", "D4": "G", "D5": "C", "D6": "F",
    }
    for delta, decision_key in gate_map.items():
        validate_execution_gate(delta, result["decisions"][decision_key], result["execution_gates"][delta], delta_dirs[delta], failures)

    require(result["decisions"]["A"].get("decision") == "AUTO", "Scenario A must AUTO", failures)
    require(result["results"]["A"].get("validation") == "PASS" and result["results"]["A"].get("gate") == "PROCEED", "Scenario A Validation/Gate mismatch", failures)
    validate_routing("A", read_json(dirs["A"] / "routing_evidence.json"), delta_dirs["D1"], failures)

    require(result["decisions"]["B_before"].get("decision") == "APPROVAL_REQUIRED", "Scenario B must require approval", failures)
    require(result.get("b_runtime_before_approval") == {"run_started": 0, "run_directories": 0, "runtime_evidence": 0}, "Scenario B pre-approval side effects must be zero", failures)
    events_b = read_events(dirs["B"])
    approval_positions = [index for index, event in enumerate(events_b) if event.get("type") == "USER_APPROVAL_RECORDED"]
    require(bool(approval_positions), "Scenario B approval event missing", failures)
    if approval_positions:
        require(not any(event.get("type") == "RUN_STARTED" for event in events_b[:approval_positions[0]]), "Scenario B pre-approval side effects must be zero", failures)
    require(result["decisions"]["B_after"].get("decision") == "AUTO", "Scenario B matching approval must AUTO", failures)
    require(result.get("b_duplicate_approval_questions") == 0, "Scenario B duplicate approval question", failures)
    require(result["results"]["B"].get("validation") == "PASS" and result["results"]["B"].get("gate") == "PROCEED", "Scenario B Validation/Gate mismatch", failures)
    validate_routing("B", read_json(dirs["B"] / "routing_evidence.json"), delta_dirs["D2_after"], failures)

    hold_c = read_json(dirs["C"] / "hold_evidence.json")
    require(result["decisions"]["C"].get("decision") == "HOLD" and result["decisions"]["C"].get("reason_code") == "SSOT_CONFLICT", "Scenario C HOLD reason mismatch", failures)
    require(runtime_counts(delta_dirs["D5"]) == {"run_started": 0, "run_directories": 0, "runtime_evidence": 0}, "Scenario C runtime side effects must be zero", failures)
    require(hold_c.get("arbitrary_fix_count") == 0, "Scenario C arbitrary fix forbidden", failures)

    require(result["decisions"]["D"].get("decision") == "APPROVAL_REQUIRED", "Scenario D expansion must require approval", failures)
    require(runtime_counts(delta_dirs["D3"]) == {"run_started": 0, "run_directories": 0, "runtime_evidence": 0}, "Scenario D pre-approval side effects must be zero", failures)

    require(result["decisions"]["G"].get("decision") == "HOLD", "Scenario G C3 false must HOLD", failures)
    require(runtime_counts(delta_dirs["D4"]) == {"run_started": 0, "run_directories": 0, "runtime_evidence": 0}, "Scenario G C3 false runtime side effects must be zero", failures)

    idem = read_json(dirs["E"] / "idempotency_evidence.json")
    managed = Path(idem["managed_path"]).resolve()
    current_managed = snapshot(managed)
    require(idem.get("first_status") == "WRITE" and idem.get("reentry_status") == "NO_CHANGE", "Scenario E re-entry status mismatch", failures)
    require(idem.get("after_first") == idem.get("after_reentry") == current_managed, "Scenario E filesystem changed on re-entry", failures)
    require(idem.get("reentry_write_delta") == 0 and idem.get("reentry_evidence_delta") == 0, "Scenario E duplicate write/evidence detected", failures)
    require(set(current_managed) == {"state.json", "EVD-idempotent.json"}, "Scenario E managed file set mismatch", failures)

    require(result["decisions"]["F"].get("decision") == "AUTO", "Scenario F User Gate must AUTO before routing mismatch", failures)
    validate_routing("F", read_json(dirs["F"] / "routing_evidence.json"), delta_dirs["D6"], failures)
    validate_recovery("verified", result["recovery"]["verified"], failures)
    validate_recovery("new_failure", result["recovery"]["new_failure"], failures)

    for link in result.get("scenario_evidence", []):
        path = Path(link["path"])
        require(path.is_file() and sha256_file(path) == link.get("sha256"), "Scenario Evidence link/hash mismatch", failures)
except (OSError, ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError) as exc:
    failures.append(f"user gate validator error: {exc}")

print(json.dumps({
    "mvp_test_id": "MVP-TEST-6", "mvp_test_name": "User Gate", "test_plan_version": "1.2",
    "validation_status": "PASS" if not failures else "FAIL", "failures": failures,
    "scenario_evidence": result.get("scenario_evidence", []) if "result" in locals() else [],
}, ensure_ascii=False, sort_keys=True))
raise SystemExit(0 if not failures else 1)
