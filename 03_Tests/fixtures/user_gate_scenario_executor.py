"""Execute MVP Test 6 User Gate scenarios with enforcement at real boundaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
CORE_ROOT = PROJECT_ROOT / "02_Core"
FIXTURES = PROJECT_ROOT / "03_Tests/fixtures"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
if str(FIXTURES) not in sys.path:
    sys.path.insert(0, str(FIXTURES))

from beta_core.cli import run_task
from beta_core.event_store import EventStore
from beta_core.model import new_id, sha256_file
from prevention_scenario_executor import (
    actual_fix_signature,
    make_record,
    source_chain,
    target_plan,
    validate_candidate,
)
from routing_scenario_executor import evaluate_routing


AUTO_KEYS = (
    "existing_contract",
    "io_clear",
    "fixture_runtime_pass",
    "bounded_change_scope",
    "postflight_possible",
    "idempotent",
    "reason_and_stop_defined",
    "within_approved_scope",
)
BASE_AUTO_KEYS = AUTO_KEYS[:-1]
IDENTITY_SOURCE = "ORDER_EXECUTION_CONTEXT"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")


def scope_is_contained(approval: dict[str, Any] | None, request: dict[str, Any] | None) -> bool:
    if not isinstance(approval, dict) or not isinstance(request, dict):
        return False
    if approval.get("approval_status") != "APPROVED" or not approval.get("approval_id"):
        return False
    approved = approval.get("approved_scope")
    requested = request.get("requested_scope")
    if not isinstance(approved, list) or not approved or not isinstance(requested, list) or not requested:
        return False
    if not all(isinstance(item, str) and item for item in approved + requested):
        return False
    return set(requested).issubset(set(approved))


def evaluated_conditions(context: dict[str, Any]) -> dict[str, bool]:
    conditions = {key: context.get(key) is True for key in BASE_AUTO_KEYS}
    conditions["within_approved_scope"] = scope_is_contained(context.get("approval"), context.get("request"))
    return conditions


def decide_user_gate(context: dict[str, Any]) -> dict[str, Any]:
    hold_reasons = (
        ("routing_mismatch", "ROUTING_MISMATCH"),
        ("ssot_conflict", "SSOT_CONFLICT"),
        ("required_evidence_missing", "REQUIRED_EVIDENCE_MISSING"),
        ("validator_error", "VALIDATOR_ERROR"),
        ("new_unverified_failure", "NEW_ROOT_CAUSE_UNCONFIRMED"),
    )
    conditions = evaluated_conditions(context)
    for key, reason in hold_reasons:
        if context.get(key):
            return {
                "decision": "HOLD", "reason_code": reason, "question_count": 0,
                "side_effect_allowed": False, "conditions": conditions,
            }
    if all(conditions.values()):
        return {
            "decision": "AUTO", "reason_code": "ALL_AUTO_CONDITIONS_MET",
            "question_count": 0, "side_effect_allowed": True, "conditions": conditions,
        }
    if all(conditions[key] for key in BASE_AUTO_KEYS) and not conditions["within_approved_scope"]:
        return {
            "decision": "APPROVAL_REQUIRED", "reason_code": "APPROVAL_SCOPE_REQUIRED",
            "question_count": 1, "side_effect_allowed": False, "conditions": conditions,
        }
    return {
        "decision": "HOLD", "reason_code": "AUTO_CONDITIONS_INCOMPLETE",
        "question_count": 0, "side_effect_allowed": False, "conditions": conditions,
    }


def approved_context(approved_scope: list[str], requested_scope: list[str]) -> dict[str, Any]:
    return {
        **{key: True for key in BASE_AUTO_KEYS},
        "approval": {
            "approval_id": "APPROVAL-ORDER-037",
            "approved_scope": approved_scope,
            "approval_status": "APPROVED",
        },
        "request": {"requested_scope": requested_scope},
    }


def scenario_plan(label: str) -> dict[str, Any]:
    executor = FIXTURES / "executor_success.py"
    validator = FIXTURES / "validator_success.py"
    return {
        "task_id": f"TASK-MVP6-{label}", "plan_version": "1.2", "order_id": "Order-039",
        "change_reason_ref": f"Order-039-Scenario-{label}", "write_owner": "Codex",
        "write_scope": ["04_Evidence/mvp_test_6/scenarios"], "shared_resources": [], "depends_on": [],
        "steps": [{"step_id": f"USER-GATE-{label}-001", "action": "execute approved deterministic fixture"}],
        "executor": {"path": executor.relative_to(PROJECT_ROOT).as_posix(), "sha256": sha256_file(executor)},
        "required_validators": [{
            "validator_id": "VAL-USER-GATE-TARGET", "path": validator.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256_file(validator), "criteria": {"expected_value": "phase1-ok"},
        }],
        "completion_criteria": ["approved scenario executes once and passes"],
        "permissions": {"subprocess": "approved fixture paths only", "network": False},
    }


def append_decision(directory: Path, label: str, decision: dict[str, Any], phase: str) -> None:
    EventStore(directory / "events.jsonl").append(
        "USER_GATE_DECISION", task_id=f"TASK-MVP6-{label}", run_id=new_id("DECISION"), plan_version="1.2",
        actor_role="UserGate", payload={**decision, "phase": phase},
    )


def file_snapshot(directory: Path) -> dict[str, str]:
    if not directory.is_dir():
        return {}
    return {
        path.relative_to(directory).as_posix(): sha256_file(path)
        for path in sorted(directory.rglob("*")) if path.is_file()
    }


def changed_file_count(before: dict[str, str], after: dict[str, str]) -> int:
    return sum(before.get(key) != after.get(key) for key in set(before) | set(after))


def routing_entry(
    directory: Path,
    expected_to: str,
    actual_executor: str,
    action: str,
    downstream: Callable[[Callable[..., dict[str, Any]]], Any],
) -> tuple[dict[str, Any], Any]:
    base = evaluate_routing(expected_to, actual_executor, action, "Order-039", "Beta")
    matched = base["routing_result"] == "MATCH" and action == "WRITE"
    before = file_snapshot(directory)
    counters = {"writer_call_count": 0, "run_task_call_count": 0, "downstream_call_count": 0}
    value = None

    def measured_run_task(*args: Any, **kwargs: Any) -> dict[str, Any]:
        counters["run_task_call_count"] += 1
        return run_task(*args, **kwargs)

    if matched:
        counters["writer_call_count"] += 1
        counters["downstream_call_count"] += 1
        value = downstream(measured_run_task)
    after = file_snapshot(directory)
    evidence = {
        "expected_to": expected_to, "actual_executor": actual_executor, "action": action,
        "order_id": "Order-039", "project": "Beta", "identity_source": IDENTITY_SOURCE,
        "routing_result": "MATCH" if matched else "HOLD",
        "mismatch_reason": None if matched else "ROUTING_MISMATCH",
        "write_allowed": matched,
        **counters,
        "beta_write_delta": changed_file_count(before, after),
        "before_snapshot": before,
        "after_snapshot": after,
    }
    return evidence, value


def runtime_counts(directory: Path) -> dict[str, int]:
    events_path = directory / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()] if events_path.is_file() else []
    return {
        "run_started": sum(event["type"] == "RUN_STARTED" for event in events),
        "run_directories": len([path for path in (directory / "runs").iterdir() if path.is_dir()]) if (directory / "runs").is_dir() else 0,
        "runtime_evidence": len(list(directory.glob("EVD-*.json"))),
    }


def decision_execution_entry(
    decision: dict[str, Any],
    directory: Path,
    expected_to: str,
    actual_executor: str,
    downstream: Callable[[Callable[..., dict[str, Any]]], Any],
) -> tuple[dict[str, Any], dict[str, Any] | None, Any]:
    """Enter routing only when the independently visible User Gate decision is AUTO."""
    before_files = file_snapshot(directory)
    before_runtime = runtime_counts(directory)
    route = None
    result = None
    routing_calls = 0
    if decision.get("decision") == "AUTO":
        routing_calls = 1
        route, result = routing_entry(directory, expected_to, actual_executor, "WRITE", downstream)
    after_files = file_snapshot(directory)
    after_runtime = runtime_counts(directory)
    enforcement = {
        "decision": decision.get("decision"),
        "execution_dir": str(directory),
        "routing_entry_call_count": routing_calls,
        "writer_call_count": route["writer_call_count"] if route else 0,
        "run_task_call_count": route["run_task_call_count"] if route else 0,
        "downstream_call_count": route["downstream_call_count"] if route else 0,
        "run_started_delta": after_runtime["run_started"] - before_runtime["run_started"],
        "run_directory_delta": after_runtime["run_directories"] - before_runtime["run_directories"],
        "runtime_evidence_delta": after_runtime["runtime_evidence"] - before_runtime["runtime_evidence"],
        "managed_write_delta": changed_file_count(before_files, after_files),
        "before_snapshot": before_files,
        "after_snapshot": after_files,
    }
    return enforcement, route, result


def idempotent_write(managed: Path, input_key: str) -> str:
    state_path = managed / "state.json"
    evidence_path = managed / "EVD-idempotent.json"
    state = {"input_key": input_key, "status": "completed"}
    evidence = {"input_key": input_key, "result": "PASS"}
    if state_path.is_file() and evidence_path.is_file():
        current_state = json.loads(state_path.read_text(encoding="utf-8"))
        current_evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        if current_state == state and current_evidence == evidence:
            return "NO_CHANGE"
        raise ValueError("idempotency state collision")
    if state_path.exists() or evidence_path.exists():
        raise ValueError("partial idempotency state")
    write_json(state_path, state)
    write_json(evidence_path, evidence)
    return "WRITE"


def assess_recovery(requested_fingerprint: str) -> dict[str, Any]:
    chain = source_chain()
    record = make_record(chain)
    plan = target_plan(record, chain)
    eligible, reasons = validate_candidate(record, chain)
    fingerprint_applicable = requested_fingerprint == record["failure_fingerprint"]
    scope_match = plan["required_validators"][0]["validator_id"] == record["applicable_scope"]["validator_id"]
    fix_contract_valid = chain["source_actual_fix_signature"] == record["fix_signature"] == actual_fix_signature(plan)
    postflight_possible = bool(plan.get("required_validators"))
    allowed = fingerprint_applicable and eligible and scope_match and fix_contract_valid and postflight_possible
    return {
        "requested_fingerprint": requested_fingerprint,
        "prevention_record": record,
        "target_plan": plan,
        "fingerprint_applicable": fingerprint_applicable,
        "prevention_verified": eligible,
        "eligibility_reasons": reasons,
        "scope_match": scope_match,
        "fix_contract_valid": fix_contract_valid,
        "postflight_possible": postflight_possible,
        "decision": "AUTO_RECOVERY_ALLOWED" if allowed else "HOLD",
        "reason_code": None if allowed else "NEW_ROOT_CAUSE_UNCONFIRMED",
        "automatic_fix_count": 0,
        "unauthorized_new_run_count": 0,
        "reused_asset": "03_Tests/fixtures/prevention_scenario_executor.py",
    }


def main() -> int:
    result_path = Path(sys.argv[1]).resolve()
    root = result_path.parents[2].parent / "scenarios" / new_id("SCN")
    root.mkdir(parents=True)

    a_dir = root / "a_auto"
    a_execution = a_dir / "execution"
    context_a = approved_context(["fixture:A"], ["fixture:A"])
    decision_a = decide_user_gate(context_a)
    append_decision(a_dir, "A", decision_a, "PRE_EXECUTION")

    def run_a(measured_run_task: Callable[..., dict[str, Any]]) -> dict[str, Any]:
        plan_path = a_execution / "plan.json"
        write_json(plan_path, scenario_plan("A"))
        return measured_run_task(plan_path, PROJECT_ROOT, a_execution)

    gate_a, routing_a, result_a = decision_execution_entry(decision_a, a_execution, "Codex", "Codex", run_a)
    write_json(a_dir / "decision_execution_evidence.json", gate_a)
    write_json(a_dir / "routing_evidence.json", routing_a)

    b_dir = root / "b_approval_required"
    request_b = {"requested_scope": ["fixture:B"]}
    before_context = {**{key: True for key in BASE_AUTO_KEYS}, "request": request_b}
    decision_b_before = decide_user_gate(before_context)
    append_decision(b_dir, "B", decision_b_before, "BEFORE_APPROVAL")
    b_pre_execution = b_dir / "pre_approval_execution"

    def forbidden_before_approval(measured_run_task: Callable[..., dict[str, Any]]) -> dict[str, Any]:
        plan_path = b_pre_execution / "FORBIDDEN-plan.json"
        write_json(plan_path, scenario_plan("B-PRE"))
        return measured_run_task(plan_path, PROJECT_ROOT, b_pre_execution)

    gate_b_before, routing_b_before, result_b_before = decision_execution_entry(
        decision_b_before, b_pre_execution, "Codex", "Codex", forbidden_before_approval,
    )
    before_counts = runtime_counts(b_pre_execution)
    approval_b = {"approval_id": new_id("APPROVAL"), "approved_scope": ["fixture:B"], "approval_status": "APPROVED"}
    EventStore(b_dir / "events.jsonl").append(
        "USER_APPROVAL_RECORDED", task_id="TASK-MVP6-B", run_id=approval_b["approval_id"],
        plan_version="1.1", actor_role="User", payload={**approval_b, **request_b},
    )
    after_context = {**before_context, "approval": approval_b}
    decision_b_after = decide_user_gate(after_context)
    append_decision(b_dir, "B", decision_b_after, "AFTER_APPROVAL")
    b_execution = b_dir / "approved_execution"

    def run_b(measured_run_task: Callable[..., dict[str, Any]]) -> dict[str, Any]:
        plan_path = b_execution / "plan.json"
        write_json(plan_path, scenario_plan("B"))
        return measured_run_task(plan_path, PROJECT_ROOT, b_execution)

    gate_b_after, routing_b, result_b = decision_execution_entry(decision_b_after, b_execution, "Codex", "Codex", run_b)
    write_json(b_dir / "pre_approval_decision_execution_evidence.json", gate_b_before)
    write_json(b_dir / "approved_decision_execution_evidence.json", gate_b_after)
    write_json(b_dir / "routing_evidence.json", routing_b)

    c_dir = root / "c_hold"
    c_execution = c_dir / "execution"
    context_c = {**approved_context(["fixture:C"], ["fixture:C"]), "ssot_conflict": True}
    decision_c = decide_user_gate(context_c)
    append_decision(c_dir, "C", decision_c, "PRE_EXECUTION")

    def forbidden_hold(measured_run_task: Callable[..., dict[str, Any]]) -> dict[str, Any]:
        plan_path = c_execution / "FORBIDDEN-plan.json"
        write_json(plan_path, scenario_plan("C"))
        return measured_run_task(plan_path, PROJECT_ROOT, c_execution)

    gate_c, _, _ = decision_execution_entry(decision_c, c_execution, "Codex", "Codex", forbidden_hold)
    write_json(c_dir / "hold_evidence.json", {"decision": decision_c, "enforcement": gate_c, "arbitrary_fix_count": 0})

    d_dir = root / "d_scope_expansion"
    d_execution = d_dir / "execution"
    context_d = approved_context(["fixture:D:read"], ["fixture:D:read", "fixture:D:write"])
    decision_d = decide_user_gate(context_d)
    append_decision(d_dir, "D", decision_d, "PRE_APPROVAL")

    def forbidden_scope_expansion(measured_run_task: Callable[..., dict[str, Any]]) -> dict[str, Any]:
        plan_path = d_execution / "FORBIDDEN-plan.json"
        write_json(plan_path, scenario_plan("D"))
        return measured_run_task(plan_path, PROJECT_ROOT, d_execution)

    gate_d, _, _ = decision_execution_entry(decision_d, d_execution, "Codex", "Codex", forbidden_scope_expansion)
    write_json(d_dir / "approval_evidence.json", {"decision": decision_d, "enforcement": gate_d})

    g_dir = root / "g_c3_false"
    g_execution = g_dir / "execution"
    context_g = approved_context(["fixture:G"], ["fixture:G"])
    context_g["fixture_runtime_pass"] = False
    decision_g = decide_user_gate(context_g)
    append_decision(g_dir, "G", decision_g, "PRE_EXECUTION")

    def forbidden_c3_false(measured_run_task: Callable[..., dict[str, Any]]) -> dict[str, Any]:
        plan_path = g_execution / "FORBIDDEN-plan.json"
        write_json(plan_path, scenario_plan("G"))
        return measured_run_task(plan_path, PROJECT_ROOT, g_execution)

    gate_g, _, _ = decision_execution_entry(decision_g, g_execution, "Codex", "Codex", forbidden_c3_false)
    write_json(g_dir / "condition_failure_evidence.json", {"decision": decision_g, "enforcement": gate_g})

    e_dir = root / "e_idempotent_reentry"
    managed = e_dir / "managed"
    before_e = file_snapshot(managed)
    first_status = idempotent_write(managed, "same-approved-input")
    after_first_e = file_snapshot(managed)
    second_status = idempotent_write(managed, "same-approved-input")
    after_reentry_e = file_snapshot(managed)
    write_json(e_dir / "idempotency_evidence.json", {
        "managed_path": str(managed), "before": before_e, "after_first": after_first_e,
        "after_reentry": after_reentry_e, "first_status": first_status, "reentry_status": second_status,
        "reentry_write_delta": changed_file_count(after_first_e, after_reentry_e),
        "reentry_evidence_delta": len([key for key in after_reentry_e if key.startswith("EVD-")]) - len([key for key in after_first_e if key.startswith("EVD-")]),
    })

    f_dir = root / "f_routing_mismatch"
    f_execution = f_dir / "execution"
    context_f = approved_context(["fixture:F"], ["fixture:F"])
    decision_f = decide_user_gate(context_f)
    append_decision(f_dir, "F", decision_f, "PRE_ROUTING")

    def forbidden_downstream(measured_run_task: Callable[..., dict[str, Any]]) -> dict[str, Any]:
        write_json(f_execution / "FORBIDDEN-WRITE.json", {"should_not_exist": True})
        return measured_run_task(f_execution / "missing-plan.json", PROJECT_ROOT, f_execution)

    gate_f, routing_f, _ = decision_execution_entry(decision_f, f_execution, "Claude Code", "Codex", forbidden_downstream)
    EventStore(f_dir / "events.jsonl").append(
        "ROUTING_DECISION", task_id="TASK-MVP6-F", run_id=new_id("ROUTE"), plan_version="1.2",
        actor_role="Router", payload=routing_f,
    )
    write_json(f_dir / "decision_execution_evidence.json", gate_f)
    write_json(f_dir / "routing_evidence.json", routing_f)

    valid_recovery = assess_recovery(source_chain()["fingerprint"]["fingerprint"])
    invalid_recovery = assess_recovery("UNVERIFIED-NEW-FINGERPRINT")
    evidence_links = [
        {"path": str(path), "sha256": sha256_file(path)}
        for path in sorted(root.rglob("*")) if path.is_file()
    ]
    output = {
        "mvp_test_id": "MVP-TEST-6", "mvp_test_name": "User Gate",
        "test_plan_id": "MVP-TEST-6-USER-GATE", "test_plan_version": "1.2",
        "scenario_root": str(root),
        "scenario_dirs": {"A": str(a_dir), "B": str(b_dir), "C": str(c_dir), "D": str(d_dir), "E": str(e_dir), "F": str(f_dir)},
        "delta_dirs": {"D1": str(a_execution), "D2_before": str(b_pre_execution), "D2_after": str(b_execution), "D3": str(d_execution), "D4": str(g_execution), "D5": str(c_execution), "D6": str(f_execution)},
        "contexts": {"A": context_a, "B_before": before_context, "B_after": after_context, "C": context_c, "D": context_d, "G": context_g, "F": context_f},
        "decisions": {"A": decision_a, "B_before": decision_b_before, "B_after": decision_b_after, "C": decision_c, "D": decision_d, "G": decision_g, "F": decision_f},
        "results": {"A": result_a, "B": result_b, "B_before": result_b_before},
        "routing": {"A": routing_a, "B": routing_b, "F": routing_f},
        "execution_gates": {"D1": gate_a, "D2_before": gate_b_before, "D2_after": gate_b_after, "D3": gate_d, "D4": gate_g, "D5": gate_c, "D6": gate_f},
        "b_runtime_before_approval": before_counts,
        "b_duplicate_approval_questions": decide_user_gate(after_context)["question_count"],
        "recovery": {"verified": valid_recovery, "new_failure": invalid_recovery},
        "scenario_evidence": evidence_links,
    }
    write_json(result_path, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
