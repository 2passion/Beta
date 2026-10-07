from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_Core"))

from beta_core import cli  # noqa: E402
from beta_core import runtime_boundary as boundary  # noqa: E402
from beta_core.model import sha256_file, validate_pinned_programs  # noqa: E402
from beta_core.user_gate import issue_fixture_user_gate_authorization  # noqa: E402


TEMP_PARENT = ROOT / "03_Tests" / ".tmp"


class RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        TEMP_PARENT.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_PARENT)
        self.work = Path(self.temp.name)
        self.approved_root = self.work / "approved"
        self.approved_root.mkdir()
        self.target = self.approved_root / "isolated-target.md"
        self.target.write_text("isolated runtime target\n", encoding="utf-8")
        self.evidence_root = self.work / "evidence"
        self.patchers = [
            mock.patch.object(boundary, "APPROVED_ROOT", self.approved_root),
            mock.patch.object(boundary, "FIRST_RUNTIME_TARGET", self.target),
            mock.patch.object(boundary, "EVIDENCE_ROOT", self.evidence_root),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self) -> None:
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.temp.cleanup()
        try:
            TEMP_PARENT.rmdir()
        except OSError:
            pass

    def request(self, request_id: str = "REQ-V1", **changes: object) -> dict:
        request = {
            "request_id": request_id,
            "approval_ref": "ORDER-062-ISOLATED-FIXTURE",
            "operation": "READ_ONLY_INTEGRITY",
            "target_path": str(self.target.resolve()),
            "approved_root": str(self.approved_root.resolve()),
            "task_count": 1,
            "parallel_allowed": False,
            "dependencies": [],
            "expected_target_side_effect": "NONE",
            "network": False,
            "external_publish": False,
            "execution_context": "TEST_FIXTURE",
        }
        request.update(changes)
        return request

    def execute(self, request: dict) -> dict:
        prepared = boundary.prepare_runtime_request(request)
        authorization = None
        if prepared.get("status") == "READY_FOR_FINAL_USER_GATE":
            authorization = issue_fixture_user_gate_authorization(
                project_root=ROOT,
                runtime_request_hash=prepared["runtime_request_hash"],
                runtime_code_baseline_hash=prepared["runtime_code_baseline_hash"],
                approved_git_commit=prepared["approved_git_commit"],
                decision_ref=f"FIXTURE-USER-GATE-{request['request_id']}",
            )
        return boundary.execute_approved_request(request, authorization)

    def build_plan(self, request: dict, evidence_dir: Path) -> dict:
        prepared = boundary.prepare_runtime_request(request)
        self.assertEqual(prepared["status"], "READY_FOR_FINAL_USER_GATE")
        return boundary._build_plan(
            prepared["normalized_request"],
            evidence_dir,
            prepared["runtime_request_hash"],
            prepared["runtime_code_baseline_hash"],
        )

    def test_v1_normal_pass_proceed_and_target_unchanged(self) -> None:
        before = sha256_file(self.target)
        result = self.execute(self.request())
        self.assertEqual((result["status"], result["decision"]), ("PASS", "PROCEED"))
        self.assertEqual(result["run_task_call_count"], 1)
        self.assertEqual(result["target_before"], result["target_after"])
        self.assertEqual(sha256_file(self.target), before)

    def test_v2_forged_executor_result_fails_and_blocks(self) -> None:
        real = cli.run_executor

        def forged(*args: object, **kwargs: object) -> dict:
            execution = real(*args, **kwargs)
            result_path = Path(args[1])
            body = json.loads(result_path.read_text(encoding="utf-8"))
            body["observed_after"]["sha256"] = "0" * 64
            result_path.write_text(json.dumps(body, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            return execution

        with mock.patch.object(cli, "run_executor", side_effect=forged):
            result = self.execute(self.request("REQ-V2"))
        self.assertEqual((result["status"], result["decision"]), ("FAIL", "BLOCK"))
        self.assertEqual(result["core_result"]["validation"], "FAIL")

    def test_v3_out_of_scope_holds_with_run_zero(self) -> None:
        outside = self.work / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        result = self.execute(self.request("REQ-V3", target_path=str(outside.resolve())))
        self.assertEqual((result["status"], result["decision"], result["run_task_call_count"]), ("HOLD", "HOLD", 0))
        self.assertFalse(self.evidence_root.exists())

    def test_v4_dangerous_ads_path_holds_with_run_zero(self) -> None:
        dangerous = str(self.target.resolve()) + ":stream"
        result = self.execute(self.request("REQ-V4", target_path=dangerous))
        self.assertEqual((result["status"], result["reason"], result["run_task_call_count"]), ("HOLD", "TARGET_PATH_ADS", 0))
        self.assertFalse(self.evidence_root.exists())

    def test_v5_missing_target_holds_with_run_zero(self) -> None:
        missing = self.approved_root / "missing.md"
        with mock.patch.object(boundary, "FIRST_RUNTIME_TARGET", missing):
            result = self.execute(self.request("REQ-V5", target_path=str(missing.resolve())))
        self.assertEqual((result["status"], result["reason"], result["run_task_call_count"]), ("HOLD", "TARGET_MISSING", 0))
        self.assertFalse(self.evidence_root.exists())

    def test_v6_target_mutation_fails_and_blocks(self) -> None:
        real = cli.run_executor

        def mutating(*args: object, **kwargs: object) -> dict:
            execution = real(*args, **kwargs)
            self.target.write_text("mutated after executor\n", encoding="utf-8")
            return execution

        with mock.patch.object(cli, "run_executor", side_effect=mutating):
            result = self.execute(self.request("REQ-V6"))
        self.assertEqual((result["status"], result["decision"]), ("FAIL", "BLOCK"))
        self.assertFalse(result["target_before"] == result["target_after"])

    def test_v7_missing_approval_has_execution_zero(self) -> None:
        result = self.execute(self.request("REQ-V7", approval_ref=""))
        self.assertEqual((result["status"], result["decision"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", "APPROVAL_REQUIRED", 0))
        self.assertFalse(self.evidence_root.exists())

    def test_v8_evidence_identity_hash_tamper_blocks(self) -> None:
        mutations = {
            "request": lambda body: body["runtime_request"].update(request_id="FORGED"),
            "task": lambda body: body.update(task_id="TASK-FORGED"),
            "run": lambda body: body.update(run_id="RUN-FORGED"),
            "validation": lambda body: body["validations"][0].update(validator_id="VALIDATOR-FORGED"),
            "evidence": lambda body: body.update(evidence_id="EVD-FORGED"),
            "sha": lambda body: body.update(task_plan_sha256="0" * 64),
        }
        for number, (label, mutate) in enumerate(mutations.items(), start=1):
            with self.subTest(label=label):
                result = self.execute(self.request(f"REQ-V8-{number}"))
                self.assertEqual(result["status"], "PASS")
                evidence_dir = Path(result["evidence_dir"])
                evidence_path = Path(result["core_result"]["evidence"]["path"])
                body = json.loads(evidence_path.read_text(encoding="utf-8"))
                mutate(body)
                evidence_path.write_text(json.dumps(body, sort_keys=True, indent=2) + "\n", encoding="utf-8")
                index_path = evidence_dir / "evidence_index.jsonl"
                index = json.loads(index_path.read_text(encoding="utf-8").strip())
                index["sha256"] = sha256_file(evidence_path)
                index_path.write_text(json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
                verification = boundary.verify_runtime_evidence(
                    evidence_dir=evidence_dir,
                    task_plan_path=Path(result["task_plan"]),
                    request=json.loads(Path(result["task_plan"]).read_text(encoding="utf-8"))["runtime_request"],
                    core_result=result["core_result"],
                )
                self.assertEqual(verification["status"], "FAIL")

    def test_exact_executable_allowlist_rejects_unlisted_program(self) -> None:
        plan = self.build_plan(self.request("REQ-ALLOW"), self.evidence_root / "REQ-ALLOW")
        plan["executor"]["path"] = "03_Tests/fixtures/executor_success.py"
        plan["executor"]["sha256"] = sha256_file(ROOT / "03_Tests" / "fixtures" / "executor_success.py")
        _, errors = validate_pinned_programs(plan, ROOT, {boundary.EXECUTOR_PATH, boundary.VALIDATOR_PATH})
        self.assertTrue(any("exact approved allowlist" in error for error in errors))

    def test_sha_pin_rejects_modified_pin(self) -> None:
        plan = self.build_plan(self.request("REQ-PIN"), self.evidence_root / "REQ-PIN")
        plan["executor"]["sha256"] = "F" * 64
        _, errors = validate_pinned_programs(plan, ROOT, {boundary.EXECUTOR_PATH, boundary.VALIDATOR_PATH})
        self.assertIn("executor SHA-256 mismatch", errors)

    def test_duplicate_identical_pass_returns_no_change(self) -> None:
        request = self.request("REQ-DUPLICATE")
        first = self.execute(request)
        evidence_dir = Path(first["evidence_dir"])
        files_before = {path.relative_to(evidence_dir): sha256_file(path) for path in evidence_dir.rglob("*") if path.is_file()}
        second = boundary.execute_approved_request(request)
        files_after = {path.relative_to(evidence_dir): sha256_file(path) for path in evidence_dir.rglob("*") if path.is_file()}
        self.assertEqual(first["status"], "PASS")
        self.assertEqual((second["status"], second["decision"], second["run_task_call_count"]), ("NO_CHANGE", "NO_CHANGE", 0))
        self.assertEqual(files_before, files_after)

    def test_duplicate_changed_contract_holds(self) -> None:
        request = self.request("REQ-COLLISION")
        first = self.execute(request)
        changed = dict(request)
        changed["approval_ref"] = "DIFFERENT-APPROVAL"
        second = self.execute(changed)
        self.assertEqual(first["status"], "PASS")
        self.assertEqual((second["status"], second["decision"], second["run_task_call_count"]), ("HOLD", "HOLD", 0))


if __name__ == "__main__":
    unittest.main()
