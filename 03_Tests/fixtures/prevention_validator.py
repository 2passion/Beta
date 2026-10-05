"""Independent validator for MVP Test 5 Prevention enforcement."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def actual_fix_signature(plan: dict[str, Any]) -> str:
    contract = {
        "executor": {"path": plan["executor"]["path"], "sha256": plan["executor"]["sha256"]},
        "validators": [{
            "validator_id": spec["validator_id"], "path": spec["path"],
            "sha256": spec["sha256"], "criteria": spec.get("criteria"),
        } for spec in plan["required_validators"]],
    }
    return stable_hash(contract)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def contains_key(value: Any, forbidden: str) -> bool:
    if isinstance(value, dict):
        return forbidden in value or any(contains_key(item, forbidden) for item in value.values())
    if isinstance(value, list):
        return any(contains_key(item, forbidden) for item in value)
    return False


def validate_enforcement(label: str, directory: Path, expected_outcome: str, expected_calls: int, failures: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events = read_events(directory / "events.jsonl")
    searches = [event for event in events if event["type"] == "PREVENTION_SEARCH"]
    starts = [event for event in events if event["type"] == "RUN_STARTED"]
    require(len(searches) == 1, f"Scenario {label} PREVENTION_SEARCH count mismatch", failures)
    search = searches[0]["payload"] if searches else {}
    require(search.get("outcome") == expected_outcome, f"Scenario {label} search outcome mismatch", failures)
    require(len(starts) == expected_calls, f"Scenario {label} RUN_STARTED count mismatch", failures)
    run_dirs = [path for path in (directory / "runs").iterdir() if path.is_dir()] if (directory / "runs").is_dir() else []
    evidence = list(directory.glob("EVD-*.json"))
    require(len(run_dirs) == expected_calls, f"Scenario {label} Run directory count mismatch", failures)
    require(len(evidence) == expected_calls, f"Scenario {label} Runtime Evidence count mismatch", failures)
    if starts and searches:
        require(events.index(searches[0]) < events.index(starts[0]), f"Scenario {label} search must precede execution", failures)
    return events, search


def main() -> int:
    result_path = Path(sys.argv[1]).resolve()
    criteria = json.loads(sys.argv[2])
    failures: list[str] = []
    try:
        result = read_json(result_path)
        dirs = {key: Path(value).resolve() for key, value in result["scenario_evidence_dirs"].items()}
        scenario_root = Path(result["scenario_root"]).resolve()
        require(result.get("mvp_test_id") == criteria.get("mvp_test_id"), "MVP Test ID mismatch", failures)
        require(result.get("mvp_test_name") == "Prevention", "MVP Test name mismatch", failures)
        require(result.get("test_plan_id") == criteria.get("test_plan_id"), "Test Plan ID mismatch", failures)
        require(result.get("test_plan_version") == criteria.get("test_plan_version"), "Test Plan version mismatch", failures)
        require(set(dirs) == {"A", "B", "C", "D"}, "Scenario set mismatch", failures)
        for label, directory in dirs.items():
            require(directory.is_relative_to(scenario_root), f"Scenario {label} outside scenario root", failures)

        record = read_json(dirs["A"] / "prevention_record.json")
        required_fields = {"prevention_id", "status", "failure_fingerprint", "failure_class", "problem_description", "root_cause", "root_cause_evidence_refs", "fix_description", "fix_signature", "source_fail_run_id", "source_pass_run_id", "source_evidence_ids", "applicable_scope", "created_from", "verification_status"}
        require(required_fields.issubset(record), "Scenario A Prevention record fields incomplete", failures)
        require(record.get("status") == "CANDIDATE", "Scenario A status must remain CANDIDATE", failures)
        require(record.get("root_cause_status") == "CONFIRMED", "Scenario A Root Cause must be confirmed", failures)
        require(record.get("verification_status") == "SOURCE_CHAIN_VERIFIED", "Scenario A source chain not verified", failures)

        outer_path = Path(result["source_outer_result"]["path"])
        require(outer_path.is_file(), "Test 4 source outer result missing", failures)
        require(outer_path.is_file() and sha256_file(outer_path) == result["source_outer_result"]["sha256"], "Test 4 source outer result hash mismatch", failures)
        outer = read_json(outer_path)
        source_dir = Path(outer["scenario_evidence_dirs"]["B"])
        source_events_path = source_dir / "events.jsonl"
        source_events = read_events(source_events_path)
        fail_plan_path, fixed_plan_path = source_dir / "scenario_plan_1_0.json", source_dir / "scenario_plan_1_1.json"
        fail_plan, fixed_plan = read_json(fail_plan_path), read_json(fixed_plan_path)
        source_signature = actual_fix_signature(fixed_plan)
        fail_signature = actual_fix_signature(fail_plan)
        source_fp_event = next((event for event in source_events if event["type"] == "FAILURE_FINGERPRINT"), None)
        source_decision_event = next((event for event in source_events if event["type"] == "RETRY_DECISION"), None)
        require(source_fp_event is not None, "Test 4 source fingerprint missing", failures)
        require(source_decision_event is not None, "Test 4 source fix decision missing", failures)
        if source_fp_event:
            require(record.get("failure_fingerprint") == source_fp_event["payload"].get("fingerprint"), "Scenario A source fingerprint mismatch", failures)
        if source_decision_event:
            decision = source_decision_event["payload"]
            require(decision.get("decision") == "ALLOW_NEW_RUN" and decision.get("change_reason_ref"), "Test 4 source fix decision invalid", failures)
        require(fail_signature != source_signature, "Test 4 source actual fix change missing", failures)
        require(record.get("fix_signature") == source_signature, "Scenario A source actual fix signature mismatch", failures)
        require(result.get("source_actual_fix_signature") == source_signature, "Executor source actual fix signature mismatch", failures)

        source_evidence = {item["evidence_id"]: item for item in (read_json(path) for path in source_dir.glob("EVD-*.json"))}
        require(set(record.get("source_evidence_ids", [])) == set(source_evidence), "Scenario A source Evidence IDs mismatch", failures)
        fail_evd = next((item for item in source_evidence.values() if item.get("validation_result") == "FAIL"), None)
        pass_evd = next((item for item in source_evidence.values() if item.get("validation_result") == "PASS"), None)
        require(fail_evd is not None and fail_evd.get("gate") == "BLOCK" and fail_evd.get("run_id") == record.get("source_fail_run_id"), "Scenario A FAIL Evidence chain missing", failures)
        require(pass_evd is not None and pass_evd.get("gate") == "PROCEED" and pass_evd.get("run_id") == record.get("source_pass_run_id"), "Scenario A PASS Evidence chain missing", failures)
        require((source_dir / "runs" / str(record.get("source_fail_run_id"))).is_dir(), "Scenario A source FAIL Run missing", failures)
        require((source_dir / "runs" / str(record.get("source_pass_run_id"))).is_dir(), "Scenario A source PASS Run missing", failures)
        for link in record.get("source_evidence", []):
            path = Path(link["path"])
            require(path.is_file() and sha256_file(path) == link.get("sha256"), "Scenario A source Evidence hash mismatch", failures)

        refs = record.get("root_cause_evidence_refs", [])
        expected_refs = {
            "SOURCE_EVENTS": source_events_path, "FAIL_PLAN": fail_plan_path, "FIXED_PLAN": fixed_plan_path,
            "FAIL_EVIDENCE": source_dir / f"{fail_evd['evidence_id']}.json" if fail_evd else source_dir / "missing",
            "PASS_EVIDENCE": source_dir / f"{pass_evd['evidence_id']}.json" if pass_evd else source_dir / "missing",
        }
        require({ref.get("kind") for ref in refs} == set(expected_refs), "Scenario A Root Cause Evidence refs incomplete", failures)
        for ref in refs:
            expected_path = expected_refs.get(ref.get("kind"))
            path = Path(ref.get("path", ""))
            require(expected_path is not None and path.resolve() == expected_path.resolve() and path.is_file() and sha256_file(path) == ref.get("sha256"), "Scenario A Root Cause Evidence ref mismatch", failures)
        fail_validator, fixed_validator = fail_plan["required_validators"][0], fixed_plan["required_validators"][0]
        require(fail_validator.get("criteria") != fixed_validator.get("criteria") and fail_validator.get("sha256") != fixed_validator.get("sha256"), "Scenario A Root Cause fix delta missing", failures)

        events_b, search_b = validate_enforcement("B", dirs["B"], "MATCH", 1, failures)
        require(search_b.get("requested_fingerprint") == record.get("failure_fingerprint"), "Scenario B requested fingerprint mismatch", failures)
        require(search_b.get("eligible") is True and search_b.get("fix_contract_valid") is True, "Scenario B MATCH must be ELIGIBLE with valid fix", failures)
        require(search_b.get("selected_prevention_id") == record.get("prevention_id") and search_b.get("fix_preapplied") is True, "Scenario B selected Prevention mismatch", failures)
        target_plan_path = dirs["B"] / "target_plan.json"
        target_plan = read_json(target_plan_path)
        target_signature = actual_fix_signature(target_plan)
        require(target_signature == source_signature == record.get("fix_signature"), "Scenario B actual Source/Record/Target fix signature mismatch", failures)
        require(result.get("target_actual_fix_signature") == target_signature, "Executor target actual fix signature mismatch", failures)
        application = target_plan.get("prevention_application", {})
        require(application.get("fix_signature") == record.get("fix_signature"), "Scenario B applied fix signature mismatch", failures)
        starts_b = [event for event in events_b if event["type"] == "RUN_STARTED"]
        target_plan_sha = sha256_file(target_plan_path)
        require(bool(starts_b) and starts_b[0]["payload"].get("task_plan_sha256") == target_plan_sha, "Scenario B Target Plan SHA / RUN_STARTED mismatch", failures)
        apply_evidence = read_json(dirs["B"] / "prevention_apply_evidence.json")
        require(apply_evidence.get("target_plan_sha256") == target_plan_sha, "Scenario B apply Evidence Target Plan SHA mismatch", failures)
        require(apply_evidence.get("enforcement") == {"run_task_call_count": 1, "run_started_delta": 1, "run_directory_delta": 1, "runtime_evidence_delta": 1}, "Scenario B execution enforcement mismatch", failures)
        require(not any(event["type"] == "EXECUTION_ERROR" or (event["type"] == "VALIDATION_RESULT" and event["payload"].get("status") != "PASS") for event in events_b), "Scenario B repeated the source failure", failures)
        require(any(event["type"] == "GATE_DECISION" and event["payload"].get("decision") == "PROCEED" for event in events_b), "Scenario B Gate PROCEED missing", failures)

        events_c, search_c = validate_enforcement("C", dirs["C"], "NO_MATCH", 0, failures)
        require(search_c.get("selected_prevention_id") is None and search_c.get("fix_preapplied") is False, "Scenario C must not auto-apply", failures)
        search_evidence_c = read_json(dirs["C"] / "search_evidence.json")
        require(search_evidence_c.get("enforcement") == {"run_task_call_count": 0, "run_started_delta": 0, "run_directory_delta": 0, "runtime_evidence_delta": 0}, "Scenario C NO_MATCH executed", failures)

        unverified = read_json(dirs["D"] / "unverified_record.json")
        events_d, search_d = validate_enforcement("D", dirs["D"], "NOT_ELIGIBLE", 0, failures)
        require(search_d.get("eligible") is False and search_d.get("selected_prevention_id") is None and search_d.get("fix_preapplied") is False, "Scenario D must not reuse fix", failures)
        search_evidence_d = read_json(dirs["D"] / "search_evidence.json")
        require(search_evidence_d.get("enforcement") == {"run_task_call_count": 0, "run_started_delta": 0, "run_directory_delta": 0, "runtime_evidence_delta": 0}, "Scenario D NOT_ELIGIBLE executed", failures)
        require(not unverified.get("root_cause_evidence_refs"), "Scenario D fixture must lack Root Cause Evidence", failures)

        require(not contains_key(record, "active_rule"), "Prevention must not be promoted to active_rule", failures)
        require(not any("active_rule" in path.name.casefold() for path in scenario_root.rglob("*")), "active_rule artifact must not be created", failures)
        for link in result.get("scenario_evidence", []):
            path = Path(link["path"])
            require(path.is_file() and sha256_file(path) == link.get("sha256"), "Scenario Evidence link/hash mismatch", failures)
    except (OSError, ValueError, KeyError, StopIteration, TypeError, json.JSONDecodeError) as exc:
        failures.append(f"validator error: {exc}")

    output = {
        "mvp_test_id": "MVP-TEST-5", "mvp_test_name": "Prevention", "test_plan_id": "MVP-TEST-5-PREVENTION",
        "test_plan_version": "1.1", "validation_status": "PASS" if not failures else "FAIL", "failures": failures,
        "source_actual_fix_signature": locals().get("source_signature"), "target_actual_fix_signature": locals().get("target_signature"),
        "target_plan_sha256": locals().get("target_plan_sha"),
        "scenario_evidence": result.get("scenario_evidence", []) if "result" in locals() else [],
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
