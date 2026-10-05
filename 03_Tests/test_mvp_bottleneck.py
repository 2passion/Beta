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
sys.path.insert(0, str(ROOT / "03_Tests" / "fixtures"))

from beta_core.cli import run_task  # noqa: E402
from beta_core.executor import run_executor  # noqa: E402
from beta_core.gate import decide_gate  # noqa: E402
from beta_core.validator_runner import run_validator  # noqa: E402
from bottleneck_scenario_executor import execute_decision_controlled_retry, task_plan  # noqa: E402


FIXTURES = ROOT / "03_Tests" / "fixtures"
PLAN = FIXTURES / "task_mvp_test_4_bottleneck.json"
EXECUTOR = FIXTURES / "bottleneck_scenario_executor.py"
VALIDATOR = FIXTURES / "bottleneck_validator.py"


def independent_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def criteria() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))["required_validators"][0]["criteria"]


def prepare_scenarios(temporary: str) -> tuple[dict, Path, dict]:
    result_path = Path(temporary) / "official" / "runs" / "PREP" / "executor_result.json"
    execution = run_executor(EXECUTOR, result_path, 20.0)
    if execution["status"] != "PASS":
        raise AssertionError(execution)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    return execution, result_path, result


def rewrite_events(path: Path, events: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for event in events),
        encoding="utf-8",
        newline="\n",
    )


def mutate_event(result: dict, scenario: str, event_type: str, mutation) -> None:
    event_path = Path(result["scenario_evidence_dirs"][scenario]) / "events.jsonl"
    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
    event = next(item for item in events if item["type"] == event_type)
    mutation(event)
    rewrite_events(event_path, events)


def assert_mutation_blocked(test: unittest.TestCase, execution: dict, result_path: Path) -> dict:
    validation = run_validator("VAL-MVP-TEST-4-BOTTLENECK", VALIDATOR, result_path, criteria(), 10.0)
    test.assertEqual(validation["status"], "FAIL")
    test.assertEqual(decide_gate(execution, [validation], evidence_recorded=True), "BLOCK")
    return json.loads(validation["stdout"])


class BottleneckHarnessTests(unittest.TestCase):
    def test_27_common_harness_bottleneck_a_to_e(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "mvp_test_4" / "official", executor_timeout_seconds=20.0)
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("PASS", "PASS", "PROCEED"))
            evidence = json.loads(Path(result["evidence"]["path"]).read_text(encoding="utf-8"))
            validation = json.loads(evidence["validations"][0]["stdout"])
            self.assertEqual((validation["mvp_test_id"], validation["mvp_test_name"], validation["test_plan_version"]), ("MVP-TEST-4", "Bottleneck", "1.2"))
            self.assertEqual(validation["validation_status"], "PASS")
            self.assertEqual(validation["fingerprints"]["A"], validation["fingerprints"]["B"])
            self.assertEqual(len({validation["fingerprints"][key] for key in ("A", "C", "D")}), 3)
            self.assertEqual(validation["retry_decisions"]["A"][0]["decision"], "BLOCK_BLIND_RETRY")
            self.assertEqual(validation["retry_decisions"]["B"][0]["decision"], "ALLOW_NEW_RUN")
            for link in validation["scenario_evidence"]:
                self.assertEqual(independent_sha256(Path(link["path"])), link["sha256"])

    def test_28_negative_a_run_id_in_fingerprint_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            def include_run_id(event: dict) -> None:
                event["payload"]["fingerprint_inputs"]["run_id"] = event["payload"]["source_run_id"]
                event["payload"]["fingerprint"] = independent_value_hash(event["payload"]["fingerprint_inputs"])
            mutate_event(result, "A", "FAILURE_FINGERPRINT", include_run_id)
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("Scenario A fingerprint includes volatile field", output["failures"])

    def test_29_negative_b_blind_retry_allowed_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            mutate_event(result, "A", "RETRY_DECISION", lambda event: event["payload"].update({"decision": "ALLOW_NEW_RUN"}))
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("Scenario A blind retry must BLOCK", output["failures"])

    def test_30_negative_c_reason_only_allow_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            mutate_event(
                result,
                "A",
                "RETRY_DECISION",
                lambda event: event["payload"].update({"decision": "ALLOW_NEW_RUN", "change_reason_ref": "reason-only"}),
            )
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("Scenario A blind retry must BLOCK", output["failures"])
            self.assertIn("Scenario A blind retry reason must be null", output["failures"])

    def test_31_negative_d_failure_class_collision_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            fingerprint_a = result["failure_fingerprints"]["A"]["fingerprint"]
            mutate_event(result, "D", "FAILURE_FINGERPRINT", lambda event: event["payload"].update({"fingerprint": fingerprint_a}))
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("Scenario D fingerprint mismatch", output["failures"])

    def test_32_retry_limits_are_fixture_only_and_block_excess(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "mvp_test_4" / "official", executor_timeout_seconds=20.0)
            evidence = json.loads(Path(result["evidence"]["path"]).read_text(encoding="utf-8"))
            validation = json.loads(evidence["validations"][0]["stdout"])
            records = validation["retry_limits"]
            self.assertEqual(len(records), 10)
            blocked = [item for item in records if item["decision"] == "BLOCK_LIMIT"]
            self.assertEqual({item["kind"] for item in blocked}, {"VALIDATOR_ERROR", "EXECUTION_ERROR", "PRODUCT_NEW_RUN"})
            self.assertEqual(len([item for item in records if item["decision"] == "ALLOW_NEW_RUN"]), 7)
            self.assertTrue(all(item["user_gate_workflow_started"] is False for item in records))

    def test_33_mutation_e_fake_count_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            directory = Path(result["retry_limit_directories"]["VALIDATOR_ERROR"])
            events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            block = next(event for event in events if event["type"] == "RETRY_LIMIT_DECISION" and event["payload"]["decision"] == "BLOCK_LIMIT")
            block["payload"].update({"attempts": 3, "observed_event_count": 3, "observed_run_started_count": 3, "observed_run_directory_count": 3})
            rewrite_events(directory / "events.jsonl", [block])
            shutil.rmtree(directory / "runs")
            for path in directory.glob("EVD-*.json"):
                path.unlink()
            (directory / "evidence_index.jsonl").unlink()
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("VALIDATOR_ERROR actual Event count must equal fixture limit", output["failures"])
            self.assertIn("VALIDATOR_ERROR self-reported Event count mismatch", output["failures"])

    def test_34_mutation_f_fake_blocked_run_directory_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            directory = Path(result["scenario_evidence_dirs"]["A"])
            events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            decision = next(event for event in events if event["type"] == "RETRY_DECISION")
            (directory / "runs" / decision["run_id"]).mkdir(parents=True)
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("Scenario A blocked retry Run directory must be absent", output["failures"])

    def test_35_mutation_g_missing_allowed_run_directory_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            directory = Path(result["scenario_evidence_dirs"]["A"])
            events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            source_run_id = next(event["run_id"] for event in events if event["type"] == "RUN_STARTED")
            shutil.rmtree(directory / "runs" / source_run_id)
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("Scenario A actual Run directory set mismatch", output["failures"])

    def test_36_mutation_h_block_then_run_task_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare_scenarios(temporary)
            directory = Path(result["scenario_evidence_dirs"]["A"])
            rerun = run_task(directory / "scenario_plan_1_0.json", ROOT, directory)
            self.assertEqual((rerun["validation"], rerun["gate"]), ("FAIL", "BLOCK"))
            output = assert_mutation_blocked(self, execution, result_path)
            self.assertIn("Scenario A blind retry must not create a second RUN_STARTED", output["failures"])

    def test_37_retry_limits_use_actual_events_runs_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "mvp_test_4" / "official", executor_timeout_seconds=20.0)
            evidence = json.loads(Path(result["evidence"]["path"]).read_text(encoding="utf-8"))
            validation = json.loads(evidence["validations"][0]["stdout"])
            counts = validation["retry_limit_counts"]
            self.assertEqual(counts["VALIDATOR_ERROR"], {
                "fixture_limit": 2, "actual_event_count": 2, "actual_run_started_count": 2,
                "actual_run_directory_count": 2, "actual_runtime_evidence_count": 2, "blocked_excess_run_count": 0,
            })
            self.assertEqual(counts["EXECUTION_ERROR"], {
                "fixture_limit": 2, "actual_event_count": 2, "actual_run_started_count": 2,
                "actual_run_directory_count": 2, "actual_runtime_evidence_count": 0, "blocked_excess_run_count": 0,
            })
            self.assertEqual(counts["PRODUCT_NEW_RUN"], {
                "fixture_limit": 3, "actual_event_count": 3, "actual_run_started_count": 3,
                "actual_run_directory_count": 3, "actual_runtime_evidence_count": 3, "blocked_excess_run_count": 0,
            })

    def test_38_mutation_i_reason_and_version_without_fix_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "mutation_i"
            baseline = task_plan("B", "1.0", FIXTURES / "executor_success.py", FIXTURES / "validator_fail.py", {"mode": "fail"}, "baseline")
            candidate = task_plan("B", "1.1", FIXTURES / "executor_success.py", FIXTURES / "validator_fail.py", {"mode": "fail"}, "reason-present")
            outcome = execute_decision_controlled_retry(directory, baseline, directory / "baseline.json", candidate, directory / "candidate.json", 3, "decision_evidence.json")
            self.assert_blocked_without_execution(outcome, directory)

    def test_39_mutation_j_fix_and_reason_without_version_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "mutation_j"
            baseline = task_plan("B", "1.0", FIXTURES / "executor_success.py", FIXTURES / "validator_fail.py", {"mode": "fail"}, "baseline")
            candidate = task_plan("B", "1.0", FIXTURES / "executor_success.py", FIXTURES / "validator_success.py", {"expected_value": "phase1-ok"}, "reason-present")
            outcome = execute_decision_controlled_retry(directory, baseline, directory / "baseline.json", candidate, directory / "candidate.json", 3, "decision_evidence.json")
            self.assert_blocked_without_execution(outcome, directory)

    def test_40_mutation_k_fix_and_version_without_reason_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "mutation_k"
            baseline = task_plan("B", "1.0", FIXTURES / "executor_success.py", FIXTURES / "validator_fail.py", {"mode": "fail"}, "baseline")
            candidate = task_plan("B", "1.1", FIXTURES / "executor_success.py", FIXTURES / "validator_success.py", {"expected_value": "phase1-ok"}, "")
            outcome = execute_decision_controlled_retry(directory, baseline, directory / "baseline.json", candidate, directory / "candidate.json", 3, "decision_evidence.json")
            self.assert_blocked_without_execution(outcome, directory)

    def assert_blocked_without_execution(self, outcome: dict, directory: Path) -> None:
        self.assertEqual(outcome["decision"]["decision"], "BLOCK_BLIND_RETRY")
        self.assertIsNone(outcome["candidate_result"])
        self.assertEqual(outcome["enforcement"], {
            "run_task_call_count": 0,
            "run_started_delta": 0,
            "run_directory_delta": 0,
            "runtime_evidence_delta": 0,
        })
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len([event for event in events if event["type"] == "RUN_STARTED"]), 1)
        self.assertEqual(len([path for path in (directory / "runs").iterdir() if path.is_dir()]), 1)
        self.assertEqual(len(list(directory.glob("EVD-*.json"))), 1)


def independent_value_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


if __name__ == "__main__":
    unittest.main()
