"""Deterministic fixture executor subprocess adapter."""

from __future__ import annotations

import json
import hashlib
import stat
import subprocess
import sys
from collections.abc import Collection
from pathlib import Path
from typing import Any


def run_executor(
    script_path: Path,
    output_path: Path,
    timeout_seconds: float,
    runtime_request: dict[str, Any] | None = None,
    *,
    snapshot_sha256: str | None = None,
    snapshot_allowed_names: Collection[str] | None = None,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(script_path), str(output_path)]
    final_snapshot_sha256: str | None = None
    if snapshot_sha256 is not None:
        try:
            info = script_path.lstat()
            reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            if script_path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & reparse_flag) or not script_path.is_file():
                raise OSError("executor snapshot identity is unsafe")
            expected_names = set(snapshot_allowed_names or ())
            actual_names = {item.name for item in script_path.parent.iterdir()}
            if actual_names != expected_names or script_path.name not in expected_names:
                raise OSError("executor snapshot directory has unexpected sibling")
            verified_bytes = script_path.read_bytes()
            final_snapshot_sha256 = hashlib.sha256(verified_bytes).hexdigest().upper()
            if final_snapshot_sha256 != snapshot_sha256:
                raise OSError("executor snapshot final SHA-256 mismatch")
            verified_code = verified_bytes.decode("utf-8")
            command = [sys.executable, "-I", "-c", verified_code, str(output_path)]
        except (OSError, UnicodeDecodeError) as exc:
            return {"status": "ERROR", "exit_code": None, "stdout": "", "stderr": str(exc)}
    if runtime_request is not None:
        command.append(json.dumps(runtime_request, ensure_ascii=False, sort_keys=True))
    try:
        completed = subprocess.run(
            command,
            cwd=str(script_path.parent),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "ERROR", "exit_code": None, "stdout": "", "stderr": str(exc)}
    result = {
        "status": "PASS" if completed.returncode == 0 else "ERROR",
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if final_snapshot_sha256 is not None:
        result["snapshot_sha256"] = final_snapshot_sha256
        result["python_isolated_mode"] = True
    return result
