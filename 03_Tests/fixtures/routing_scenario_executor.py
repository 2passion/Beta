"""Minimal Order-level execution routing contract fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def evaluate_routing(expected_to: str, actual_executor: str, action: str, order_id: str, project: str) -> dict:
    matched = expected_to == actual_executor
    return {
        "expected_to": expected_to,
        "actual_executor": actual_executor,
        "action": action,
        "order_id": order_id,
        "project": project,
        "routing_result": "MATCH" if matched else "HOLD",
        "mismatch_reason": None if matched else "ROUTING_MISMATCH",
        "write_allowed": matched and action == "WRITE",
        "writer_call_count": 1 if matched and action == "WRITE" else 0,
        "beta_write_count": 1 if matched and action == "WRITE" else 0,
        "next_step_count": 1 if matched and action == "WRITE" else 0,
    }


def main() -> int:
    output_path = Path(sys.argv[1])
    output = {
        "match": evaluate_routing("Codex", "Codex", "WRITE", "Order-035", "Beta"),
        "mismatch_fixture": evaluate_routing("Claude Code", "Codex", "WRITE", "Order-035", "Beta"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(output, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
