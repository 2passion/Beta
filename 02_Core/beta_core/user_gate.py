"""Ephemeral, one-shot Final User Gate capability for runtime admission."""

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any


LOCAL_BETA_ROOT = Path(__file__).resolve().parents[2]
_ISSUER = object()


class EphemeralUserGateAuthorization:
    """An in-memory capability; it is never serialized into policy or packets."""

    __slots__ = (
        "_request_hash",
        "_runtime_code_baseline_hash",
        "_approved_git_commit",
        "_decision_ref",
        "_project_root",
        "_scope",
        "_consumed",
        "_lock",
    )

    def __init__(
        self,
        issuer: object,
        request_hash: str,
        runtime_code_baseline_hash: str,
        approved_git_commit: str,
        decision_ref: str,
        project_root: Path,
        scope: str,
    ) -> None:
        if issuer is not _ISSUER:
            raise TypeError("authorization must come from an external User Gate")
        self._request_hash = request_hash
        self._runtime_code_baseline_hash = runtime_code_baseline_hash
        self._approved_git_commit = approved_git_commit
        self._decision_ref = decision_ref
        self._project_root = project_root.resolve()
        self._scope = scope
        self._consumed = False
        self._lock = Lock()

    def __copy__(self) -> Any:
        raise TypeError("ephemeral authorization cannot be copied")

    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        raise TypeError("ephemeral authorization cannot be copied")

    def __reduce__(self) -> Any:
        raise TypeError("ephemeral authorization cannot be serialized")

    def __reduce_ex__(self, protocol: int) -> Any:
        raise TypeError("ephemeral authorization cannot be serialized")

    def __getstate__(self) -> Any:
        raise TypeError("ephemeral authorization state cannot be exported")

    def __setstate__(self, state: Any) -> None:
        raise TypeError("ephemeral authorization state cannot be restored")


def issue_fixture_user_gate_authorization(
    *,
    project_root: Path,
    runtime_request_hash: str,
    runtime_code_baseline_hash: str,
    approved_git_commit: str,
    decision_ref: str,
    production_simulation: bool = False,
) -> EphemeralUserGateAuthorization:
    """Test-only external gate used by isolated regression fixtures."""
    root = project_root.resolve()
    if not isinstance(runtime_request_hash, str) or len(runtime_request_hash) != 64:
        raise ValueError("fixture authorization requires an exact request hash")
    if not isinstance(runtime_code_baseline_hash, str) or len(runtime_code_baseline_hash) != 64:
        raise ValueError("fixture authorization requires an exact runtime code baseline hash")
    if not isinstance(approved_git_commit, str) or not approved_git_commit:
        raise ValueError("fixture authorization requires an approved Git commit identity")
    if not isinstance(decision_ref, str) or not decision_ref.startswith("FIXTURE-USER-GATE-"):
        raise ValueError("fixture authorization decision reference is invalid")
    if production_simulation:
        if root == LOCAL_BETA_ROOT.resolve():
            raise ValueError("fixture authorization cannot authorize Beta Production")
        scope = "ISOLATED_PRODUCTION_TEST"
    else:
        scope = "TEST_FIXTURE"
    return EphemeralUserGateAuthorization(
        _ISSUER,
        runtime_request_hash,
        runtime_code_baseline_hash,
        approved_git_commit,
        decision_ref,
        root,
        scope,
    )


def _inspect_locked(
    authorization: EphemeralUserGateAuthorization,
    *,
    project_root: Path,
    execution_context: str,
    runtime_request_hash: str,
    runtime_code_baseline_hash: str,
    approved_git_commit: str,
) -> tuple[str | None, list[str]]:
    expected_scope = "TEST_FIXTURE" if execution_context == "TEST_FIXTURE" else "ISOLATED_PRODUCTION_TEST"
    if authorization._scope != expected_scope:
        return None, ["Final User Gate authorization scope mismatch"]
    if authorization._project_root != project_root.resolve():
        return None, ["Final User Gate authorization project root mismatch"]
    if authorization._request_hash != runtime_request_hash:
        return None, ["Final User Gate authorization request hash mismatch"]
    if authorization._runtime_code_baseline_hash != runtime_code_baseline_hash:
        return None, ["Final User Gate authorization runtime code baseline mismatch"]
    if authorization._approved_git_commit != approved_git_commit:
        return None, ["Final User Gate authorization approved Git commit mismatch"]
    if authorization._consumed:
        return None, ["Final User Gate authorization already consumed"]
    return authorization._decision_ref, []


def inspect_user_gate_authorization(
    authorization: Any,
    *,
    project_root: Path,
    execution_context: str,
    runtime_request_hash: str,
    runtime_code_baseline_hash: str,
    approved_git_commit: str,
) -> tuple[str | None, list[str]]:
    if type(authorization) is not EphemeralUserGateAuthorization:
        return None, ["execution-time Final User Gate authorization is required"]
    with authorization._lock:
        return _inspect_locked(
            authorization,
            project_root=project_root,
            execution_context=execution_context,
            runtime_request_hash=runtime_request_hash,
            runtime_code_baseline_hash=runtime_code_baseline_hash,
            approved_git_commit=approved_git_commit,
        )


def claim_user_gate_authorization(
    authorization: Any,
    *,
    project_root: Path,
    execution_context: str,
    runtime_request_hash: str,
    runtime_code_baseline_hash: str,
    approved_git_commit: str,
) -> tuple[str | None, list[str]]:
    if type(authorization) is not EphemeralUserGateAuthorization:
        return None, ["execution-time Final User Gate authorization is required"]
    with authorization._lock:
        decision_ref, errors = _inspect_locked(
            authorization,
            project_root=project_root,
            execution_context=execution_context,
            runtime_request_hash=runtime_request_hash,
            runtime_code_baseline_hash=runtime_code_baseline_hash,
            approved_git_commit=approved_git_commit,
        )
        if errors:
            return None, errors
        authorization._consumed = True
        return decision_ref, []
