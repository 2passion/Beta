"""Deterministic fixture executor subprocess adapter."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


def run_executor(script_path: Path, output_path: Path, timeout_seconds: float) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(
            [sys.executable, str(script_path), str(output_path)],
            cwd=str(script_path.parent),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "ERROR", "exit_code": None, "stdout": "", "stderr": str(exc)}
    return {
        "status": "PASS" if completed.returncode == 0 else "ERROR",
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
