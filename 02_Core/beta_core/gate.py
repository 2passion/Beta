"""Phase 1 Gate decision as a logical responsibility."""

from __future__ import annotations

from typing import Any


def decide_gate(execution: dict[str, Any], validations: list[dict[str, Any]], evidence_recorded: bool) -> str:
    if execution.get("status") != "PASS":
        return "BLOCK"
    if not validations or any(item.get("status") != "PASS" for item in validations):
        return "BLOCK"
    if not evidence_recorded:
        return "BLOCK"
    return "PROCEED"
