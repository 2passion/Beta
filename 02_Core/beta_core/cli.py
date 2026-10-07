"""CLI orchestration for the Local Core MVP Phase 1 vertical slice."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Collection
from pathlib import Path
from typing import Any

from .event_store import EventStore, append_jsonl
from .executor import run_executor
from .gate import decide_gate
from .model import load_task_plan, new_id, sha256_file, utc_now, validate_contract, validate_pinned_programs
from .runtime_policy import (
    load_runtime_policy,
    prepare_runtime_program_snapshot,
    runtime_code_baseline,
    runtime_request_payload_and_hash,
    validate_runtime_plan_policy,
)
from .user_gate import claim_user_gate_authorization
from .validator_runner import run_validator


def _blocked(
    store: EventStore,
    plan: dict[str, Any],
    run_id: str,
    reasons: list[str],
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_id = str(plan.get("task_id", "TASK-UNKNOWN"))
    plan_version = str(plan.get("plan_version", "UNKNOWN"))
    store.append(
        "BLOCKED",
        task_id=task_id,
        run_id=run_id,
        plan_version=plan_version,
        actor_role="Gate",
        payload={"reasons": reasons, **({"contract": contract} if contract else {})},
    )
    return {
        "status": "BLOCKED",
        "task_id": task_id,
        "plan_version": plan_version,
        "run_id": run_id,
        "execution": "NOT_RUN",
        "validation": "NOT_RUN",
        "gate": "BLOCK",
        "evidence": None,
        "reasons": reasons,
    }


def _write_evidence(
    evidence_dir: Path,
    plan: dict[str, Any],
    run_id: str,
    execution: dict[str, Any],
    validations: list[dict[str, Any]],
    validation_status: str,
    contract: dict[str, Any],
) -> dict[str, Any]:
    evidence_id = new_id("EVD")
    filename = f"{evidence_id}.json"
    body_path = evidence_dir / filename
    predicted_gate = decide_gate(execution, validations, evidence_recorded=True)
    body = {
        "evidence_id": evidence_id,
        "run_id": run_id,
        "task_id": plan["task_id"],
        "plan_version": plan["plan_version"],
        "order_id": plan["order_id"],
        "created_at": utc_now(),
        "execution": execution,
        "validation_result": validation_status,
        "validations": validations,
        "gate": predicted_gate,
        "task_plan_sha256": contract["task_plan_sha256"],
        "executor_sha256": contract["executor_sha256"],
        "validator_sha256": contract["validator_sha256"],
        "change_reason_ref": contract["change_reason_ref"],
    }
    runtime_request = contract.get("runtime_request")
    if isinstance(runtime_request, dict):
        body["runtime_request"] = runtime_request
        body["runtime_request_hash"] = contract["runtime_request_hash"]
        body["runtime_code_baseline_hash"] = contract["runtime_code_baseline_hash"]
        body["user_gate_decision_ref"] = contract["user_gate_decision_ref"]
        body["approved_git_commit"] = contract["approved_git_commit"]
        body["executor_path"] = contract["executor_path"]
        body["validator_path"] = contract["validator_path"]
        body["executor_snapshot"] = contract["executor_snapshot"]
        body["validator_snapshots"] = contract["validator_snapshots"]
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with body_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(body, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    digest = sha256_file(body_path)
    index_record = {
        "evidence_id": evidence_id,
        "filename": filename,
        "run_id": run_id,
        "task_id": plan["task_id"],
        "plan_version": plan["plan_version"],
        "path": str(body_path.resolve()),
        "sha256": digest,
        "created_at": body["created_at"],
        "validation_result": validation_status,
        "gate": predicted_gate,
        "task_plan_sha256": contract["task_plan_sha256"],
        "executor_sha256": contract["executor_sha256"],
        "validator_sha256": contract["validator_sha256"],
        "change_reason_ref": contract["change_reason_ref"],
    }
    if isinstance(runtime_request, dict):
        index_record.update(
            {
                "request_id": runtime_request.get("request_id"),
                "approval_ref": runtime_request.get("approval_ref"),
                "operation": runtime_request.get("operation"),
                "target_path": runtime_request.get("target_path"),
                "runtime_request_hash": contract["runtime_request_hash"],
                "runtime_code_baseline_hash": contract["runtime_code_baseline_hash"],
                "user_gate_decision_ref": contract["user_gate_decision_ref"],
                "approved_git_commit": contract["approved_git_commit"],
                "executor_path": contract["executor_path"],
                "validator_path": contract["validator_path"],
                "executor_snapshot": contract["executor_snapshot"],
                "validator_snapshots": contract["validator_snapshots"],
            }
        )
    append_jsonl(evidence_dir / "evidence_index.jsonl", index_record)
    return index_record


def run_task(
    task_path: Path,
    project_root: Path,
    evidence_dir: Path,
    executor_timeout_seconds: float = 10.0,
    validator_timeout_seconds: float = 10.0,
    approved_program_paths: Collection[Path] | None = None,
    user_gate_authorization: Any = None,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    evidence_dir = evidence_dir.resolve()
    task_path = task_path.resolve()
    task_plan_sha256 = sha256_file(task_path)
    plan = load_task_plan(task_path)
    run_id = new_id("RUN")
    store = EventStore(evidence_dir / "events.jsonl")

    contract_errors = validate_contract(plan)
    if contract_errors:
        return _blocked(store, plan, run_id, contract_errors)
    if approved_program_paths is not None:
        return _blocked(store, plan, run_id, ["caller-supplied executable allowlist is prohibited"])
    if "runtime_request" in plan:
        resolved, pin_errors = validate_runtime_plan_policy(plan, project_root)
    else:
        resolved, pin_errors = validate_pinned_programs(plan, project_root)
    if pin_errors:
        return _blocked(store, plan, run_id, pin_errors)

    user_gate_decision_ref: str | None = None
    canonical_payload: dict[str, Any] | None = None
    calculated_code_baseline_hash: str | None = None
    if isinstance(plan.get("runtime_request"), dict):
        try:
            policy = load_runtime_policy(project_root)
            canonical_payload, calculated_hash = runtime_request_payload_and_hash(plan["runtime_request"], project_root, policy)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return _blocked(store, plan, run_id, [str(exc)])
        if plan.get("runtime_request_hash") != calculated_hash:
            return _blocked(store, plan, run_id, ["runtime_request_hash mismatch"])
        try:
            _, calculated_code_baseline_hash = runtime_code_baseline(project_root)
        except (OSError, TypeError, ValueError) as exc:
            return _blocked(store, plan, run_id, [str(exc)])
        if plan.get("runtime_code_baseline_hash") != calculated_code_baseline_hash:
            return _blocked(store, plan, run_id, ["runtime_code_baseline_hash mismatch"])
        user_gate_decision_ref, authorization_errors = claim_user_gate_authorization(
            user_gate_authorization,
            project_root=project_root,
            execution_context=plan["runtime_request"].get("execution_context"),
            runtime_request_hash=calculated_hash,
            runtime_code_baseline_hash=calculated_code_baseline_hash,
            approved_git_commit=canonical_payload["approved_git_commit"],
        )
        if authorization_errors:
            return _blocked(store, plan, run_id, authorization_errors)

    task_id = plan["task_id"]
    plan_version = plan["plan_version"]
    contract = {
        "task_plan_sha256": task_plan_sha256,
        "executor_sha256": plan["executor"]["sha256"],
        "validator_sha256": [
            {"validator_id": spec["validator_id"], "sha256": spec["sha256"]}
            for spec in plan["required_validators"]
        ],
        "change_reason_ref": plan["change_reason_ref"],
    }
    if isinstance(plan.get("runtime_request"), dict):
        contract["runtime_request"] = plan["runtime_request"]
        contract["runtime_request_hash"] = plan["runtime_request_hash"]
        contract["runtime_code_baseline_hash"] = plan["runtime_code_baseline_hash"]
        contract["user_gate_decision_ref"] = user_gate_decision_ref
        contract["approved_git_commit"] = canonical_payload["approved_git_commit"] if canonical_payload else None
        contract["executor_path"] = plan["executor"]["path"]
        contract["validator_path"] = [
            {"validator_id": spec["validator_id"], "path": spec["path"]}
            for spec in plan["required_validators"]
        ]
        contract["executor_snapshot"] = None
        contract["validator_snapshots"] = []
    first_plan_hash = store.first_plan_hash(task_id, plan_version)
    if first_plan_hash is not None and first_plan_hash != task_plan_sha256:
        return _blocked(
            store,
            plan,
            run_id,
            ["task_plan_sha256 differs for an existing task_id/plan_version"],
            {**contract, "first_task_plan_sha256": first_plan_hash},
        )
    store.append(
        "RUN_STARTED",
        task_id=task_id,
        run_id=run_id,
        plan_version=plan_version,
        actor_role="CLI",
        payload={"order_id": plan["order_id"], "write_owner": plan["write_owner"], **contract},
    )
    result_path = evidence_dir / "runs" / run_id / "executor_result.json"
    execution_request = None
    if isinstance(plan.get("runtime_request"), dict):
        execution_request = {**plan["runtime_request"], "run_id": run_id}
    executor_path = resolved["executor"]
    if isinstance(plan.get("runtime_request"), dict):
        executor_path, executor_snapshot, snapshot_errors = prepare_runtime_program_snapshot(
            plan,
            project_root,
            program_key="executor",
            expected_sha256=plan["executor"]["sha256"],
            evidence_dir=evidence_dir,
            run_id=run_id,
        )
        if snapshot_errors or executor_path is None or executor_snapshot is None:
            return _blocked(store, plan, run_id, snapshot_errors or ["executor snapshot unavailable"], contract)
        contract["executor_snapshot"] = executor_snapshot
        store.append(
            "EXECUTION_SNAPSHOT_RECORDED",
            task_id=task_id,
            run_id=run_id,
            plan_version=plan_version,
            actor_role="CLI",
            payload=executor_snapshot,
        )
    execution = run_executor(
        executor_path,
        result_path,
        executor_timeout_seconds,
        runtime_request=execution_request,
        snapshot_sha256=executor_snapshot["sha256"] if isinstance(plan.get("runtime_request"), dict) else None,
        snapshot_allowed_names={"executor.py"} if isinstance(plan.get("runtime_request"), dict) else None,
    )
    if execution["status"] != "PASS":
        store.append(
            "EXECUTION_ERROR",
            task_id=task_id,
            run_id=run_id,
            plan_version=plan_version,
            actor_role="Executor",
            payload=execution,
        )
        store.append(
            "GATE_DECISION",
            task_id=task_id,
            run_id=run_id,
            plan_version=plan_version,
            actor_role="Gate",
            payload={"decision": "BLOCK", "reason": "EXECUTION_ERROR"},
        )
        return {"status": "ERROR", "task_id": task_id, "plan_version": plan_version, "run_id": run_id, "execution": "ERROR", "validation": "NOT_RUN", "gate": "BLOCK", "evidence": None}
    store.append(
        "RUN_COMPLETED",
        task_id=task_id,
        run_id=run_id,
        plan_version=plan_version,
        actor_role="Executor",
        payload={"status": "PASS", "result_path": str(result_path)},
    )
    checkpoint = {
        "stage_id": plan["steps"][0]["step_id"],
        "state_path": str(result_path),
        "state_sha256": sha256_file(result_path),
    }
    store.append(
        "CHECKPOINT_RECORDED",
        task_id=task_id,
        run_id=run_id,
        plan_version=plan_version,
        actor_role="Executor",
        payload=checkpoint,
    )

    validations: list[dict[str, Any]] = []
    for spec in plan["required_validators"]:
        validator_id = spec["validator_id"]
        store.append(
            "VALIDATION_STARTED",
            task_id=task_id,
            run_id=run_id,
            plan_version=plan_version,
            actor_role="Validator",
            payload={"validator_id": validator_id, "sha256": spec["sha256"]},
        )
        criteria = spec.get("criteria")
        if isinstance(plan.get("runtime_request"), dict) and isinstance(criteria, dict):
            criteria = {**criteria, "run_id": run_id}
        validator_path = resolved[f"validator:{validator_id}"]
        if isinstance(plan.get("runtime_request"), dict):
            validator_path, validator_snapshot, snapshot_errors = prepare_runtime_program_snapshot(
                plan,
                project_root,
                program_key=f"validator:{validator_id}",
                expected_sha256=spec["sha256"],
                evidence_dir=evidence_dir,
                run_id=run_id,
            )
            if snapshot_errors or validator_path is None or validator_snapshot is None:
                validation = {
                    "validator_id": validator_id,
                    "status": "ERROR",
                    "exit_code": None,
                    "stdout": "",
                    "stderr": "; ".join(snapshot_errors or ["validator snapshot unavailable"]),
                }
            else:
                contract["validator_snapshots"].append(validator_snapshot)
                store.append(
                    "EXECUTION_SNAPSHOT_RECORDED",
                    task_id=task_id,
                    run_id=run_id,
                    plan_version=plan_version,
                    actor_role="CLI",
                    payload=validator_snapshot,
                )
                validation = run_validator(
                    validator_id,
                    validator_path,
                    result_path,
                    criteria,
                    validator_timeout_seconds,
                    snapshot_sha256=validator_snapshot["sha256"],
                    snapshot_allowed_names={"executor.py", Path(validator_snapshot["relative_path"]).name},
                )
        else:
            validation = run_validator(
                validator_id,
                validator_path,
                result_path,
                criteria,
                validator_timeout_seconds,
            )
        validations.append(validation)
        store.append(
            "VALIDATION_RESULT",
            task_id=task_id,
            run_id=run_id,
            plan_version=plan_version,
            actor_role="Validator",
            payload=validation,
        )

    validation_status = "ERROR" if any(v["status"] == "ERROR" for v in validations) else "FAIL" if any(v["status"] == "FAIL" for v in validations) else "PASS"
    try:
        evidence = _write_evidence(evidence_dir, plan, run_id, execution, validations, validation_status, contract)
        evidence_recorded = True
        store.append(
            "EVIDENCE_RECORDED",
            task_id=task_id,
            run_id=run_id,
            plan_version=plan_version,
            actor_role="Evidence",
            payload=evidence,
        )
    except (OSError, ValueError) as exc:
        evidence = None
        evidence_recorded = False
        validation_status = "ERROR"
        validations.append({"validator_id": "EVIDENCE-WRITE", "status": "ERROR", "exit_code": None, "stdout": "", "stderr": str(exc)})

    gate = decide_gate(execution, validations, evidence_recorded)
    store.append(
        "GATE_DECISION",
        task_id=task_id,
        run_id=run_id,
        plan_version=plan_version,
        actor_role="Gate",
        payload={"decision": gate, "validation": validation_status, "evidence_recorded": evidence_recorded},
    )
    status = "PASS" if gate == "PROCEED" else "ERROR" if validation_status == "ERROR" else "FAIL"
    result = {
        "status": status,
        "task_id": task_id,
        "plan_version": plan_version,
        "run_id": run_id,
        "execution": execution["status"],
        "validation": validation_status,
        "gate": gate,
        "evidence": evidence,
    }
    if isinstance(plan.get("runtime_request"), dict):
        result["runtime_request_hash"] = plan["runtime_request_hash"]
        result["runtime_code_baseline_hash"] = plan["runtime_code_baseline_hash"]
        result["user_gate_decision_ref"] = user_gate_decision_ref
        result["approved_git_commit"] = canonical_payload["approved_git_commit"] if canonical_payload else None
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Beta Local Core MVP Phase 1")
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--executor-timeout", type=float, default=10.0)
    parser.add_argument("--validator-timeout", type=float, default=10.0)
    args = parser.parse_args(argv)
    try:
        result = run_task(
            args.task,
            args.project_root,
            args.evidence_dir,
            executor_timeout_seconds=args.executor_timeout,
            validator_timeout_seconds=args.validator_timeout,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1 if result["status"] == "FAIL" else 2


if __name__ == "__main__":
    sys.exit(main())
