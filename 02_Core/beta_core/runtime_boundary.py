"""Minimal approved-input boundary for one read-only production operation."""

from __future__ import annotations

import json
import re
import stat
from pathlib import Path
from typing import Any

from .cli import run_task
from .event_store import EventStore
from .model import sha256_file
from .runtime_policy import (
    canonical_local_path,
    load_runtime_policy,
    runtime_code_baseline,
    runtime_request_payload_and_hash,
    trusted_programs,
    validate_runtime_plan_policy,
    verify_production_trust_anchor,
)
from .user_gate import inspect_user_gate_authorization


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPROVED_ROOT = PROJECT_ROOT
FIRST_RUNTIME_TARGET = PROJECT_ROOT / "Beta-Index.md"
EXECUTOR_PATH = Path(__file__).with_name("file_integrity_executor.py").resolve()
VALIDATOR_PATH = Path(__file__).with_name("file_integrity_validator.py").resolve()
EVIDENCE_ROOT = PROJECT_ROOT / "04_Evidence" / "runtime" / "read_only_integrity"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL", "CLOCK$", "CONIN$", "CONOUT$",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
INPUT_REQUEST_FIELDS = {
    "request_id",
    "approval_ref",
    "operation",
    "target_path",
    "approved_root",
    "task_count",
    "parallel_allowed",
    "dependencies",
    "expected_target_side_effect",
    "network",
    "external_publish",
    "execution_context",
}


def _result(status: str, decision: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": status,
        "decision": decision,
        "reason": reason,
        "run_task_call_count": 0,
        **extra,
    }


def _observe(path: Path) -> dict[str, Any]:
    stat_result = path.stat()
    return {
        "path": str(path.resolve()),
        "exists": path.is_file(),
        "size": stat_result.st_size,
        "sha256": sha256_file(path),
    }


def _path_problem(raw_path: Any) -> str | None:
    if not isinstance(raw_path, str) or not raw_path:
        return "TARGET_PATH_INVALID"
    if any(token in raw_path for token in ("*", "?", "[", "]")):
        return "TARGET_PATH_WILDCARD"
    if raw_path.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")):
        return "TARGET_PATH_DEVICE_OR_UNC"
    path = Path(raw_path)
    if not path.is_absolute():
        return "TARGET_PATH_RELATIVE"
    # A colon is valid only as the drive separator (for example C:).
    if ":" in raw_path[2:]:
        return "TARGET_PATH_ADS"
    for part in path.parts[1:]:
        stem = part.rstrip(" .").split(".", 1)[0].upper()
        if stem in WINDOWS_RESERVED or part != part.rstrip(" ."):
            return "TARGET_PATH_RESERVED_OR_AMBIGUOUS"
    return None


def _is_reparse_or_symlink(path: Path) -> bool:
    info = path.lstat()
    attributes = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse_flag)


def _has_reparse_component(path: Path) -> bool:
    current = path
    while True:
        if _is_reparse_or_symlink(current):
            return True
        if current.parent == current:
            return False
        current = current.parent


def _validate_request(request: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not isinstance(request, dict):
        return None, _result("HOLD", "HOLD", "REQUEST_NOT_OBJECT")
    if set(request) != INPUT_REQUEST_FIELDS:
        return None, _result("HOLD", "HOLD", "UNKNOWN_OR_MISSING_CONTRACT_FIELD")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or REQUEST_ID_PATTERN.fullmatch(request_id) is None:
        return None, _result("HOLD", "HOLD", "REQUEST_ID_INVALID")
    if request_id.upper() in WINDOWS_RESERVED:
        return None, _result("HOLD", "HOLD", "REQUEST_ID_RESERVED")
    approval_ref = request.get("approval_ref")
    if not isinstance(approval_ref, str) or not approval_ref.strip():
        return None, _result("APPROVAL_REQUIRED", "APPROVAL_REQUIRED", "APPROVAL_MISSING")
    if request.get("operation") != "READ_ONLY_INTEGRITY":
        return None, _result("HOLD", "HOLD", "CONTRACT_OPERATION_INVALID")
    if type(request.get("task_count")) is not int or request.get("task_count") != 1:
        return None, _result("HOLD", "HOLD", "CONTRACT_TASK_COUNT_INVALID")
    for key in ("parallel_allowed", "network", "external_publish"):
        if type(request.get(key)) is not bool or request.get(key) is not False:
            return None, _result("HOLD", "HOLD", f"CONTRACT_{key.upper()}_INVALID")
    if type(request.get("dependencies")) is not list or request.get("dependencies") != []:
        return None, _result("HOLD", "HOLD", "CONTRACT_DEPENDENCIES_INVALID")
    if request.get("expected_target_side_effect") != "NONE":
        return None, _result("HOLD", "HOLD", "CONTRACT_EXPECTED_TARGET_SIDE_EFFECT_INVALID")
    raw_target = request.get("target_path")
    problem = _path_problem(raw_target)
    if problem:
        return None, _result("HOLD", "HOLD", problem)
    raw_target_path = Path(raw_target)
    if not raw_target_path.exists():
        return None, _result("HOLD", "HOLD", "TARGET_MISSING")
    try:
        if _has_reparse_component(raw_target_path):
            return None, _result("HOLD", "HOLD", "TARGET_IDENTITY_UNSAFE")
    except OSError:
        return None, _result("HOLD", "HOLD", "TARGET_IDENTITY_UNCONFIRMED")
    target = raw_target_path.resolve()
    approved_root = APPROVED_ROOT.resolve()
    approved_target = FIRST_RUNTIME_TARGET.resolve()
    try:
        approved_root_matches = canonical_local_path(request.get("approved_root")) == canonical_local_path(str(approved_root))
    except (OSError, TypeError, ValueError):
        approved_root_matches = False
    if not approved_root_matches:
        return None, _result("HOLD", "HOLD", "APPROVED_ROOT_MISMATCH")
    if target != approved_target or not target.is_relative_to(approved_root):
        return None, _result("HOLD", "HOLD", "TARGET_OUT_OF_SCOPE")
    if not target.exists() or not target.is_file():
        return None, _result("HOLD", "HOLD", "TARGET_MISSING")
    try:
        policy = load_runtime_policy(PROJECT_ROOT)
    except (OSError, ValueError, json.JSONDecodeError):
        return None, _result("HOLD", "HOLD", "TRUSTED_POLICY_INVALID")
    context = request.get("execution_context")
    if context == "PRODUCTION":
        _, anchor_errors = verify_production_trust_anchor(request, PROJECT_ROOT, policy)
        if anchor_errors:
            return None, _result("APPROVAL_REQUIRED", "APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_NOT_ISSUED", trust_anchor_errors=anchor_errors)
    elif context == "TEST_FIXTURE":
        fixture_root = (PROJECT_ROOT / policy["test_fixture"]["approved_root"]).resolve()
        if approval_ref != policy["test_fixture"].get("approval_ref"):
            return None, _result("APPROVAL_REQUIRED", "APPROVAL_REQUIRED", "FIXTURE_APPROVAL_MISMATCH")
        if not approved_root.is_relative_to(fixture_root) or not target.is_relative_to(approved_root):
            return None, _result("HOLD", "HOLD", "FIXTURE_SCOPE_INVALID")
    else:
        return None, _result("HOLD", "HOLD", "EXECUTION_CONTEXT_INVALID")
    try:
        if _is_reparse_or_symlink(target):
            return None, _result("HOLD", "HOLD", "TARGET_IDENTITY_UNSAFE")
        preflight = _observe(target)
    except OSError:
        return None, _result("HOLD", "HOLD", "TARGET_OBSERVATION_ERROR")
    normalized = dict(request)
    normalized["target_path"] = str(target)
    normalized["approved_root"] = str(approved_root)
    normalized["preflight"] = preflight
    return normalized, None


def _relative_program(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def _build_plan(
    request: dict[str, Any],
    evidence_dir: Path,
    runtime_request_hash: str,
    runtime_code_baseline_hash: str,
) -> dict[str, Any]:
    _, executor, validator = trusted_programs(PROJECT_ROOT)
    return {
        "task_id": f"RUNTIME-{request['request_id']}",
        "plan_version": "1.0",
        "order_id": "Order-066",
        "write_owner": "Codex",
        "write_scope": [str(evidence_dir.resolve())],
        "shared_resources": [],
        "depends_on": [],
        "steps": [{"step_id": "READ_ONLY_INTEGRITY", "action": "observe one approved file"}],
        "executor": {"path": executor["path"], "sha256": executor["sha256"]},
        "required_validators": [{
            "validator_id": validator["validator_id"],
            "path": validator["path"],
            "sha256": validator["sha256"],
            "criteria": {
                "request_id": request["request_id"],
                "approval_ref": request["approval_ref"],
                "target_path": request["target_path"],
                "preflight": request["preflight"],
            },
        }],
        "completion_criteria": ["independent path/existence/size/SHA-256 match", "target before/after SHA unchanged"],
        "permissions": {
            "read": [request["target_path"]],
            "write": [str(evidence_dir.resolve())],
            "network": False,
            "external_publish": False,
            "target_write_count": 0,
        },
        "change_reason_ref": "Order-066",
        "runtime_request": request,
        "runtime_request_hash": runtime_request_hash,
        "runtime_code_baseline_hash": runtime_code_baseline_hash,
    }


def prepare_runtime_request(request: Any) -> dict[str, Any]:
    """Validate and return the canonical payload/hash to show at Final User Gate."""
    normalized, rejected = _validate_request(request)
    if rejected is not None:
        return rejected
    assert normalized is not None
    try:
        policy = load_runtime_policy(PROJECT_ROOT)
        payload, request_hash = runtime_request_payload_and_hash(normalized, PROJECT_ROOT, policy)
        code_manifest, code_baseline_hash = runtime_code_baseline(PROJECT_ROOT)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return _result("HOLD", "HOLD", "REQUEST_HASH_PREPARATION_FAILED", detail=str(exc))
    return {
        "status": "READY_FOR_FINAL_USER_GATE",
        "decision": "APPROVAL_REQUIRED",
        "runtime_request_hash": request_hash,
        "runtime_code_baseline": code_manifest,
        "runtime_code_baseline_hash": code_baseline_hash,
        "approved_git_commit": payload["approved_git_commit"],
        "user_gate_display": {
            "target": normalized["target_path"],
            "operation": normalized["operation"],
            "target_write": "NONE",
            "network": False,
            "external_publish": False,
            "approved_git_commit": payload["approved_git_commit"],
            "runtime_request_hash": request_hash,
            "runtime_code_baseline_hash": code_baseline_hash,
            "executor_sha256": payload["executor_sha256"],
            "validator_sha256": payload["validator_sha256"],
        },
        "canonical_payload": payload,
        "normalized_request": normalized,
        "run_task_call_count": 0,
    }


def _read_json_lines(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("JSONL record is not an object")
            records.append(value)
    return records


def _verify_snapshot_artifacts(
    evidence_dir: Path,
    body: dict[str, Any],
    run_events: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Verify the preserved run-local snapshots used by Executor and Validator."""
    failures: list[str] = []
    try:
        executor_snapshot = body.get("executor_snapshot")
        validator_snapshots = body.get("validator_snapshots")
        if not isinstance(executor_snapshot, dict) or not isinstance(validator_snapshots, list) or len(validator_snapshots) != 1:
            return ["snapshot Evidence contract is incomplete"]
        contracts = [executor_snapshot, *validator_snapshots]
        expected_roles = ["executor", f"validator:{body['validations'][0]['validator_id']}"]
        snapshot_dir = (evidence_dir / "runs" / body["run_id"] / "execution_snapshot").resolve()
        expected_paths: list[Path] = []
        for contract, role in zip(contracts, expected_roles, strict=True):
            if set(contract) != {"role", "relative_path", "sha256", "lifecycle", "python_isolated_mode"}:
                failures.append(f"{role} snapshot contract schema mismatch")
                continue
            relative = Path(str(contract.get("relative_path")))
            path = (evidence_dir / relative).resolve()
            if relative.is_absolute() or ".." in relative.parts or path.parent != snapshot_dir:
                failures.append(f"{role} snapshot identity mismatch")
                continue
            if contract.get("role") != role:
                failures.append(f"{role} snapshot role mismatch")
            if contract.get("lifecycle") != "PRESERVED_FOR_NO_CHANGE" or contract.get("python_isolated_mode") is not True:
                failures.append(f"{role} snapshot lifecycle mismatch")
            if not path.is_file() or sha256_file(path) != contract.get("sha256"):
                failures.append(f"{role} preserved snapshot SHA-256 mismatch")
            expected_paths.append(path)
        if snapshot_dir.is_dir():
            actual_names = {item.name for item in snapshot_dir.iterdir()}
            expected_names = {path.name for path in expected_paths}
            if actual_names != expected_names:
                failures.append("snapshot directory contains unexpected sibling")
        else:
            failures.append("preserved snapshot directory is missing")
        if body.get("execution", {}).get("snapshot_sha256") != executor_snapshot.get("sha256"):
            failures.append("Executor final snapshot SHA Evidence mismatch")
        if body.get("validations", [{}])[0].get("snapshot_sha256") != validator_snapshots[0].get("sha256"):
            failures.append("Validator final snapshot SHA Evidence mismatch")
        if run_events is not None:
            snapshot_events = [event.get("payload") for event in run_events if event.get("type") == "EXECUTION_SNAPSHOT_RECORDED"]
            if snapshot_events != contracts:
                failures.append("snapshot Event/Evidence linkage mismatch")
    except (IndexError, KeyError, OSError, TypeError, ValueError):
        failures.append("snapshot Evidence verification failed")
    return failures


def verify_runtime_evidence(
    *, evidence_dir: Path, task_plan_path: Path, request: dict[str, Any], core_result: dict[str, Any]
) -> dict[str, Any]:
    """Recompute the runtime identity, hash, and evidence chain independently."""
    failures: list[str] = []
    try:
        policy, trusted_executor, trusted_validator = trusted_programs(PROJECT_ROOT)
        canonical_payload, calculated_request_hash = runtime_request_payload_and_hash(request, PROJECT_ROOT, policy)
        _, calculated_code_baseline_hash = runtime_code_baseline(PROJECT_ROOT)
        index_records = _read_json_lines(evidence_dir / "evidence_index.jsonl")
        matching = [item for item in index_records if item.get("run_id") == core_result.get("run_id")]
        if len(matching) != 1:
            raise ValueError("exactly one Evidence index record is required")
        index = matching[0]
        body_path = evidence_dir / str(index["filename"])
        body = json.loads(body_path.read_text(encoding="utf-8"))
        plan = json.loads(task_plan_path.read_text(encoding="utf-8"))
        current = _observe(Path(request["target_path"]))
        checks = {
            "evidence_sha256": (index.get("sha256"), sha256_file(body_path)),
            "evidence_id": (index.get("evidence_id"), body.get("evidence_id")),
            "run_id index/body": (index.get("run_id"), body.get("run_id")),
            "run_id body/result": (body.get("run_id"), core_result.get("run_id")),
            "task_id index/body": (index.get("task_id"), body.get("task_id")),
            "task_id body/plan": (body.get("task_id"), plan.get("task_id")),
            "task_plan_sha256": (body.get("task_plan_sha256"), sha256_file(task_plan_path)),
            "request contract": (body.get("runtime_request"), request),
            "runtime_request_hash body/plan": (body.get("runtime_request_hash"), plan.get("runtime_request_hash")),
            "runtime_request_hash index/body": (index.get("runtime_request_hash"), body.get("runtime_request_hash")),
            "runtime_request_hash calculated/body": (calculated_request_hash, body.get("runtime_request_hash")),
            "runtime_code_baseline_hash body/plan": (body.get("runtime_code_baseline_hash"), plan.get("runtime_code_baseline_hash")),
            "runtime_code_baseline_hash index/body": (index.get("runtime_code_baseline_hash"), body.get("runtime_code_baseline_hash")),
            "runtime_code_baseline_hash calculated/body": (calculated_code_baseline_hash, body.get("runtime_code_baseline_hash")),
            "approved_git_commit body/payload": (body.get("approved_git_commit"), canonical_payload.get("approved_git_commit")),
            "approved_git_commit index/body": (index.get("approved_git_commit"), body.get("approved_git_commit")),
            "user_gate_decision_ref index/body": (index.get("user_gate_decision_ref"), body.get("user_gate_decision_ref")),
            "approval_ref": (body.get("runtime_request", {}).get("approval_ref"), request["approval_ref"]),
            "target_path": (body.get("runtime_request", {}).get("target_path"), request["target_path"]),
            "executor_path body/policy": (body.get("executor_path"), trusted_executor["path"]),
            "executor_path index/body": (index.get("executor_path"), body.get("executor_path")),
            "executor_sha256": (body.get("executor_sha256"), trusted_executor["sha256"]),
            "executor_sha256 index/body": (index.get("executor_sha256"), body.get("executor_sha256")),
            "executor plan/policy": (
                plan.get("executor"),
                {"path": trusted_executor["path"], "sha256": trusted_executor["sha256"]},
            ),
            "validator_path body/policy": (
                body.get("validator_path"),
                [{"validator_id": trusted_validator["validator_id"], "path": trusted_validator["path"]}],
            ),
            "validator_path index/body": (index.get("validator_path"), body.get("validator_path")),
            "validator_sha256": (
                body.get("validator_sha256", [{}])[0].get("sha256"),
                trusted_validator["sha256"],
            ),
            "validator_sha256 index/body": (index.get("validator_sha256"), body.get("validator_sha256")),
            "executor_snapshot index/body": (index.get("executor_snapshot"), body.get("executor_snapshot")),
            "validator_snapshots index/body": (index.get("validator_snapshots"), body.get("validator_snapshots")),
            "target_sha256": (current.get("sha256"), request["preflight"].get("sha256")),
            "target_size": (current.get("size"), request["preflight"].get("size")),
        }
        for label, values in checks.items():
            if values[0] != values[1]:
                failures.append(f"{label} mismatch")
        if index.get("request_id") != request["request_id"]:
            failures.append("index request_id mismatch")
        if core_result.get("evidence", {}).get("evidence_id") != body.get("evidence_id"):
            failures.append("core result Evidence identity mismatch")
        expected_validators = [item.get("validator_id") for item in plan.get("required_validators", [])]
        actual_validators = [item.get("validator_id") for item in body.get("validations", [])]
        if actual_validators != expected_validators:
            failures.append("Validation identity mismatch")
        if body.get("validation_result") != core_result.get("validation"):
            failures.append("Validation status mismatch")
        if not isinstance(body.get("user_gate_decision_ref"), str) or not body["user_gate_decision_ref"].strip():
            failures.append("Final User Gate decision reference missing")
        failures.extend(_verify_snapshot_artifacts(evidence_dir, body))
    except (IndexError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        failures.append(str(exc))
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def _verify_run_artifacts(
    evidence_dir: Path,
    request: dict[str, Any],
    body: dict[str, Any],
    run_events: list[dict[str, Any]],
) -> list[str]:
    """Recompute Executor result, Checkpoint, and Validator output linkage."""
    failures: list[str] = []
    try:
        run_id = body["run_id"]
        result_path = (evidence_dir / "runs" / run_id / "executor_result.json").resolve()
        if not result_path.is_file():
            raise ValueError("executor_result.json is missing")
        result_sha = sha256_file(result_path)
        result = json.loads(result_path.read_text(encoding="utf-8"))
        checkpoints = [event for event in run_events if event.get("type") == "CHECKPOINT_RECORDED"]
        if len(checkpoints) != 1:
            failures.append("exactly one Checkpoint is required")
        else:
            checkpoint = checkpoints[0].get("payload", {})
            if Path(str(checkpoint.get("state_path"))).resolve() != result_path:
                failures.append("Checkpoint state_path mismatch")
            if checkpoint.get("state_sha256") != result_sha:
                failures.append("Checkpoint state_sha256 mismatch")
        expected_result = {
            "status": "COMPLETED",
            "request_id": request["request_id"],
            "run_id": run_id,
            "approval_ref": request["approval_ref"],
            "operation": request["operation"],
            "target_path": request["target_path"],
        }
        for key, expected in expected_result.items():
            if result.get(key) != expected:
                failures.append(f"executor_result {key} mismatch")
        current = _observe(Path(request["target_path"]))
        for label in ("observed_before", "observed_after"):
            if result.get(label) != current or result.get(label) != request.get("preflight"):
                failures.append(f"executor_result {label} mismatch")
        validation_events = [event for event in run_events if event.get("type") == "VALIDATION_RESULT"]
        validations = body.get("validations")
        if len(validation_events) != 1 or not isinstance(validations, list) or len(validations) != 1:
            failures.append("exactly one Validator record/output is required")
        else:
            record = validation_events[0].get("payload")
            if record != validations[0]:
                failures.append("Validator Event/Evidence record mismatch")
            if not isinstance(record, dict) or record.get("status") != "PASS":
                failures.append("Validator record is not PASS")
            else:
                output = json.loads(record.get("stdout", ""))
                if output.get("status") != "PASS" or output.get("request_id") != request["request_id"] or output.get("run_id") != run_id:
                    failures.append("Validator output identity mismatch")
                if output.get("target_observation") != current or output.get("failures") != []:
                    failures.append("Validator output observation mismatch")
        failures.extend(_verify_snapshot_artifacts(evidence_dir, body, run_events))
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        failures.append(str(exc))
    return failures


def _existing_pass(evidence_dir: Path, plan_path: Path, plan_bytes: bytes, request: dict[str, Any]) -> bool:
    try:
        if plan_path.read_bytes() != plan_bytes:
            return False
        plan = json.loads(plan_bytes)
        _, policy_errors = validate_runtime_plan_policy(plan, PROJECT_ROOT)
        if policy_errors:
            return False
        policy = load_runtime_policy(PROJECT_ROOT)
        _, calculated_request_hash = runtime_request_payload_and_hash(request, PROJECT_ROOT, policy)
        _, calculated_code_baseline_hash = runtime_code_baseline(PROJECT_ROOT)
        if plan.get("runtime_request_hash") != calculated_request_hash:
            return False
        if plan.get("runtime_code_baseline_hash") != calculated_code_baseline_hash:
            return False
        records = _read_json_lines(evidence_dir / "evidence_index.jsonl")
        candidates = [record for record in records if record.get("request_id") == request["request_id"] and record.get("gate") == "PROCEED"]
        if len(candidates) != 1:
            return False
        index = candidates[0]
        body_path = evidence_dir / index["filename"]
        body = json.loads(body_path.read_text(encoding="utf-8"))
        core_result = {
            "run_id": body.get("run_id"),
            "task_id": body.get("task_id"),
            "validation": body.get("validation_result"),
            "gate": body.get("gate"),
            "evidence": index,
        }
        chain = verify_runtime_evidence(
            evidence_dir=evidence_dir,
            task_plan_path=plan_path,
            request=request,
            core_result=core_result,
        )
        events = _read_json_lines(evidence_dir / "events.jsonl")
        run_id = body.get("run_id")
        run_events = [event for event in events if event.get("run_id") == run_id]
        gate_events = [event for event in run_events if event.get("type") == "GATE_DECISION"]
        validation_events = [event for event in run_events if event.get("type") == "VALIDATION_RESULT"]
        evidence_events = [event for event in run_events if event.get("type") == "EVIDENCE_RECORDED"]
        boundary_validations = [event for event in run_events if event.get("type") == "RUNTIME_BOUNDARY_VALIDATION"]
        boundary_decisions = [event for event in run_events if event.get("type") == "RUNTIME_BOUNDARY_DECISION"]
        invalidating = any(
            event.get("type") in {"BLOCKED", "EXECUTION_ERROR"}
            or (event.get("type") == "GATE_DECISION" and event.get("payload", {}).get("decision") != "PROCEED")
            or (event.get("type") == "RUNTIME_BOUNDARY_DECISION" and event.get("payload", {}).get("decision") != "PROCEED")
            for event in events
        )
        run_started = [event for event in run_events if event.get("type") == "RUN_STARTED"]
        run_artifact_failures = _verify_run_artifacts(evidence_dir, request, body, run_events)
        return all(
            (
                index.get("sha256") == sha256_file(body_path),
                body.get("validation_result") == "PASS",
                body.get("gate") == "PROCEED",
                body.get("task_plan_sha256") == sha256_file(plan_path),
                body.get("runtime_request") == request,
                chain.get("status") == "PASS",
                len(run_started) == 1 and run_started[0].get("payload", {}).get("task_plan_sha256") == sha256_file(plan_path),
                len(validation_events) == 1 and validation_events[0].get("payload", {}).get("status") == "PASS",
                len(gate_events) == 1 and gate_events[0].get("payload", {}).get("decision") == "PROCEED",
                len(evidence_events) == 1 and evidence_events[0].get("payload", {}).get("sha256") == index.get("sha256"),
                len(boundary_validations) == 1 and boundary_validations[0].get("payload", {}).get("evidence_chain", {}).get("status") == "PASS" and boundary_validations[0].get("payload", {}).get("target_unchanged") is True,
                len(boundary_decisions) == 1
                and boundary_decisions[0].get("payload", {}).get("decision") == "PROCEED"
                and boundary_decisions[0].get("payload", {}).get("runtime_request_hash") == calculated_request_hash
                and boundary_decisions[0].get("payload", {}).get("runtime_code_baseline_hash") == calculated_code_baseline_hash
                and boundary_decisions[0].get("payload", {}).get("user_gate_decision_ref") == body.get("user_gate_decision_ref"),
                not run_artifact_failures,
                not invalidating,
            )
        )
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def execute_approved_request(request: Any, user_gate_authorization: Any = None) -> dict[str, Any]:
    prepared = prepare_runtime_request(request)
    if prepared.get("status") != "READY_FOR_FINAL_USER_GATE":
        request_id = request.get("request_id") if isinstance(request, dict) else None
        if isinstance(request_id, str) and REQUEST_ID_PATTERN.fullmatch(request_id) and (EVIDENCE_ROOT.resolve() / request_id).exists():
            return _result("HOLD", "HOLD", "REQUEST_ID_COLLISION_OR_INCOMPLETE", evidence_dir=str(EVIDENCE_ROOT.resolve() / request_id))
        return prepared
    normalized = prepared["normalized_request"]
    runtime_request_hash = prepared["runtime_request_hash"]
    runtime_code_baseline_hash = prepared["runtime_code_baseline_hash"]
    evidence_dir = EVIDENCE_ROOT.resolve() / normalized["request_id"]
    plan_path = evidence_dir / "task_plan.json"
    try:
        plan = _build_plan(normalized, evidence_dir, runtime_request_hash, runtime_code_baseline_hash)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return _result("HOLD", "HOLD", "TRUSTED_PROGRAM_POLICY_MISMATCH", detail=str(exc))
    plan_bytes = (json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if evidence_dir.exists():
        if _existing_pass(evidence_dir, plan_path, plan_bytes, normalized):
            return _result("NO_CHANGE", "NO_CHANGE", "DUPLICATE_PASS", evidence_dir=str(evidence_dir))
        return _result("HOLD", "HOLD", "REQUEST_ID_COLLISION_OR_INCOMPLETE", evidence_dir=str(evidence_dir))

    user_gate_decision_ref, authorization_errors = inspect_user_gate_authorization(
        user_gate_authorization,
        project_root=PROJECT_ROOT,
        execution_context=normalized["execution_context"],
        runtime_request_hash=runtime_request_hash,
        runtime_code_baseline_hash=runtime_code_baseline_hash,
        approved_git_commit=prepared["approved_git_commit"],
    )
    if authorization_errors:
        return _result(
            "APPROVAL_REQUIRED",
            "APPROVAL_REQUIRED",
            "FINAL_USER_GATE_REQUIRED",
            runtime_request_hash=runtime_request_hash,
            runtime_code_baseline_hash=runtime_code_baseline_hash,
            canonical_payload=prepared["canonical_payload"],
            user_gate_display=prepared["user_gate_display"],
            authorization_errors=authorization_errors,
        )

    try:
        evidence_dir.mkdir(parents=True, exist_ok=False)
        with plan_path.open("xb") as handle:
            handle.write(plan_bytes)
    except FileExistsError:
        return _result("HOLD", "HOLD", "CONCURRENT_REQUEST_COLLISION", evidence_dir=str(evidence_dir))
    core_result = run_task(
        plan_path,
        PROJECT_ROOT,
        evidence_dir,
        user_gate_authorization=user_gate_authorization,
    )
    chain = verify_runtime_evidence(
        evidence_dir=evidence_dir,
        task_plan_path=plan_path,
        request=normalized,
        core_result=core_result,
    ) if core_result.get("evidence") else {"status": "FAIL", "failures": ["Runtime Evidence missing"]}
    observation_error: str | None = None
    try:
        target_after = _observe(Path(normalized["target_path"]))
        target_unchanged = target_after == normalized["preflight"]
    except OSError as exc:
        observation_error = str(exc)
        target_after = {"path": normalized["target_path"], "exists": False, "error": observation_error}
        target_unchanged = False
    proceed = core_result.get("status") == "PASS" and core_result.get("gate") == "PROCEED" and chain["status"] == "PASS" and target_unchanged
    final_status = "PASS" if proceed else "FAIL"
    decision = "PROCEED" if proceed else "BLOCK"
    store = EventStore(evidence_dir / "events.jsonl")
    store.append(
        "RUNTIME_BOUNDARY_VALIDATION",
        task_id=plan["task_id"],
        run_id=str(core_result.get("run_id", "RUN-NONE")),
        plan_version=plan["plan_version"],
        actor_role="RuntimeBoundary",
        payload={"evidence_chain": chain, "target_before": normalized["preflight"], "target_after": target_after, "target_unchanged": target_unchanged, "observation_error": observation_error},
    )
    store.append(
        "RUNTIME_BOUNDARY_DECISION",
        task_id=plan["task_id"],
        run_id=str(core_result.get("run_id", "RUN-NONE")),
        plan_version=plan["plan_version"],
        actor_role="RuntimeBoundary",
        payload={"decision": decision, "core_gate": core_result.get("gate"), "runtime_request_hash": runtime_request_hash, "runtime_code_baseline_hash": runtime_code_baseline_hash, "user_gate_decision_ref": user_gate_decision_ref},
    )
    return {
        "status": final_status,
        "decision": decision,
        "reason": "VALIDATED" if proceed else "VALIDATION_OR_EVIDENCE_FAILURE",
        "run_task_call_count": 1,
        "evidence_dir": str(evidence_dir),
        "task_plan": str(plan_path),
        "core_result": core_result,
        "evidence_chain": chain,
        "target_before": normalized["preflight"],
        "target_after": target_after,
        "runtime_request_hash": runtime_request_hash,
        "runtime_code_baseline_hash": runtime_code_baseline_hash,
        "user_gate_decision_ref": user_gate_decision_ref,
    }
