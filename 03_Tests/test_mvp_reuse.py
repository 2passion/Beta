from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_Core"))

from beta_core.cli import run_task  # noqa: E402
from beta_core.executor import run_executor  # noqa: E402
from beta_core.gate import decide_gate  # noqa: E402
from beta_core.validator_runner import run_validator  # noqa: E402


FIXTURES = ROOT / "03_Tests" / "fixtures"
PLAN = FIXTURES / "task_mvp_test_1_reuse.json"
EXECUTOR = FIXTURES / "reuse_scenario_executor.py"
VALIDATOR = FIXTURES / "reuse_validator.py"


def independent_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def criteria(project: Path = ROOT) -> dict:
    plan = json.loads((project / "03_Tests" / "fixtures" / "task_mvp_test_1_reuse.json").read_text(encoding="utf-8"))
    return plan["required_validators"][0]["criteria"]


def isolated_project(parent: Path, name: str) -> Path:
    project = parent / name
    shutil.copytree(ROOT / "02_Core", project / "02_Core")
    shutil.copytree(ROOT / "03_Tests" / "fixtures", project / "03_Tests" / "fixtures")
    (project / "Reference").mkdir(parents=True)
    shutil.copyfile(ROOT / "Reference" / "harness-visual-review.html", project / "Reference" / "harness-visual-review.html")
    return project


def prepare_scenarios(temporary: str, project: Path = ROOT) -> tuple[dict, Path, dict]:
    result_path = Path(temporary) / "official" / "runs" / "PREP" / "executor_result.json"
    execution = run_executor(project / "03_Tests" / "fixtures" / "reuse_scenario_executor.py", result_path, 10.0)
    if execution["status"] != "PASS":
        raise AssertionError(execution)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    return execution, result_path, result


def rewrite_events(path: Path, events: list[dict]) -> None:
    path.write_text("".join(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for event in events), encoding="utf-8", newline="\n")


def assert_mutation_blocked(test: unittest.TestCase, execution: dict, result_path: Path, project: Path = ROOT) -> dict:
    validation = run_validator(
        "VAL-MVP-TEST-1-REUSE",
        project / "03_Tests" / "fixtures" / "reuse_validator.py",
        result_path,
        criteria(project),
        10.0,
    )
    test.assertEqual(validation["status"], "FAIL")
    test.assertEqual(decide_gate(execution, [validation], evidence_recorded=True), "BLOCK")
    return json.loads(validation["stdout"])


class ReuseHarnessTests(unittest.TestCase):
    def test_21_common_harness_reuse_a_b_c(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "mvp_test_1" / "official")
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("PASS", "PASS", "PROCEED"))
            evidence = json.loads(Path(result["evidence"]["path"]).read_text(encoding="utf-8"))
            validation = json.loads(evidence["validations"][0]["stdout"])
            self.assertEqual((validation["mvp_test_id"], validation["mvp_test_name"], validation["test_plan_version"]), ("MVP-TEST-1", "Reuse", "1.1"))
            self.assertEqual(validation["validation_status"], "PASS")
            self.assertEqual(validation["scenario_decisions"]["A"]["decision"], "REUSE")
            self.assertEqual(validation["scenario_decisions"]["B"]["decision"], "CREATE")
            self.assertEqual(validation["scenario_decisions"]["C"]["decision"], "CREATE")
            self.assertFalse(validation["reference_executed"])
            for link in validation["scenario_evidence"]:
                self.assertEqual(independent_sha256(Path(link["path"])), link["sha256"])

    def test_22_negative_approved_asset_create_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            event_path = Path(result["scenario_evidence_dirs"]["A"]) / "events.jsonl"
            events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
            search = next(event for event in events if event["type"] == "REUSE_SEARCH")
            search["payload"].update({"decision": "CREATE", "selected_asset_id": None, "selected_path": None, "selected_sha256": None, "reason": "forced create"})
            rewrite_events(event_path, events)
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("Scenario A REUSE_SEARCH decision mismatch", output["failures"])

    def test_23_negative_reference_reuse_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            event_path = Path(result["scenario_evidence_dirs"]["C"]) / "events.jsonl"
            events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
            search = next(event for event in events if event["type"] == "REUSE_SEARCH")
            search["payload"].update({
                "decision": "REUSE",
                "selected_asset_id": "REFERENCE-HARNESS-VISUAL",
                "selected_path": "Reference/harness-visual-review.html",
                "selected_sha256": "17490AA44F8FEAE35B55F1CF811D18AA1A6EB0716ABAB398B1A016B3600E14C0",
                "reason": "forced reference reuse",
            })
            rewrite_events(event_path, events)
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("Scenario C REUSE_SEARCH decision mismatch", output["failures"])

    def test_24_negative_late_reuse_search_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            event_path = Path(result["scenario_evidence_dirs"]["A"]) / "events.jsonl"
            events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
            search = next(event for event in events if event["type"] == "REUSE_SEARCH")
            events.remove(search)
            start_index = next(index for index, event in enumerate(events) if event["type"] == "RUN_STARTED")
            events.insert(start_index + 1, search)
            rewrite_events(event_path, events)
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("a_approved_reuse REUSE_SEARCH must precede RUN_STARTED", output["failures"])

    def test_25_mutation_d_same_hash_different_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = isolated_project(Path(temporary), "mutation_d")
            fixtures = project / "03_Tests" / "fixtures"
            shutil.copyfile(fixtures / "executor_success.py", fixtures / "executor_success_copy.py")
            executor = fixtures / "reuse_scenario_executor.py"
            source = executor.read_text(encoding="utf-8")
            old = '        executor_path = PROJECT_ROOT / decision["selected_path"]\n'
            new = '        executor_path = THIS_FILE.parent / "executor_success_copy.py"\n'
            self.assertIn(old, source)
            executor.write_text(source.replace(old, new, 1), encoding="utf-8", newline="\n")
            execution, result_path, _ = prepare_scenarios(str(Path(temporary) / "runtime_d"), project)
            output = assert_mutation_blocked(self, execution, result_path, project)
            self.assertIn("Scenario A Asset path and Plan Executor path mismatch", output["failures"])

    def test_26_mutation_e_create_before_search_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = isolated_project(Path(temporary), "mutation_e")
            executor = project / "03_Tests" / "fixtures" / "reuse_scenario_executor.py"
            source = executor.read_text(encoding="utf-8")
            needle = '    EventStore(directory / "events.jsonl").append(\n'
            injection = '''    if scenario in {"B", "C"}:
        early_path = directory / "synthetic_project" / "03_Tests" / "fixtures" / "executor_created.py"
        early_path.parent.mkdir(parents=True, exist_ok=True)
        early_path.write_text(CREATED_EXECUTOR, encoding="utf-8", newline="\\n")
    EventStore(directory / "events.jsonl").append(
'''
            self.assertIn(needle, source)
            executor.write_text(source.replace(needle, injection, 1), encoding="utf-8", newline="\n")
            execution, result_path, _ = prepare_scenarios(str(Path(temporary) / "runtime_e"), project)
            output = assert_mutation_blocked(self, execution, result_path, project)
            self.assertTrue(any("CREATE order must be REUSE_SEARCH < file creation < RUN_STARTED" in failure for failure in output["failures"]))


if __name__ == "__main__":
    unittest.main()
