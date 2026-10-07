"""Git-anchored, fail-closed policy for READ_ONLY_INTEGRITY runtime admission."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
from pathlib import Path
from typing import Any

from .model import sha256_file


POLICY_RELATIVE_PATH = "02_Core/beta_core/runtime_policy.json"
APPROVAL_RELATIVE_ROOT = Path("04_Evidence/runtime/approvals")
APPROVAL_FIELDS = {
    "approval_ref", "approved_git_commit", "target_path", "approved_root", "operation",
    "policy_path", "policy_sha256", "executor_path", "executor_sha256",
    "validator_path", "validator_sha256", "parallel_allowed", "dependencies", "approved_at",
}
RUNTIME_REQUEST_FIELDS = {
    "request_id", "approval_ref", "operation", "target_path", "approved_root", "task_count",
    "parallel_allowed", "dependencies", "expected_target_side_effect", "network",
    "external_publish", "execution_context", "preflight",
}
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
APPROVAL_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL", "CLOCK$", "CONIN$", "CONOUT$",
    *(f"COM{number}" for number in range(1, 10)), *(f"LPT{number}" for number in range(1, 10)),
}
REQUIRED_RUNTIME_CODE_FILES = {"__init__.py", "model.py", "event_store.py"}
RUNTIME_CODE_BASELINE_PATHS = tuple(
    f"02_Core/beta_core/{path.name}"
    for path in sorted(Path(__file__).resolve().parent.glob("*.py"), key=lambda item: item.name)
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def canonical_local_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("canonical path requires a non-empty string")
    path = Path(value)
    if not path.is_absolute():
        raise ValueError("canonical path must be absolute")
    return path.resolve().as_posix().casefold()


def _policy_path(project_root: Path) -> Path:
    return (project_root.resolve() / POLICY_RELATIVE_PATH).resolve()


def runtime_code_baseline(project_root: Path) -> tuple[list[dict[str, str]], str]:
    """Hash every production Core Python module for the Final User Gate."""
    root = project_root.resolve()
    core_root = (root / "02_Core" / "beta_core").resolve()
    if not core_root.is_relative_to(root) or not core_root.is_dir():
        raise ValueError("runtime code baseline directory is unavailable")
    paths = sorted(core_root.glob("*.py"), key=lambda item: item.name)
    names = {path.name for path in paths}
    if not REQUIRED_RUNTIME_CODE_FILES.issubset(names):
        raise ValueError("runtime code baseline required module is unavailable")
    manifest: list[dict[str, str]] = []
    for raw_path in paths:
        info = raw_path.lstat()
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        if raw_path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & reparse_flag):
            raise ValueError(f"runtime code baseline path identity is unsafe: {raw_path.name}")
        path = raw_path.resolve()
        if not path.is_relative_to(core_root) or not path.is_file():
            raise ValueError(f"runtime code baseline file is unavailable: {raw_path.name}")
        manifest.append({
            "relative_path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
        })
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return manifest, _sha256_bytes(canonical)


def prepare_runtime_program_snapshot(
    plan: dict[str, Any],
    project_root: Path,
    *,
    program_key: str,
    expected_sha256: str,
    evidence_dir: Path,
    run_id: str,
) -> tuple[Path | None, dict[str, Any] | None, list[str]]:
    """Revalidate the approved source and execute only the verified run-local bytes."""
    try:
        _, current_code_baseline_hash = runtime_code_baseline(project_root)
    except (OSError, TypeError, ValueError) as exc:
        return None, None, [str(exc)]
    if plan.get("runtime_code_baseline_hash") != current_code_baseline_hash:
        return None, None, ["runtime_code_baseline_hash final revalidation mismatch"]
    resolved, errors = validate_runtime_plan_policy(plan, project_root)
    if errors:
        return None, None, errors
    source = resolved.get(program_key)
    if source is None:
        return None, None, [f"runtime program is not approved: {program_key}"]
    try:
        evidence_root = evidence_dir.resolve()
        run_dir = (evidence_root / "runs" / run_id).resolve()
        if not run_dir.is_relative_to(evidence_root) or run_dir.parent != (evidence_root / "runs").resolve():
            return None, None, [f"{program_key} run-local snapshot path is unsafe"]
        snapshot_dir = run_dir / "execution_snapshot"
        if program_key == "executor":
            if snapshot_dir.exists():
                return None, None, ["executor snapshot directory already exists"]
            snapshot_dir.mkdir(parents=True, exist_ok=False)
            expected_before: set[str] = set()
            snapshot_name = "executor.py"
        else:
            if not snapshot_dir.is_dir():
                return None, None, ["validator snapshot directory is unavailable"]
            expected_before = {"executor.py"}
            validator_id = program_key.removeprefix("validator:")
            if REQUEST_ID_PATTERN.fullmatch(validator_id) is None:
                return None, None, ["validator snapshot identity is unsafe"]
            snapshot_name = f"validator-{validator_id}.py"
        before_names = {item.name for item in snapshot_dir.iterdir()}
        if before_names != expected_before:
            return None, None, [f"{program_key} snapshot directory has unexpected sibling"]
        source_bytes = source.read_bytes()
        source_sha = _sha256_bytes(source_bytes)
        if source_sha != expected_sha256:
            return None, None, [f"{program_key} final SHA-256 mismatch"]
        snapshot = (snapshot_dir / snapshot_name).resolve()
        if snapshot.parent != snapshot_dir.resolve():
            return None, None, [f"{program_key} snapshot path is unsafe"]
        with snapshot.open("xb") as handle:
            handle.write(source_bytes)
        if sha256_file(snapshot) != expected_sha256:
            return None, None, [f"{program_key} execution snapshot SHA-256 mismatch"]
        after_names = {item.name for item in snapshot_dir.iterdir()}
        if after_names != expected_before | {snapshot_name}:
            return None, None, [f"{program_key} snapshot directory changed unexpectedly"]
        contract = {
            "role": program_key,
            "relative_path": snapshot.relative_to(evidence_root).as_posix(),
            "sha256": expected_sha256,
            "lifecycle": "PRESERVED_FOR_NO_CHANGE",
            "python_isolated_mode": True,
        }
        return snapshot, contract, []
    except OSError as exc:
        return None, None, [f"{program_key} execution snapshot failed: {exc}"]


def load_runtime_policy(project_root: Path) -> dict[str, Any]:
    value = json.loads(_policy_path(project_root).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"policy_version", "production", "test_fixture", "executor", "validator"}:
        raise ValueError("trusted runtime policy schema mismatch")
    production = value.get("production")
    if not isinstance(production, dict) or set(production) != {"approved_root", "target_path", "operation"}:
        raise ValueError("production policy schema mismatch")
    return value


def _safe_program(project_root: Path, label: str, spec: Any) -> Path:
    if not isinstance(spec, dict) or not {"path", "sha256"}.issubset(spec) or not isinstance(spec.get("path"), str) or not isinstance(spec.get("sha256"), str):
        raise ValueError(f"trusted {label} policy invalid")
    raw_path = project_root.resolve() / spec["path"]
    info = raw_path.lstat()
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if raw_path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & reparse_flag):
        raise ValueError(f"trusted {label} path identity is unsafe")
    path = raw_path.resolve()
    if not path.is_relative_to(project_root.resolve()) or not path.is_file() or sha256_file(path) != spec["sha256"]:
        raise ValueError(f"trusted {label} current SHA-256 mismatch")
    return path


def trusted_programs(project_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    policy = load_runtime_policy(project_root)
    _safe_program(project_root, "executor", policy["executor"])
    _safe_program(project_root, "validator", policy["validator"])
    return policy, policy["executor"], policy["validator"]


def _git(project_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(project_root.resolve()), *args], capture_output=True, check=False, shell=False
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.decode("utf-8", errors="replace").strip() or "Git trust-anchor command failed")
    return completed.stdout


def _verify_blob(project_root: Path, commit: str, relative_path: str, approved_sha: str) -> list[str]:
    errors: list[str] = []
    try:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("approval packet path must be repository-relative")
        current_path = (project_root / relative).resolve()
        if not current_path.is_relative_to(project_root.resolve()) or not current_path.is_file():
            raise ValueError("approved runtime file is unavailable")
        blob = _git(project_root, "show", f"{commit}:{relative.as_posix()}")
        current = current_path.read_bytes()
        if _sha256_bytes(blob) != approved_sha or _sha256_bytes(current) != approved_sha or current != blob:
            errors.append(f"approved Git blob/current file mismatch: {relative.as_posix()}")
    except (OSError, TypeError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def load_approval_packet(project_root: Path, approval_ref: Any) -> dict[str, Any]:
    if not isinstance(approval_ref, str) or APPROVAL_REF_PATTERN.fullmatch(approval_ref) is None or approval_ref.upper() in WINDOWS_RESERVED:
        raise ValueError("production approval_ref is invalid")
    root = project_root.resolve()
    path = (root / APPROVAL_RELATIVE_ROOT / f"{approval_ref}.json").resolve()
    if path.parent != (root / APPROVAL_RELATIVE_ROOT).resolve():
        raise ValueError("approval packet path is not fixed")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != APPROVAL_FIELDS:
        raise ValueError("approval packet schema mismatch")
    return value


def verify_production_trust_anchor(
    request: dict[str, Any], project_root: Path, policy: dict[str, Any]
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        packet = load_approval_packet(project_root, request.get("approval_ref"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return None, [f"production approval NOT ISSUED: {exc}"]
    commit = packet.get("approved_git_commit")
    if not isinstance(commit, str) or COMMIT_PATTERN.fullmatch(commit) is None:
        errors.append("approved_git_commit must be a full commit SHA")
    else:
        try:
            repo_root = Path(_git(project_root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
            if repo_root != project_root.resolve():
                errors.append("Git repository root mismatch")
            _git(project_root, "cat-file", "-e", f"{commit}^{{commit}}")
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    production = policy["production"]
    expected_values = {
        "approval_ref": request.get("approval_ref"), "target_path": request.get("target_path"),
        "approved_root": request.get("approved_root"), "operation": request.get("operation"),
        "policy_path": POLICY_RELATIVE_PATH, "executor_path": policy["executor"]["path"],
        "executor_sha256": policy["executor"]["sha256"], "validator_path": policy["validator"]["path"],
        "validator_sha256": policy["validator"]["sha256"], "parallel_allowed": False, "dependencies": [],
    }
    for key, expected in expected_values.items():
        if key in {"target_path", "approved_root"}:
            try:
                matches = canonical_local_path(packet.get(key)) == canonical_local_path(expected)
            except (OSError, TypeError, ValueError):
                matches = False
        else:
            matches = packet.get(key) == expected
        if not matches:
            errors.append(f"approval packet {key} mismatch")
    try:
        production_paths_match = (
            canonical_local_path(request.get("target_path")) == canonical_local_path(production.get("target_path"))
            and canonical_local_path(request.get("approved_root")) == canonical_local_path(production.get("approved_root"))
        )
    except (OSError, TypeError, ValueError):
        production_paths_match = False
    if not production_paths_match or request.get("operation") != production.get("operation"):
        errors.append("request does not match production policy")
    policy_sha = sha256_file(_policy_path(project_root))
    if packet.get("policy_sha256") != policy_sha:
        errors.append("approval packet policy_sha256 mismatch")
    if isinstance(commit, str) and COMMIT_PATTERN.fullmatch(commit):
        for relative_path, approved_sha in (
            (POLICY_RELATIVE_PATH, packet.get("policy_sha256")),
            (policy["executor"]["path"], packet.get("executor_sha256")),
            (policy["validator"]["path"], packet.get("validator_sha256")),
        ):
            if not isinstance(approved_sha, str):
                errors.append(f"approval SHA missing: {relative_path}")
            else:
                errors.extend(_verify_blob(project_root, commit, relative_path, approved_sha))
    return packet, errors


def runtime_request_payload_and_hash(
    request: dict[str, Any], project_root: Path, policy: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    """Create the canonical payload shown to the execution-time User Gate."""
    context = request.get("execution_context")
    if context == "PRODUCTION":
        packet, errors = verify_production_trust_anchor(request, project_root, policy)
        if errors or packet is None:
            raise ValueError("Production Git/packet trust anchor is not valid")
        approved_git_commit = packet["approved_git_commit"]
        policy_sha = packet["policy_sha256"]
    elif context == "TEST_FIXTURE":
        approved_git_commit = "TEST_FIXTURE_ONLY"
        policy_sha = sha256_file(_policy_path(project_root))
    else:
        raise ValueError("execution context cannot produce a runtime request hash")
    payload = {
        "request_id": request["request_id"],
        "target_path": canonical_local_path(request["target_path"]),
        "approved_root": canonical_local_path(request["approved_root"]),
        "operation": request["operation"],
        "target_side_effect": request["expected_target_side_effect"],
        "parallel": request["parallel_allowed"],
        "dependencies": request["dependencies"],
        "approved_git_commit": approved_git_commit,
        "policy_path": POLICY_RELATIVE_PATH,
        "policy_sha256": policy_sha,
        "executor_path": policy["executor"]["path"],
        "executor_sha256": policy["executor"]["sha256"],
        "validator_path": policy["validator"]["path"],
        "validator_sha256": policy["validator"]["sha256"],
        "network": request["network"],
        "external_publish": request["external_publish"],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return payload, _sha256_bytes(canonical)


def validate_runtime_plan_policy(
    plan: dict[str, Any], project_root: Path
) -> tuple[dict[str, Path], list[str]]:
    """Enforce runtime and Git/User-Gate policy again inside Core."""
    errors: list[str] = []
    request = plan.get("runtime_request")
    if not isinstance(request, dict):
        return {}, ["production runtime_request is required"]
    if set(request) != RUNTIME_REQUEST_FIELDS:
        errors.append("runtime_request fields do not exactly match trusted contract")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or REQUEST_ID_PATTERN.fullmatch(request_id) is None or request_id.upper() in WINDOWS_RESERVED:
        errors.append("runtime request_id is invalid or reserved")
    if request.get("operation") != "READ_ONLY_INTEGRITY":
        errors.append("runtime operation is not approved")
    for key in ("parallel_allowed", "network", "external_publish"):
        if type(request.get(key)) is not bool or request.get(key) is not False:
            errors.append(f"runtime {key} must be exact bool False")
    if type(request.get("task_count")) is not int or request.get("task_count") != 1:
        errors.append("runtime task_count must be exact int 1")
    if type(request.get("dependencies")) is not list or request.get("dependencies") != []:
        errors.append("runtime dependencies must be an empty list")
    if request.get("expected_target_side_effect") != "NONE":
        errors.append("runtime target side effect must be NONE")
    try:
        policy, executor, validator = trusted_programs(project_root)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {}, [str(exc), *errors]
    context = request.get("execution_context")
    try:
        raw_root = Path(request["approved_root"])
        raw_target = Path(request["target_path"])
        if not raw_root.is_absolute() or not raw_target.is_absolute():
            errors.append("runtime target/root must be absolute")
        approved_root = raw_root.resolve()
        target = raw_target.resolve()
        info = raw_target.lstat()
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        if raw_target.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & reparse_flag):
            errors.append("runtime target identity is unsafe")
        if not target.is_file():
            errors.append("runtime target is not a normal file")
    except (KeyError, OSError, TypeError, ValueError):
        errors.append("runtime target/root identity is invalid")
        approved_root = project_root / "INVALID"
        target = approved_root / "INVALID"
    if context == "PRODUCTION":
        _, anchor_errors = verify_production_trust_anchor(request, project_root, policy)
        errors.extend(anchor_errors)
        production = policy["production"]
        if approved_root != Path(production["approved_root"]).resolve() or target != Path(production["target_path"]).resolve():
            errors.append("production scope/target mismatch")
    elif context == "TEST_FIXTURE":
        fixture = policy["test_fixture"]
        fixture_root = (project_root / fixture["approved_root"]).resolve()
        if request.get("approval_ref") != fixture.get("approval_ref"):
            errors.append("test fixture approval_ref mismatch")
        if not approved_root.is_relative_to(fixture_root) or not target.is_relative_to(approved_root):
            errors.append("test fixture scope is outside isolated fixture root")
    else:
        errors.append("execution_context is not approved")
    preflight = request.get("preflight")
    try:
        if not isinstance(preflight, dict) or not target.is_file():
            raise OSError("target unavailable")
        current = {"path": str(target), "exists": True, "size": target.stat().st_size, "sha256": sha256_file(target)}
        if preflight != current:
            errors.append("runtime preflight does not match current target")
    except OSError:
        errors.append("runtime preflight is invalid")
    permissions = plan.get("permissions")
    if not isinstance(permissions, dict) or permissions.get("network") is not False or permissions.get("external_publish") is not False or type(permissions.get("target_write_count")) is not int or permissions.get("target_write_count") != 0:
        errors.append("runtime permissions do not match read-only policy")
    plan_executor = plan.get("executor")
    validators = plan.get("required_validators")
    if not isinstance(plan_executor, dict) or plan_executor.get("path") != executor["path"] or plan_executor.get("sha256") != executor["sha256"]:
        errors.append("executor identity does not match trusted policy")
    if not isinstance(validators, list) or len(validators) != 1 or not isinstance(validators[0], dict):
        errors.append("exactly one trusted validator is required")
    else:
        item = validators[0]
        if item.get("validator_id") != validator.get("validator_id") or item.get("path") != validator["path"] or item.get("sha256") != validator["sha256"]:
            errors.append("validator identity does not match trusted policy")
    resolved = {
        "executor": (project_root / executor["path"]).resolve(),
        f"validator:{validator.get('validator_id')}": (project_root / validator["path"]).resolve(),
    }
    return resolved, errors
