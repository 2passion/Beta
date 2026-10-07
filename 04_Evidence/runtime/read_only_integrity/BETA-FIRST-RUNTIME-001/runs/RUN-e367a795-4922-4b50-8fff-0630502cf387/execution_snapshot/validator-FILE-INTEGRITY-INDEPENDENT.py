"""Independent validator for one READ_ONLY_INTEGRITY execution result."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _observe(path: Path) -> dict[str, Any]:
    stat_result = path.stat()
    return {
        "path": str(path.resolve()),
        "exists": path.is_file(),
        "size": stat_result.st_size,
        "sha256": _sha256(path),
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        return 2
    try:
        result = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        criteria = json.loads(args[1])
        if not isinstance(result, dict) or not isinstance(criteria, dict):
            raise ValueError("invalid validator input")
        target = Path(criteria["target_path"])
        current = _observe(target)
        expected = criteria["preflight"]
        failures: list[str] = []
        exact = {
            "status": "COMPLETED",
            "request_id": criteria["request_id"],
            "run_id": criteria["run_id"],
            "approval_ref": criteria["approval_ref"],
            "operation": "READ_ONLY_INTEGRITY",
            "target_path": str(target.resolve()),
        }
        for key, value in exact.items():
            if result.get(key) != value:
                failures.append(f"executor result {key} mismatch")
        for label in ("observed_before", "observed_after"):
            observation = result.get(label)
            if not isinstance(observation, dict):
                failures.append(f"executor result {label} missing")
                continue
            for key in ("path", "exists", "size", "sha256"):
                if observation.get(key) != current.get(key):
                    failures.append(f"{label}.{key} mismatch")
        for key in ("path", "exists", "size", "sha256"):
            if expected.get(key) != current.get(key):
                failures.append(f"preflight.{key} mismatch")
        report = {
            "status": "PASS" if not failures else "FAIL",
            "request_id": criteria["request_id"],
            "run_id": criteria["run_id"],
            "target_observation": current,
            "failures": failures,
        }
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0 if not failures else 1
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
