"""Run a required Validator in a process separate from the Executor."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_validator(
    validator_id: str,
    script_path: Path,
    result_path: Path,
    criteria: Any,
    timeout_seconds: float,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [sys.executable, str(script_path), str(result_path), json.dumps(criteria, ensure_ascii=False)],
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
    return {
        "validator_id": validator_id,
        "status": status,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
