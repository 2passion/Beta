"""Deterministic exact-match Asset lookup for MVP Test 1 fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {"asset_id", "capability", "path", "sha256", "status"}
ALLOWED_STATUS = {"approved", "reference"}


def load_assets(path: Path) -> list[dict[str, Any]]:
    assets = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(assets, list):
        raise ValueError("Asset fixture must be a JSON list")
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict) or set(asset) != REQUIRED_FIELDS:
            raise ValueError(f"Asset fixture entry {index} has invalid fields")
        if asset["status"] not in ALLOWED_STATUS:
            raise ValueError(f"Asset fixture entry {index} has invalid status")
        if not all(isinstance(asset[field], str) and asset[field] for field in REQUIRED_FIELDS):
            raise ValueError(f"Asset fixture entry {index} has invalid values")
    return assets


def decide_reuse(assets: list[dict[str, Any]], capability: str) -> dict[str, Any]:
    matches = sorted(
        (asset for asset in assets if asset["capability"] == capability),
        key=lambda asset: asset["asset_id"],
    )
    approved = [asset for asset in matches if asset["status"] == "approved"]
    if approved:
        selected = approved[0]
        return {
            "requested_capability": capability,
            "matched_asset_ids": [asset["asset_id"] for asset in matches],
            "selected_asset_id": selected["asset_id"],
            "decision": "REUSE",
            "reason": "approved exact-match Asset selected",
            "selected_path": selected["path"],
            "selected_sha256": selected["sha256"],
        }
    reason = (
        "matching entries are Reference-only; Reference cannot be executed"
        if matches
        else "no approved Asset matches requested capability"
    )
    return {
        "requested_capability": capability,
        "matched_asset_ids": [asset["asset_id"] for asset in matches],
        "selected_asset_id": None,
        "decision": "CREATE",
        "reason": reason,
        "selected_path": None,
        "selected_sha256": None,
    }
