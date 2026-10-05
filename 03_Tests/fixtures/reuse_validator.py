"""Independent MVP Test 1 Validator for exact Asset reuse decisions."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reuse_search import decide_reuse, load_assets


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_events(directory: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def event_time_ns(event: dict[str, Any]) -> int:
    value = event["time"]
    parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = parsed.astimezone(timezone.utc) - epoch
    return ((delta.days * 86400 + delta.seconds) * 1_000_000_000) + parsed.microsecond * 1000


def same_file(left: Path, right: Path) -> bool:
    return left.is_file() and right.is_file() and os.path.samefile(left, right)


def validate_create_order(
    label: str,
    search: dict[str, Any] | None,
    created_path: Path,
    start: dict[str, Any] | None,
    failures: list[str],
) -> dict[str, int] | None:
    if search is None or start is None or not created_path.is_file():
        return None
    search_ns = event_time_ns(search)
    created_ns = created_path.stat().st_ctime_ns
    run_ns = event_time_ns(start)
    require(search_ns < created_ns < run_ns, f"{label} CREATE order must be REUSE_SEARCH < file creation < RUN_STARTED", failures)
    return {"reuse_search_time_ns": search_ns, "created_file_time_ns": created_ns, "run_started_time_ns": run_ns}


def validate_runtime(directory: Path, failures: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any] | None, dict[str, Any] | None]:
    events = read_events(directory)
    searches = [event for event in events if event["type"] == "REUSE_SEARCH"]
    starts = [event for event in events if event["type"] == "RUN_STARTED"]
    require(len(searches) == 1, f"{directory.name} must have one REUSE_SEARCH", failures)
    require(len(starts) == 1, f"{directory.name} must have one RUN_STARTED", failures)
    search = searches[0] if len(searches) == 1 else None
    start = starts[0] if len(starts) == 1 else None
    if search and start:
        require(events.index(search) < events.index(start), f"{directory.name} REUSE_SEARCH must precede RUN_STARTED", failures)
    require(any(event["type"] == "RUN_COMPLETED" for event in events), f"{directory.name} RUN_COMPLETED missing", failures)
    require(any(event["type"] == "VALIDATION_RESULT" and event["payload"].get("status") == "PASS" for event in events), f"{directory.name} Validation PASS missing", failures)
    require(any(event["type"] == "EVIDENCE_RECORDED" for event in events), f"{directory.name} Evidence missing", failures)
    require(any(event["type"] == "GATE_DECISION" and event["payload"].get("decision") == "PROCEED" for event in events), f"{directory.name} Gate PROCEED missing", failures)
    return events, search, start


def require_payload(actual: dict[str, Any] | None, expected: dict[str, Any], label: str, failures: list[str]) -> None:
    if actual is None:
        return
    payload = actual.get("payload", {})
    for field in ("requested_capability", "matched_asset_ids", "selected_asset_id", "decision", "selected_path", "selected_sha256"):
        require(payload.get(field) == expected[field], f"{label} REUSE_SEARCH {field} mismatch", failures)
    require(isinstance(payload.get("reason"), str) and bool(payload["reason"].strip()), f"{label} REUSE_SEARCH reason missing", failures)


def main() -> int:
    result_path = Path(sys.argv[1]).resolve()
    criteria = json.loads(sys.argv[2])
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        project_root = Path(__file__).resolve().parents[2]
        allowed_root = (result_path.parents[3] / "scenarios").resolve()
        directories = {key: Path(value).resolve() for key, value in result["scenario_evidence_dirs"].items()}
        asset_list_path = (project_root / criteria["asset_list_path"]).resolve()
        reference_path = (project_root / criteria["reference_path"]).resolve()
        reuse_search_path = (project_root / criteria["reuse_search_path"]).resolve()
        assets = load_assets(asset_list_path)
        failures: list[str] = []

        require(result.get("mvp_test_id") == criteria.get("mvp_test_id"), "MVP Test ID mismatch", failures)
        require(result.get("mvp_test_name") == criteria.get("mvp_test_name"), "MVP Test name mismatch", failures)
        require(result.get("test_plan_id") == criteria.get("test_plan_id"), "Test Plan ID mismatch", failures)
        require(result.get("test_plan_version") == criteria.get("test_plan_version"), "Test Plan version mismatch", failures)
        require(sha256_file(asset_list_path) == criteria["asset_list_sha256"], "Asset list pinned hash mismatch", failures)
        require(sha256_file(reuse_search_path) == criteria["reuse_search_sha256"], "Reuse Search pinned hash mismatch", failures)
        require(result.get("asset_list_sha256_before") == criteria["asset_list_sha256"], "Asset list before hash mismatch", failures)
        require(result.get("asset_list_sha256_after") == criteria["asset_list_sha256"], "Asset list changed during scenarios", failures)
        require(sha256_file(reference_path) == criteria["reference_sha256"], "Reference pinned hash mismatch", failures)
        require(result.get("reference_sha256_before") == criteria["reference_sha256"], "Reference before hash mismatch", failures)
        require(result.get("reference_sha256_after") == criteria["reference_sha256"], "Reference changed during scenarios", failures)
        for key, directory in directories.items():
            require(directory.is_relative_to(allowed_root), f"Scenario {key} path is outside allowed root", failures)

        events_a, search_a, start_a = validate_runtime(directories["A"], failures)
        expected_a = decide_reuse(assets, "deterministic-success")
        require_payload(search_a, expected_a, "Scenario A", failures)
        approved_matches = [asset for asset in assets if asset["capability"] == "deterministic-success" and asset["status"] == "approved"]
        require(len(approved_matches) == 1, "Scenario A requires exactly one approved exact match", failures)
        require(expected_a["decision"] == "REUSE", "Scenario A must REUSE", failures)
        asset_a = approved_matches[0] if len(approved_matches) == 1 else None
        plan_a_path = directories["A"] / "scenario_task_plan.json"
        plan_a = json.loads(plan_a_path.read_text(encoding="utf-8"))
        asset_path = (project_root / asset_a["path"]).resolve() if asset_a else project_root
        selected_path = (project_root / search_a["payload"]["selected_path"]).resolve() if search_a and search_a["payload"].get("selected_path") else project_root
        plan_executor_path = (project_root / plan_a["executor"]["path"]).resolve()
        require(asset_a is not None and same_file(asset_path, selected_path), "Scenario A Asset path and REUSE_SEARCH path mismatch", failures)
        require(asset_a is not None and same_file(asset_path, plan_executor_path), "Scenario A Asset path and Plan Executor path mismatch", failures)
        actual_executor_sha = sha256_file(plan_executor_path) if plan_executor_path.is_file() else None
        if asset_a:
            require(asset_a["sha256"] == expected_a["selected_sha256"], "Scenario A Asset and REUSE_SEARCH SHA mismatch", failures)
            require(plan_a["executor"].get("sha256") == asset_a["sha256"], "Scenario A Plan Executor SHA mismatch", failures)
            require(actual_executor_sha == asset_a["sha256"], "Scenario A actual Executor SHA mismatch", failures)
        if start_a:
            require(start_a["payload"].get("task_plan_sha256") == sha256_file(plan_a_path), "Scenario A Plan SHA and RUN_STARTED mismatch", failures)
            require(start_a["payload"].get("executor_sha256") == actual_executor_sha, "Scenario A RUN_STARTED and actual Executor SHA mismatch", failures)
        require(not (directories["A"] / "synthetic_project").exists(), "Scenario A must not create a synthetic Asset", failures)

        events_b, search_b, start_b = validate_runtime(directories["B"], failures)
        expected_b = decide_reuse(assets, "missing-capability")
        require_payload(search_b, expected_b, "Scenario B", failures)
        require(expected_b["decision"] == "CREATE" and not expected_b["matched_asset_ids"], "Scenario B must CREATE after no match", failures)
        if search_b:
            require("no approved" in search_b["payload"].get("reason", "").lower(), "Scenario B CREATE reason invalid", failures)
        created_b = directories["B"] / "synthetic_project" / "03_Tests" / "fixtures" / "executor_created.py"
        require(created_b.is_file(), "Scenario B created executor missing", failures)
        if start_b and created_b.is_file():
            require(start_b["payload"].get("executor_sha256") == sha256_file(created_b), "Scenario B Executor hash mismatch", failures)
        create_order_b = validate_create_order("Scenario B", search_b, created_b, start_b, failures)

        events_c, search_c, start_c = validate_runtime(directories["C"], failures)
        expected_c = decide_reuse(assets, "visual-review")
        require_payload(search_c, expected_c, "Scenario C", failures)
        require(expected_c["decision"] == "CREATE", "Scenario C must not REUSE Reference", failures)
        require(expected_c["matched_asset_ids"] == ["REFERENCE-HARNESS-VISUAL"], "Scenario C Reference match missing", failures)
        if search_c:
            require("reference" in search_c["payload"].get("reason", "").lower(), "Scenario C CREATE reason invalid", failures)
        created_c = directories["C"] / "synthetic_project" / "03_Tests" / "fixtures" / "executor_created.py"
        require(created_c.is_file(), "Scenario C created executor missing", failures)
        if start_c and created_c.is_file():
            require(start_c["payload"].get("executor_sha256") == sha256_file(created_c), "Scenario C Executor hash mismatch", failures)
            require(start_c["payload"].get("executor_sha256") != criteria["reference_sha256"], "Scenario C executed Reference", failures)
        create_order_c = validate_create_order("Scenario C", search_c, created_c, start_c, failures)

        evidence_links = []
        for key, directory in directories.items():
            paths = sorted(directory.glob("EVD-*.json"))
            paths += [directory / name for name in ("events.jsonl", "evidence_index.jsonl", "scenario_task_plan.json") if (directory / name).is_file()]
            created = directory / "synthetic_project" / "03_Tests" / "fixtures" / "executor_created.py"
            if created.is_file():
                paths.append(created)
            for path in paths:
                evidence_links.append({"scenario": key, "path": str(path.resolve()), "sha256": sha256_file(path)})
        require(bool(evidence_links), "Scenario Evidence links missing", failures)
        output = {
            "mvp_test_id": criteria["mvp_test_id"],
            "mvp_test_name": criteria["mvp_test_name"],
            "test_plan_id": criteria["test_plan_id"],
            "test_plan_version": criteria["test_plan_version"],
            "validation_status": "PASS" if not failures else "FAIL",
            "scenario_root": str(allowed_root),
            "scenario_decisions": {
                "A": search_a["payload"] if search_a else None,
                "B": search_b["payload"] if search_b else None,
                "C": search_c["payload"] if search_c else None,
            },
            "scenario_internal_runs": {
                "A": [event["run_id"] for event in events_a if event["type"] == "RUN_STARTED"],
                "B": [event["run_id"] for event in events_b if event["type"] == "RUN_STARTED"],
                "C": [event["run_id"] for event in events_c if event["type"] == "RUN_STARTED"],
            },
            "asset_list_sha256": sha256_file(asset_list_path),
            "reuse_search_sha256": sha256_file(reuse_search_path),
            "selected_asset_id": expected_a["selected_asset_id"],
            "selected_asset_sha256": expected_a["selected_sha256"],
            "reuse_path_chain": {
                "asset_path": str(asset_path),
                "selected_path": str(selected_path),
                "plan_executor_path": str(plan_executor_path),
                "actual_executor_path": str(plan_executor_path),
                "actual_executor_sha256": actual_executor_sha,
                "task_plan_sha256": sha256_file(plan_a_path),
            },
            "create_order": {"B": create_order_b, "C": create_order_c},
            "reference_sha256": sha256_file(reference_path),
            "reference_executed": False,
            "scenario_evidence": evidence_links,
            "failures": failures,
        }
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
        return 0 if not failures else 1
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"validation_status": "ERROR", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
