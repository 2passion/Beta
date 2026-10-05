"""Execute MVP Test 1 scenarios through the existing Common MVP Test Harness."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
CORE_ROOT = PROJECT_ROOT / "02_Core"
if not (CORE_ROOT / "beta_core").is_dir():
    raise RuntimeError(f"unable to locate 02_Core/beta_core from executor file: {THIS_FILE}")
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from beta_core.cli import run_task
from beta_core.event_store import EventStore
from beta_core.model import new_id, sha256_file, utc_now
from reuse_search import decide_reuse, load_assets


CREATED_EXECUTOR = '''"""Synthetic executor created only inside an isolated MVP Test scenario."""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("x", encoding="utf-8", newline="\\n") as handle:
    json.dump({"status": "completed", "value": "phase1-ok"}, handle, sort_keys=True)
    handle.write("\\n")
'''


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")


def task_plan(
    scenario: str,
    project_root: Path,
    executor_path: Path,
    validator_path: Path,
) -> dict[str, Any]:
    return {
        "task_id": f"TASK-MVP1-{scenario}",
        "plan_version": "1.0",
        "order_id": "Order-021",
        "change_reason_ref": f"Order-021 / Reuse Scenario {scenario}",
        "write_owner": "Codex",
        "write_scope": ["04_Evidence/mvp_test_1/scenarios"],
        "shared_resources": [],
        "depends_on": [],
        "steps": [{"step_id": f"REUSE-{scenario}-STEP-001", "action": "execute selected or synthetic capability"}],
        "executor": {
            "path": executor_path.resolve().relative_to(project_root.resolve()).as_posix(),
            "sha256": sha256_file(executor_path),
        },
        "required_validators": [{
            "validator_id": f"VAL-MVP1-{scenario}",
            "path": validator_path.resolve().relative_to(project_root.resolve()).as_posix(),
            "sha256": sha256_file(validator_path),
            "criteria": {"expected_value": "phase1-ok"},
        }],
        "completion_criteria": ["selected capability executes", "required validator passes"],
        "permissions": {"subprocess": "approved fixture paths only", "network": False, "reference_write": False},
    }


def execute_scenario(
    scenario: str,
    capability: str,
    directory: Path,
    assets: list[dict[str, Any]],
) -> dict[str, Any]:
    decision = decide_reuse(assets, capability)
    EventStore(directory / "events.jsonl").append(
        "REUSE_SEARCH",
        task_id=f"TASK-MVP1-{scenario}",
        run_id=new_id("SEARCH"),
        plan_version="1.0",
        actor_role="ReuseSearch",
        payload=decision,
    )

    if decision["decision"] == "REUSE":
        scenario_project_root = PROJECT_ROOT
        executor_path = PROJECT_ROOT / decision["selected_path"]
        validator_path = THIS_FILE.parent / "validator_success.py"
        created_executor_path = None
    else:
        scenario_project_root = directory / "synthetic_project"
        fixture_root = scenario_project_root / "03_Tests" / "fixtures"
        fixture_root.mkdir(parents=True, exist_ok=True)
        executor_path = fixture_root / "executor_created.py"
        executor_path.write_text(CREATED_EXECUTOR, encoding="utf-8", newline="\n")
        validator_path = fixture_root / "validator_success.py"
        shutil.copyfile(THIS_FILE.parent / "validator_success.py", validator_path)
        created_executor_path = executor_path.resolve()

    plan_path = directory / "scenario_task_plan.json"
    write_json(plan_path, task_plan(scenario, scenario_project_root, executor_path, validator_path))
    result = run_task(plan_path, scenario_project_root, directory)
    return {
        "decision": decision,
        "created_executor_path": str(created_executor_path) if created_executor_path else None,
        "result": result,
    }


def main() -> int:
    output_path = Path(sys.argv[1]).resolve()
    outer_evidence_dir = output_path.parents[2]
    scenario_root = outer_evidence_dir.parent / "scenarios" / new_id("SCN")
    directories = {
        "A": scenario_root / "a_approved_reuse",
        "B": scenario_root / "b_no_match_create",
        "C": scenario_root / "c_reference_only_create",
    }
    asset_list_path = THIS_FILE.parent / "reuse_assets.json"
    reference_path = PROJECT_ROOT / "Reference" / "harness-visual-review.html"
    assets = load_assets(asset_list_path)
    asset_hash_before = sha256_file(asset_list_path)
    reference_hash_before = sha256_file(reference_path)
    results = {
        "A": execute_scenario("A", "deterministic-success", directories["A"], assets),
        "B": execute_scenario("B", "missing-capability", directories["B"], assets),
        "C": execute_scenario("C", "visual-review", directories["C"], assets),
    }
    output = {
        "mvp_test_id": "MVP-TEST-1",
        "mvp_test_name": "Reuse",
        "test_plan_id": "MVP-TEST-1-REUSE",
        "test_plan_version": "1.1",
        "created_at": utc_now(),
        "scenario_root": str(scenario_root.resolve()),
        "scenario_evidence_dirs": {key: str(value.resolve()) for key, value in directories.items()},
        "asset_list_path": str(asset_list_path.resolve()),
        "asset_list_sha256_before": asset_hash_before,
        "asset_list_sha256_after": sha256_file(asset_list_path),
        "reference_path": str(reference_path.resolve()),
        "reference_sha256_before": reference_hash_before,
        "reference_sha256_after": sha256_file(reference_path),
        "scenario_runs": results,
    }
    write_json(output_path, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
