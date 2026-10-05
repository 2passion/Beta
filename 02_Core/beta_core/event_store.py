"""Append-only JSONL storage used by Phase 1 events and indexes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .model import new_id, utc_now


REQUIRED_EVENT_FIELDS = {
    "event_id",
    "type",
    "task_id",
    "run_id",
    "plan_version",
    "actor_role",
    "time",
    "payload",
}


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


class EventStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(
        self,
        event_type: str,
        *,
        task_id: str,
        run_id: str,
        plan_version: str,
        actor_role: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event = {
            "event_id": new_id("EVT"),
            "type": event_type,
            "task_id": task_id,
            "run_id": run_id,
            "plan_version": plan_version,
            "actor_role": actor_role,
            "time": utc_now(),
            "payload": payload,
        }
        if set(event) != REQUIRED_EVENT_FIELDS:
            raise ValueError("event fields do not match the Phase 1 contract")
        append_jsonl(self.path, event)
        return event

    def first_plan_hash(self, task_id: str, plan_version: str) -> str | None:
        """Return the first post-Order-012 Plan hash bound to task/version."""
        if not self.path.exists():
            return None
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid Event JSONL at line {line_number}") from exc
                if event.get("type") != "RUN_STARTED":
                    continue
                if event.get("task_id") != task_id or event.get("plan_version") != plan_version:
                    continue
                payload = event.get("payload")
                if isinstance(payload, dict) and isinstance(payload.get("task_plan_sha256"), str):
                    return payload["task_plan_sha256"]
        return None
