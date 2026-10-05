from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_Core"))

from beta_core.cli import run_task  # noqa: E402
from beta_core.event_store import REQUIRED_EVENT_FIELDS  # noqa: E402
from beta_core.model import sha256_file  # noqa: E402


FIXTURES = ROOT / "03_Tests" / "fixtures"
BASE_PLAN_PATH = FIXTURES / "task_phase1.json"
TEMP_PARENT = ROOT / "03_Tests" / ".tmp"


def independent_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class Phase1Tests(unittest.TestCase):
    def setUp(self) -> None:
        TEMP_PARENT.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_PARENT)
        self.work = Path(self.temp.name)
        self.plan = json.loads(BASE_PLAN_PATH.read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        self.temp.cleanup()
        try:
            TEMP_PARENT.rmdir()
        except OSError:
            pass

    def write_plan(self, plan: dict, name: str = "task.json") -> Path:
        path = self.work / name
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def run_plan(self, plan: dict, evidence_name: str = "evidence") -> dict:
        return run_task(self.write_plan(plan), ROOT, self.work / evidence_name)

    def test_01_success_proceeds(self) -> None:
        result = self.run_plan(self.plan)
        self.assertEqual((result["status"], result["validation"], result["gate"]), ("PASS", "PASS", "PROCEED"))

    def test_02_empty_required_validators_blocks_before_run(self) -> None:
        self.plan["required_validators"] = []
        result = self.run_plan(self.plan)
        self.assertEqual((result["status"], result["execution"], result["gate"]), ("BLOCKED", "NOT_RUN", "BLOCK"))

    def test_03_validator_fail_blocks(self) -> None:
        self.plan["plan_version"] = "1.0-fail"
        spec = self.plan["required_validators"][0]
        spec.update(path="03_Tests/fixtures/validator_fail.py", sha256=sha256_file(FIXTURES / "validator_fail.py"), criteria={"mode": "fail"})
        result = self.run_plan(self.plan)
        self.assertEqual((result["status"], result["validation"], result["gate"]), ("FAIL", "FAIL", "BLOCK"))

    def test_04_validator_error_is_not_product_fail(self) -> None:
        self.plan["plan_version"] = "1.0-error"
        spec = self.plan["required_validators"][0]
        spec.update(path="03_Tests/fixtures/validator_fail.py", sha256=sha256_file(FIXTURES / "validator_fail.py"), criteria={"mode": "error"})
        result = self.run_plan(self.plan)
        self.assertEqual((result["status"], result["validation"], result["gate"]), ("ERROR", "ERROR", "BLOCK"))

    def test_05_validator_hash_mismatch_blocks_before_run(self) -> None:
        self.plan["required_validators"][0]["sha256"] = "0" * 64
        result = self.run_plan(self.plan)
        self.assertEqual((result["status"], result["execution"]), ("BLOCKED", "NOT_RUN"))

    def test_06_executor_hash_mismatch_blocks_before_run(self) -> None:
        self.plan["executor"]["sha256"] = "0" * 64
        result = self.run_plan(self.plan)
        self.assertEqual((result["status"], result["execution"]), ("BLOCKED", "NOT_RUN"))

    def test_07_write_owner_must_be_exactly_one(self) -> None:
        self.plan["write_owner"] = ["Codex", "Claude Code"]
        result = self.run_plan(self.plan)
        self.assertEqual((result["status"], result["execution"]), ("BLOCKED", "NOT_RUN"))

    def test_08_event_jsonl_is_ordered_and_complete(self) -> None:
        self.run_plan(self.plan)
        events = [json.loads(line) for line in (self.work / "evidence" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([event["type"] for event in events], ["RUN_STARTED", "RUN_COMPLETED", "CHECKPOINT_RECORDED", "VALIDATION_STARTED", "VALIDATION_RESULT", "EVIDENCE_RECORDED", "GATE_DECISION"])
        self.assertTrue(all(set(event) == REQUIRED_EVENT_FIELDS for event in events))
        checkpoint = events[2]["payload"]
        self.assertEqual(checkpoint["stage_id"], "STEP-001")
        self.assertEqual(independent_sha256(Path(checkpoint["state_path"])), checkpoint["state_sha256"])

    def test_09_evidence_sha256_matches_index(self) -> None:
        result = self.run_plan(self.plan)
        record = result["evidence"]
        self.assertEqual(independent_sha256(Path(record["path"])), record["sha256"])

    def test_10_failed_run_is_not_overwritten_by_later_pass(self) -> None:
        failed = copy.deepcopy(self.plan)
        failed["plan_version"] = "1.0-fail"
        spec = failed["required_validators"][0]
        spec.update(path="03_Tests/fixtures/validator_fail.py", sha256=sha256_file(FIXTURES / "validator_fail.py"), criteria={"mode": "fail"})
        first = self.run_plan(failed, "shared")
        first_path = Path(first["evidence"]["path"])
        first_bytes = first_path.read_bytes()
        second = self.run_plan(self.plan, "shared")
        self.assertEqual(first["status"], "FAIL")
        self.assertEqual(second["status"], "PASS")
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertEqual(first_path.read_bytes(), first_bytes)
        self.assertNotEqual(first["evidence"]["path"], second["evidence"]["path"])

    def test_11_same_task_version_with_different_plan_hash_blocks(self) -> None:
        shared = self.work / "shared"
        first_path = self.write_plan(self.plan, "first.json")
        first = run_task(first_path, ROOT, shared)
        changed = copy.deepcopy(self.plan)
        changed["write_scope"] = ["04_Evidence/phase1", "04_Evidence/phase1/extra"]
        second = run_task(self.write_plan(changed, "changed.json"), ROOT, shared)
        self.assertEqual(first["status"], "PASS")
        self.assertEqual((second["status"], second["execution"], second["gate"]), ("BLOCKED", "NOT_RUN", "BLOCK"))
        events = [json.loads(line) for line in (shared / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[-1]["type"], "BLOCKED")
        self.assertIn("first_task_plan_sha256", events[-1]["payload"]["contract"])

    def test_12_multiple_owner_string_blocks_before_run(self) -> None:
        self.plan["write_owner"] = "Codex, Claude Code"
        result = self.run_plan(self.plan)
        self.assertEqual((result["status"], result["execution"], result["gate"]), ("BLOCKED", "NOT_RUN", "BLOCK"))

    def test_13_executor_error_never_becomes_validation_pass(self) -> None:
        self.plan["plan_version"] = "1.2-executor-error"
        self.plan["executor"] = {
            "path": "03_Tests/fixtures/executor_error.py",
            "sha256": independent_sha256(FIXTURES / "executor_error.py"),
        }
        result = self.run_plan(self.plan)
        events = [json.loads(line) for line in (self.work / "evidence" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual((result["status"], result["execution"], result["validation"], result["gate"]), ("ERROR", "ERROR", "NOT_RUN", "BLOCK"))
        self.assertIn("EXECUTION_ERROR", [event["type"] for event in events])

    def test_14_validator_timeout_is_error_and_blocks(self) -> None:
        self.plan["plan_version"] = "1.2-validator-timeout"
        self.plan["required_validators"][0] = {
            "validator_id": "VAL-TIMEOUT",
            "path": "03_Tests/fixtures/validator_timeout.py",
            "sha256": independent_sha256(FIXTURES / "validator_timeout.py"),
            "criteria": {},
        }
        result = run_task(
            self.write_plan(self.plan),
            ROOT,
            self.work / "evidence",
            executor_timeout_seconds=10.0,
            validator_timeout_seconds=0.1,
        )
        events = [json.loads(line) for line in (self.work / "evidence" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual((result["status"], result["validation"], result["gate"]), ("ERROR", "ERROR", "BLOCK"))
        self.assertIn("RUN_COMPLETED", [event["type"] for event in events])
        self.assertNotIn("EXECUTION_ERROR", [event["type"] for event in events])

    def test_15_evidence_write_failure_cannot_proceed(self) -> None:
        with mock.patch("beta_core.cli._write_evidence", side_effect=OSError("synthetic evidence failure")):
            result = self.run_plan(self.plan)
        events = [json.loads(line) for line in (self.work / "evidence" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual((result["status"], result["gate"], result["evidence"]), ("ERROR", "BLOCK", None))
        self.assertNotIn("EVIDENCE_RECORDED", [event["type"] for event in events])
        self.assertFalse((self.work / "evidence" / "evidence_index.jsonl").exists())

    def test_16_second_run_appends_without_rewriting_first_events(self) -> None:
        shared = self.work / "shared"
        plan_path = self.write_plan(self.plan)
        first = run_task(plan_path, ROOT, shared)
        event_path = shared / "events.jsonl"
        first_bytes = event_path.read_bytes()
        first_ids = [json.loads(line)["event_id"] for line in first_bytes.decode("utf-8").splitlines()]
        second = run_task(plan_path, ROOT, shared)
        combined = event_path.read_bytes()
        all_ids = [json.loads(line)["event_id"] for line in combined.decode("utf-8").splitlines()]
        self.assertEqual((first["status"], second["status"]), ("PASS", "PASS"))
        self.assertTrue(combined.startswith(first_bytes))
        self.assertEqual(all_ids[: len(first_ids)], first_ids)

    def test_17_missing_change_reason_ref_blocks(self) -> None:
        del self.plan["change_reason_ref"]
        result = self.run_plan(self.plan)
        self.assertEqual((result["status"], result["execution"], result["gate"]), ("BLOCKED", "NOT_RUN", "BLOCK"))


if __name__ == "__main__":
    unittest.main()
