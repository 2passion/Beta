"""Task-plan model and Phase 1 contract validation."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Collection
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_PLAN_FIELDS = {
    "task_id",
    "plan_version",
    "order_id",
    "write_owner",
    "write_scope",
    "shared_resources",
    "depends_on",
    "steps",
    "executor",
    "required_validators",
    "completion_criteria",
    "permissions",
    "change_reason_ref",
}

OWNER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_task_plan(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)
    if not isinstance(plan, dict):
        raise ValueError("Task Plan must be a JSON object")
    return plan


def validate_contract(plan: dict[str, Any]) -> list[str]:
    errors = [f"missing field: {name}" for name in sorted(REQUIRED_PLAN_FIELDS - plan.keys())]
    owner = plan.get("write_owner")
    if not isinstance(owner, str) or OWNER_PATTERN.fullmatch(owner) is None:
        errors.append("write_owner must be one identifier matching ^[A-Za-z0-9][A-Za-z0-9_-]*$")
    change_reason_ref = plan.get("change_reason_ref")
    if not isinstance(change_reason_ref, str) or not change_reason_ref.strip():
        errors.append("change_reason_ref must be a non-empty string")
    validators = plan.get("required_validators")
    if not isinstance(validators, list) or not validators:
        errors.append("required_validators must contain at least one validator")
    for field in ("write_scope", "shared_resources", "depends_on", "steps", "completion_criteria"):
        if field in plan and not isinstance(plan[field], list):
            errors.append(f"{field} must be a list")
    if not isinstance(plan.get("executor"), dict):
        errors.append("executor must be an object")
    if not isinstance(plan.get("permissions"), dict):
        errors.append("permissions must be an object")
    return errors


def resolve_fixture_path(project_root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("fixture path must be a non-empty string")
    fixture_root = (project_root / "03_Tests" / "fixtures").resolve()
    candidate = (project_root / relative_path).resolve()
    if not candidate.is_relative_to(fixture_root):
        raise ValueError(f"subprocess path is outside approved fixtures: {relative_path}")
    if not candidate.is_file():
        raise ValueError(f"fixture does not exist: {relative_path}")
    return candidate


def resolve_approved_program_path(
    project_root: Path,
    relative_path: str,
    approved_program_paths: Collection[Path],
) -> Path:
    """Resolve one program against an exact, caller-approved path allowlist."""
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("program path must be a non-empty string")
    candidate = (project_root / relative_path).resolve()
    approved = {Path(path).resolve() for path in approved_program_paths}
    if candidate not in approved:
        raise ValueError(f"program path is outside the exact approved allowlist: {relative_path}")
    if not candidate.is_file():
        raise ValueError(f"approved program does not exist: {relative_path}")
    return candidate


def validate_pinned_programs(
    plan: dict[str, Any],
    project_root: Path,
    approved_program_paths: Collection[Path] | None = None,
) -> tuple[dict[str, Path], list[str]]:
    resolved: dict[str, Path] = {}
    errors: list[str] = []
    programs: list[tuple[str, Any]] = [("executor", plan.get("executor"))]
    validators = plan.get("required_validators")
    if isinstance(validators, list):
        programs.extend((f"validator:{item.get('validator_id', index)}", item) for index, item in enumerate(validators) if isinstance(item, dict))
    for label, spec in programs:
        if not isinstance(spec, dict):
            errors.append(f"{label} specification is invalid")
            continue
        try:
            if approved_program_paths is None:
                path = resolve_fixture_path(project_root, spec.get("path"))
            else:
                path = resolve_approved_program_path(project_root, spec.get("path"), approved_program_paths)
        except (TypeError, ValueError) as exc:
            errors.append(str(exc))
            continue
        expected = spec.get("sha256")
        actual = sha256_file(path)
        if not isinstance(expected, str) or expected.upper() != actual:
            errors.append(f"{label} SHA-256 mismatch")
            continue
        resolved[label] = path
    return resolved, errors
