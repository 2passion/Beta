from __future__ import annotations

import json
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
from prevention_scenario_executor import execute_target, make_record, source_chain  # noqa: E402


FIXTURES = ROOT / "03_Tests" / "fixtures"
PLAN = FIXTURES / "task_mvp_test_5_prevention.json"
EXECUTOR = FIXTURES / "prevention_scenario_executor.py"
VALIDATOR = FIXTURES / "prevention_validator.py"


def criteria() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))["required_validators"][0]["criteria"]


def prepare(temporary: str) -> tuple[dict, Path, dict]:
    result_path = Path(temporary) / "mvp_test_5" / "official" / "runs" / "PREP" / "executor_result.json"
    execution = run_executor(EXECUTOR, result_path, 20.0)
    if execution["status"] != "PASS":
        raise AssertionError(execution)
    return execution, result_path, json.loads(result_path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def rewrite_events(path: Path, events: list[dict]) -> None:
    path.write_text("".join(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for event in events), encoding="utf-8", newline="\n")


def assert_blocked(test: unittest.TestCase, execution: dict, result_path: Path) -> dict:
    validation = run_validator("VAL-MVP-TEST-5-PREVENTION", VALIDATOR, result_path, criteria(), 10.0)
    test.assertEqual(validation["status"], "FAIL")
    test.assertEqual(decide_gate(execution, [validation], evidence_recorded=True), "BLOCK")
    return json.loads(validation["stdout"])


class PreventionHarnessTests(unittest.TestCase):
    def test_41_common_harness_prevention_a_to_d(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "mvp_test_5" / "official", executor_timeout_seconds=20.0)
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("PASS", "PASS", "PROCEED"))
            evidence = json.loads(Path(result["evidence"]["path"]).read_text(encoding="utf-8"))
            validation = json.loads(evidence["validations"][0]["stdout"])
            self.assertEqual((validation["mvp_test_id"], validation["mvp_test_name"], validation["test_plan_version"]), ("MVP-TEST-5", "Prevention", "1.1"))
            self.assertEqual(validation["validation_status"], "PASS")

    def test_42_negative_a_missing_pass_evidence_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            record_path = Path(result["scenario_evidence_dirs"]["A"]) / "prevention_record.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["source_evidence_ids"] = record["source_evidence_ids"][:1]
            write_json(record_path, record)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A source Evidence IDs mismatch", output["failures"])

    def test_43_negative_b_forced_other_fingerprint_match_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            event_path = Path(result["scenario_evidence_dirs"]["B"]) / "events.jsonl"
            events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
            search = next(event for event in events if event["type"] == "PREVENTION_SEARCH")
            search["payload"]["requested_fingerprint"] = "F" * 64
            rewrite_events(event_path, events)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario B requested fingerprint mismatch", output["failures"])

    def test_44_negative_c_hypothesis_root_cause_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            record_path = Path(result["scenario_evidence_dirs"]["A"]) / "prevention_record.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["root_cause_status"] = "HYPOTHESIS"
            write_json(record_path, record)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A Root Cause must be confirmed", output["failures"])

    def test_45_negative_d_applied_fix_signature_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            plan_path = Path(result["scenario_evidence_dirs"]["B"]) / "target_plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["prevention_application"]["fix_signature"] = "0" * 64
            write_json(plan_path, plan)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario B applied fix signature mismatch", output["failures"])

    def test_46_negative_e_active_rule_promotion_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            record_path = Path(result["scenario_evidence_dirs"]["A"]) / "prevention_record.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["active_rule"] = {"status": "ACTIVE"}
            write_json(record_path, record)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Prevention must not be promoted to active_rule", output["failures"])

    def test_47_mutation_f_declared_signature_with_failed_actual_plan_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            plan_path = Path(result["scenario_evidence_dirs"]["B"]) / "target_plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            failed_validator = FIXTURES / "validator_fail.py"
            plan["required_validators"][0].update({
                "path": failed_validator.relative_to(ROOT).as_posix(),
                "sha256": independent_sha256(failed_validator),
                "criteria": {"mode": "fail"},
            })
            write_json(plan_path, plan)
            refresh_link_hash(result, plan_path)
            write_json(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario B actual Source/Record/Target fix signature mismatch", output["failures"])

    def test_48_mutation_g_fake_source_is_not_eligible_and_never_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            chain = source_chain()
            record = make_record(chain)
            record.update({
                "source_pass_run_id": "RUN-00000000-0000-0000-0000-000000000000",
                "source_evidence_ids": [record["source_evidence_ids"][0], "EVD-00000000-0000-0000-0000-000000000000"],
                "fix_signature": "F" * 64,
            })
            outcome = execute_target(Path(temporary) / "mutation_g", record, record["failure_fingerprint"], chain)
            self.assertEqual(outcome["search"]["outcome"], "NOT_ELIGIBLE")
            self.assertFalse(outcome["search"]["eligible"])
            self.assert_zero_execution(outcome)

    def test_49_mutation_h_no_match_never_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            chain = source_chain()
            record = make_record(chain)
            outcome = execute_target(Path(temporary) / "mutation_h", record, "F" * 64, chain)
            self.assertEqual(outcome["search"]["outcome"], "NO_MATCH")
            self.assert_zero_execution(outcome)

    def test_50_mutation_i_missing_root_cause_evidence_never_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            chain = source_chain()
            record = make_record(chain)
            record["root_cause_evidence_refs"] = []
            outcome = execute_target(Path(temporary) / "mutation_i", record, record["failure_fingerprint"], chain)
            self.assertEqual(outcome["search"]["outcome"], "NOT_ELIGIBLE")
            self.assertIn("root cause evidence references incomplete", outcome["search"]["eligibility_reasons"])
            self.assert_zero_execution(outcome)

    def test_51_target_plan_sha_matches_run_started(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _, _, result = prepare(temporary)
            directory = Path(result["scenario_evidence_dirs"]["B"])
            plan_path = directory / "target_plan.json"
            events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            started = next(event for event in events if event["type"] == "RUN_STARTED")
            apply_evidence = json.loads((directory / "prevention_apply_evidence.json").read_text(encoding="utf-8"))
            plan_hash = independent_sha256(plan_path)
            self.assertEqual(started["payload"]["task_plan_sha256"], plan_hash)
            self.assertEqual(apply_evidence["target_plan_sha256"], plan_hash)

    def assert_zero_execution(self, outcome: dict) -> None:
        self.assertIsNone(outcome["result"])
        self.assertEqual(outcome["enforcement"], {
            "run_task_call_count": 0, "run_started_delta": 0,
            "run_directory_delta": 0, "runtime_evidence_delta": 0,
        })


def independent_sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def refresh_link_hash(result: dict, path: Path) -> None:
    resolved = path.resolve()
    link = next(item for item in result["scenario_evidence"] if Path(item["path"]).resolve() == resolved)
    link["sha256"] = independent_sha256(path)


if __name__ == "__main__":
    unittest.main()
