"""Narrow read-only file integrity executor for the production runtime boundary."""

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
    output_path = Path(args[0])
    try:
        request = json.loads(args[1])
        if not isinstance(request, dict) or request.get("operation") != "READ_ONLY_INTEGRITY":
            raise ValueError("invalid runtime request")
        target = Path(request["target_path"])
        before = _observe(target)
        after = _observe(target)
        result = {
            "status": "COMPLETED",
            "request_id": request["request_id"],
            "run_id": request["run_id"],
            "approval_ref": request["approval_ref"],
            "operation": request["operation"],
            "target_path": str(target.resolve()),
            "observed_before": before,
            "observed_after": after,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
