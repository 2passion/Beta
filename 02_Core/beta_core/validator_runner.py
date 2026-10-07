"""Run a required Validator in a process separate from the Executor."""

from __future__ import annotations

import json
import hashlib
import stat
import subprocess
import sys
from collections.abc import Collection
from pathlib import Path
from typing import Any


def run_validator(
    validator_id: str,
    script_path: Path,
    result_path: Path,
    criteria: Any,
    timeout_seconds: float,
    *,
    snapshot_sha256: str | None = None,
    snapshot_allowed_names: Collection[str] | None = None,
) -> dict[str, Any]:
    command = [sys.executable, str(script_path), str(result_path), json.dumps(criteria, ensure_ascii=False)]
    final_snapshot_sha256: str | None = None
    if snapshot_sha256 is not None:
        try:
            info = script_path.lstat()
            reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            if script_path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & reparse_flag) or not script_path.is_file():
                raise OSError("validator snapshot identity is unsafe")
            expected_names = set(snapshot_allowed_names or ())
            actual_names = {item.name for item in script_path.parent.iterdir()}
            if actual_names != expected_names or script_path.name not in expected_names:
                raise OSError("validator snapshot directory has unexpected sibling")
            verified_bytes = script_path.read_bytes()
            final_snapshot_sha256 = hashlib.sha256(verified_bytes).hexdigest().upper()
            if final_snapshot_sha256 != snapshot_sha256:
                raise OSError("validator snapshot final SHA-256 mismatch")
            verified_code = verified_bytes.decode("utf-8")
            command = [
                sys.executable,
                "-I",
                "-c",
                verified_code,
                str(result_path),
                json.dumps(criteria, ensure_ascii=False),
            ]
        except (OSError, UnicodeDecodeError) as exc:
            return {"validator_id": validator_id, "status": "ERROR", "exit_code": None, "stdout": "", "stderr": str(exc)}
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
        return {"validator_id": validator_id, "status": "ERROR", "exit_code": None, "stdout": "", "stderr": str(exc)}
    status = "PASS" if completed.returncode == 0 else "FAIL" if completed.returncode == 1 else "ERROR"
    result = {
        "validator_id": validator_id,
        "status": status,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if final_snapshot_sha256 is not None:
        result["snapshot_sha256"] = final_snapshot_sha256
        result["python_isolated_mode"] = True
    return result
