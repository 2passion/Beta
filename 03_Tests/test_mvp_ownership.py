from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_Core"))

from beta_core.cli import run_task  # noqa: E402


PLAN = ROOT / "03_Tests" / "fixtures" / "task_mvp_test_2_ownership.json"
TEMP_PARENT = ROOT / "03_Tests" / ".tmp"


def independent_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


@contextmanager
def without_pythonpath():
    previous = os.environ.pop("PYTHONPATH", None)
    try:
        yield
    finally:
        if previous is not None:
            os.environ["PYTHONPATH"] = previous


def isolated_project(parent: Path, name: str) -> Path:
    project = parent / name
    shutil.copytree(ROOT / "02_Core", project / "02_Core")
    shutil.copytree(ROOT / "03_Tests" / "fixtures", project / "03_Tests" / "fixtures")
    return project


def run_isolated(project: Path, evidence_name: str) -> dict:
    with without_pythonpath():
        return run_task(
            project / "03_Tests" / "fixtures" / "task_mvp_test_2_ownership.json",
            project,
            project / "04_Evidence" / evidence_name / "official",
        )


class OwnershipHarnessTests(unittest.TestCase):
    def test_18_common_harness_ownership_a_b_c(self) -> None:
        TEMP_PARENT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEMP_PARENT) as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "official")
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("PASS", "PASS", "PROCEED"))
            evidence = json.loads(Path(result["evidence"]["path"]).read_text(encoding="utf-8"))
            validation = json.loads(evidence["validations"][0]["stdout"])
            self.assertEqual(validation["mvp_test_id"], "MVP-TEST-2")
            self.assertEqual(validation["mvp_test_name"], "Ownership")
            self.assertEqual(validation["test_plan_version"], "1.1")
            self.assertEqual(validation["validation_status"], "PASS")
            self.assertTrue(validation["scenario_internal_runs"]["A"])
            self.assertTrue(validation["scenario_internal_runs"]["B_BLOCKED"])
            self.assertTrue(validation["scenario_internal_runs"]["C_BASE"])
            self.assertTrue(validation["scenario_internal_runs"]["C_SAME_VERSION_BLOCKED"])
            self.assertTrue(validation["scenario_internal_runs"]["C_NEW_VERSION"])
            for link in validation["scenario_evidence"]:
                self.assertEqual(independent_sha256(Path(link["path"])), link["sha256"])
        try:
            TEMP_PARENT.rmdir()
        except OSError:
            pass

    def test_19_mutation_b_non_owner_block_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = isolated_project(Path(temporary), "b19")
            fixture = project / "03_Tests" / "fixtures" / "ownership_b_multiple_owner.json"
            plan = json.loads(fixture.read_text(encoding="utf-8"))
            plan["write_owner"] = "Codex"
            del plan["steps"]
            fixture.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = run_isolated(project, "mutation_b")
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("FAIL", "FAIL", "BLOCK"))
            evidence = json.loads(Path(result["evidence"]["path"]).read_text(encoding="utf-8"))
            validation = json.loads(evidence["validations"][0]["stdout"])
            self.assertIn("Scenario B BLOCK reason must be the single-owner contract", validation["failures"])

    def test_20_mutation_c_wrong_block_reason_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = isolated_project(Path(temporary), "c19")
            fixture = project / "03_Tests" / "fixtures" / "ownership_c_v1_changed_owner.json"
            plan = json.loads(fixture.read_text(encoding="utf-8"))
            plan["write_owner"] = "Claude Code"
            fixture.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = run_isolated(project, "mutation_c")
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("FAIL", "FAIL", "BLOCK"))
            evidence = json.loads(Path(result["evidence"]["path"]).read_text(encoding="utf-8"))
            validation = json.loads(evidence["validations"][0]["stdout"])
            self.assertIn("Scenario C BLOCK reason must be the same-version Task Plan hash contract", validation["failures"])


if __name__ == "__main__":
    unittest.main()
