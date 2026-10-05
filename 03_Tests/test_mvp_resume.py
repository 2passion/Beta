import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_Core"))
sys.path.insert(0, str(ROOT / "03_Tests/fixtures"))

from beta_core.cli import run_task  # noqa: E402
from beta_core.executor import run_executor  # noqa: E402
from beta_core.event_store import EventStore  # noqa: E402
from beta_core.gate import decide_gate  # noqa: E402
from beta_core.validator_runner import run_validator  # noqa: E402


FIXTURES = ROOT / "03_Tests/fixtures"
PLAN = FIXTURES / "task_mvp_test_7_resume.json"
EXECUTOR = FIXTURES / "resume_scenario_executor.py"
VALIDATOR = FIXTURES / "resume_validator.py"


def criteria():
    return json.loads(PLAN.read_text(encoding="utf-8"))["required_validators"][0]["criteria"]


def prepare(temporary):
    result_path = Path(temporary) / "mvp_test_7/official/runs/PREP/executor_result.json"
    execution = run_executor(EXECUTOR, result_path, 20.0)
    if execution["status"] != "PASS":
        raise AssertionError(execution)
    return execution, result_path, json.loads(result_path.read_text(encoding="utf-8"))


def overwrite_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def refresh_manifest(result_path, result):
    root = Path(result["scenario_root"])
    result["scenario_manifest"] = [
        {"scenario_id": path.relative_to(root).parts[0], "relative_path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in sorted(root.rglob("*")) if path.is_file()
    ]
    overwrite_json(result_path, result)


def assert_blocked(test, execution, result_path):
    validation = run_validator("VAL-MVP-TEST-7-RESUME", VALIDATOR, result_path, criteria(), 10.0)
    test.assertEqual(validation["status"], "FAIL")
    test.assertEqual(decide_gate(execution, [validation], evidence_recorded=True), "BLOCK")
    return json.loads(validation["stdout"])


class ResumeTests(unittest.TestCase):
    def test_71_scenarios_a_to_g(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "mvp_test_7/official", executor_timeout_seconds=20.0)
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("PASS", "PASS", "PROCEED"))

    def test_72_mutation_m1_fake_pass_checkpoint_without_evidence_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            checkpoint_path = Path(result["scenarios"]["A"]["source_checkpoint"])
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            checkpoint["evidence_refs"] = []
            overwrite_json(checkpoint_path, checkpoint)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A source checkpoint invalid", output["failures"])

    def test_73_mutation_m2_tampered_evidence_hash_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            checkpoint_path = Path(result["scenarios"]["A"]["final_checkpoint"])
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            checkpoint["evidence_refs"][-1]["evidence_sha256"] = "0" * 64
            overwrite_json(checkpoint_path, checkpoint)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A final checkpoint invalid", output["failures"])

    def test_74_mutation_m3_completed_step_rerun_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            directory = Path(result["scenario_dirs"]["A"])
            EventStore(directory / "events.jsonl").append(
                "STEP_RESUMED", task_id="MVP-TEST-7-RESUME", run_id="MUTATION-M3",
                plan_version="1.1", actor_role="Mutation", payload={"step_id": "STEP-1"},
            )
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A did not resume exact next incomplete step", output["failures"])

    def test_75_mutation_m4_skipped_next_step_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            path = Path(result["scenario_dirs"]["A"]) / "events.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            resumed = [row for row in rows if row.get("type") == "STEP_RESUMED"]
            resumed[0]["payload"]["step_id"], resumed[1]["payload"]["step_id"] = resumed[1]["payload"]["step_id"], resumed[0]["payload"]["step_id"]
            path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A did not resume exact next incomplete step", output["failures"])

    def test_76_mutation_m5_hidden_side_effect_drift_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            path = Path(result["scenario_dirs"]["A"]) / "side_effects/STEP-2.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["value"] = "tampered"
            overwrite_json(path, value)
            output = assert_blocked(self, execution, result_path)
            self.assertTrue(any("checkpoint invalid" in item for item in output["failures"]))

    def test_77_mutation_m6_chunk_as_checkpoint_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            result["scenarios"]["C"]["chunk_decision"] = {"decision": "RESUME_ALLOWED", "reason_code": "VERIFIED_CHECKPOINT", "next_step": "STEP-2"}
            overwrite_json(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario C executed without checkpoint", output["failures"])

    def test_78_mutation_m7_interrupted_event_rewrite_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            path = Path(result["scenario_dirs"]["A"]) / "events.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            next(row for row in rows if row.get("type") == "RUN_INTERRUPTED")["type"] = "RUN_COMPLETED"
            path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
            refresh_manifest(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A interrupted/resume event identity missing", output["failures"])

    def test_79_mutation_m8_resume_reuses_interrupted_identity_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            path = Path(result["scenario_dirs"]["A"]) / "events.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            interrupted_id = next(row["run_id"] for row in rows if row.get("type") == "RUN_INTERRUPTED")
            resume_id = next(row["run_id"] for row in rows if row.get("type") == "RESUME_STARTED")
            for row in rows:
                if row.get("run_id") == resume_id:
                    row["run_id"] = interrupted_id
            path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
            refresh_manifest(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A resume reused interrupted identity", output["failures"])

    def test_80_mutation_m9_evidence_identity_tamper_with_rehashed_links_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            directory = Path(result["scenario_dirs"]["A"])
            checkpoint_path = Path(result["scenarios"]["A"]["source_checkpoint"])
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            evidence_path = Path(checkpoint["evidence_refs"][0]["evidence_path"])
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["task_id"] = "FAKE-TASK"
            overwrite_json(evidence_path, evidence)
            checkpoint["evidence_refs"][0]["evidence_sha256"] = sha256_file(evidence_path)
            overwrite_json(checkpoint_path, checkpoint)
            events_path = directory / "events.jsonl"
            rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            for row in rows:
                if row.get("type") == "CHECKPOINT_RECORDED" and row.get("payload", {}).get("checkpoint_id") == checkpoint["checkpoint_id"]:
                    row["payload"]["sha256"] = sha256_file(checkpoint_path)
            events_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
            refresh_manifest(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A source checkpoint invalid", output["failures"])

    def test_81_mutation_m10_post_resume_extra_file_fails_current_measurement(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            path = Path(result["scenario_dirs"]["F"]) / "evidence/EVD-EXTRA.json"
            overwrite_json(path, {"unexpected": True})
            refresh_manifest(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario F current filesystem/Evidence changed on re-entry", output["failures"])

    def test_82_mutation_m11_unmanifested_scenario_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            overwrite_json(Path(result["scenario_dirs"]["B"]) / "unexpected.json", {"unexpected": True})
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario manifest mismatch or unlinked file", output["failures"])


if __name__ == "__main__":
    unittest.main()
