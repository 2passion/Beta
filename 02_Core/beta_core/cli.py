"""CLI orchestration for the Local Core MVP Phase 1 vertical slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .event_store import EventStore, append_jsonl
from .executor import run_executor
from .gate import decide_gate
from .model import load_task_plan, new_id, sha256_file, utc_now, validate_contract, validate_pinned_programs
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
    append_jsonl(evidence_dir / "evidence_index.jsonl", index_record)
    return index_record


def run_task(
    task_path: Path,
    project_root: Path,
    evidence_dir: Path,
    executor_timeout_seconds: float = 10.0,
    validator_timeout_seconds: float = 10.0,
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
    resolved, pin_errors = validate_pinned_programs(plan, project_root)
    if pin_errors:
        return _blocked(store, plan, run_id, pin_errors)

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
    execution = run_executor(resolved["executor"], result_path, executor_timeout_seconds)
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
        validation = run_validator(
            validator_id,
            resolved[f"validator:{validator_id}"],
            result_path,
            spec.get("criteria"),
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
    return {
        "status": status,
        "task_id": task_id,
        "plan_version": plan_version,
        "run_id": run_id,
        "execution": execution["status"],
        "validation": validation_status,
        "gate": gate,
        "evidence": evidence,
    }


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
