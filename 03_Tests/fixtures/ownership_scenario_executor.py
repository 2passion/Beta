"""Execute isolated Ownership scenarios using the existing Phase 1 Core."""

from __future__ import annotations

import json
import sys
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
CORE_ROOT = PROJECT_ROOT / "02_Core"
if not (CORE_ROOT / "beta_core").is_dir():
    raise RuntimeError(f"unable to locate 02_Core/beta_core from executor file: {THIS_FILE}")
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from beta_core.cli import run_task
from beta_core.model import new_id, utc_now


def main() -> int:
    output_path = Path(sys.argv[1]).resolve()
    project_root = PROJECT_ROOT
    fixture_root = THIS_FILE.parent
    outer_evidence_dir = output_path.parents[2]
    scenario_root = outer_evidence_dir.parent / "scenarios" / new_id("SCN")
    scenario_dirs = {
        "A": scenario_root / "a_single_owner",
        "B": scenario_root / "b_multiple_owner",
        "C": scenario_root / "c_owner_change",
    }
    results = {
        "A": run_task(fixture_root / "ownership_a_single_owner.json", project_root, scenario_dirs["A"]),
        "B": run_task(fixture_root / "ownership_b_multiple_owner.json", project_root, scenario_dirs["B"]),
    }
    results["C_BASE"] = run_task(fixture_root / "ownership_c_v1_codex.json", project_root, scenario_dirs["C"])
    results["C_SAME_VERSION"] = run_task(fixture_root / "ownership_c_v1_changed_owner.json", project_root, scenario_dirs["C"])
    results["C_NEW_VERSION"] = run_task(fixture_root / "ownership_c_v2_claude.json", project_root, scenario_dirs["C"])

    output = {
        "mvp_test_id": "MVP-TEST-2",
        "mvp_test_name": "Ownership",
        "test_plan_id": "MVP-TEST-2-OWNERSHIP",
        "test_plan_version": "1.1",
        "created_at": utc_now(),
        "scenario_root": str(scenario_root.resolve()),
        "scenario_evidence_dirs": {key: str(value.resolve()) for key, value in scenario_dirs.items()},
        "scenario_runs": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(output, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
