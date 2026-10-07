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
from beta_core import runtime_policy  # noqa: E402
from beta_core.event_store import EventStore  # noqa: E402
from beta_core.model import sha256_file  # noqa: E402
from beta_core.user_gate import issue_fixture_user_gate_authorization  # noqa: E402


TEMP_PARENT = ROOT / "03_Tests" / ".tmp"


class RuntimeBoundaryEnforcementTests(unittest.TestCase):
    def setUp(self) -> None:
        TEMP_PARENT.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_PARENT)
        self.work = Path(self.temp.name)
        self.approved_root = self.work / "approved"
        self.approved_root.mkdir()
        self.target = self.approved_root / "target.md"
        self.target.write_text("isolated enforcement target\n", encoding="utf-8")
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

    def request(self, request_id: str, **changes: object) -> dict:
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

    def plan(self, request_id: str) -> dict:
        prepared = boundary.prepare_runtime_request(self.request(request_id))
        self.assertEqual(prepared["status"], "READY_FOR_FINAL_USER_GATE")
        return boundary._build_plan(
            prepared["normalized_request"],
            self.work / f"core-{request_id}",
            prepared["runtime_request_hash"],
            prepared["runtime_code_baseline_hash"],
        )

    def execute(self, request: dict) -> dict:
        prepared = boundary.prepare_runtime_request(request)
        authorization = None
        if prepared.get("status") == "READY_FOR_FINAL_USER_GATE" and request.get("execution_context") == "TEST_FIXTURE":
            authorization = issue_fixture_user_gate_authorization(
                project_root=ROOT,
                runtime_request_hash=prepared["runtime_request_hash"],
                runtime_code_baseline_hash=prepared["runtime_code_baseline_hash"],
                approved_git_commit=prepared["approved_git_commit"],
                decision_ref=f"FIXTURE-USER-GATE-{request['request_id']}",
            )
        return boundary.execute_approved_request(request, authorization)

    def write_plan(self, plan: dict, name: str) -> Path:
        path = self.work / name
        path.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return path

    def event_types(self, evidence_dir: Path) -> list[str]:
        path = evidence_dir / "events.jsonl"
        if not path.exists():
            return []
        return [json.loads(line)["type"] for line in path.read_text(encoding="utf-8").splitlines()]

    def test_113_direct_core_missing_approval_blocks_before_run(self) -> None:
        plan = self.plan("ATTACK-113")
        plan["runtime_request"]["approval_ref"] = ""
        evidence = self.work / "direct-missing-approval"
        result = cli.run_task(self.write_plan(plan, "missing-approval.json"), ROOT, evidence)
        self.assertEqual((result["status"], result["execution"], result["gate"]), ("BLOCKED", "NOT_RUN", "BLOCK"))
        self.assertNotIn("RUN_STARTED", self.event_types(evidence))
        self.assertFalse((evidence / "runs").exists())

    def test_114_evil_executor_and_caller_allowlist_execute_zero(self) -> None:
        marker = self.work / "evil-marker.txt"
        evil = self.work / "evil_exec.py"
        evil.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n", encoding="utf-8")
        plan = self.plan("ATTACK-114")
        plan["executor"] = {"path": str(evil), "sha256": sha256_file(evil)}
        evidence = self.work / "evil-evidence"
        result = cli.run_task(
            self.write_plan(plan, "evil.json"),
            ROOT,
            evidence,
            approved_program_paths={evil, boundary.VALIDATOR_PATH},
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(marker.exists())
        self.assertNotIn("RUN_STARTED", self.event_types(evidence))

    def test_115_modified_approved_executor_sha_blocks(self) -> None:
        real_sha = runtime_policy.sha256_file

        def changed(path: Path) -> str:
            return "0" * 64 if Path(path).resolve() == boundary.EXECUTOR_PATH else real_sha(path)

        with mock.patch.object(runtime_policy, "sha256_file", side_effect=changed):
            result = self.execute(self.request("ATTACK-115"))
        self.assertEqual((result["status"], result["decision"], result["run_task_call_count"]), ("HOLD", "HOLD", 0))

    def test_116_replaced_validator_sha_blocks(self) -> None:
        real_sha = runtime_policy.sha256_file

        def changed(path: Path) -> str:
            return "0" * 64 if Path(path).resolve() == boundary.VALIDATOR_PATH else real_sha(path)

        with mock.patch.object(runtime_policy, "sha256_file", side_effect=changed):
            result = self.execute(self.request("ATTACK-116"))
        self.assertEqual((result["status"], result["decision"], result["run_task_call_count"]), ("HOLD", "HOLD", 0))

    def test_117_arbitrary_approval_ref_is_not_production_approval(self) -> None:
        result = self.execute(self.request("ATTACK-117", approval_ref="x", execution_context="PRODUCTION"))
        self.assertEqual((result["status"], result["decision"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", "APPROVAL_REQUIRED", 0))
        self.assertFalse(self.evidence_root.exists())

    def test_118_fixture_approval_cannot_authorize_production(self) -> None:
        result = self.execute(self.request("ATTACK-118", execution_context="PRODUCTION"))
        self.assertEqual(result["reason"], "PRODUCTION_APPROVAL_NOT_ISSUED")
        self.assertEqual(result["run_task_call_count"], 0)

    def test_119_boundary_block_history_prevents_no_change(self) -> None:
        request = self.request("ATTACK-119")
        first = self.execute(request)
        EventStore(Path(first["evidence_dir"]) / "events.jsonl").append(
            "RUNTIME_BOUNDARY_DECISION",
            task_id=first["core_result"]["task_id"],
            run_id=first["core_result"]["run_id"],
            plan_version="1.0",
            actor_role="RuntimeBoundary",
            payload={"decision": "BLOCK", "core_gate": "PROCEED"},
        )
        second = boundary.execute_approved_request(request)
        self.assertEqual((second["status"], second["decision"], second["run_task_call_count"]), ("HOLD", "HOLD", 0))

    def test_120_tampered_evidence_with_rehashed_links_prevents_no_change(self) -> None:
        request = self.request("ATTACK-120")
        first = self.execute(request)
        evidence_dir = Path(first["evidence_dir"])
        body_path = Path(first["core_result"]["evidence"]["path"])
        body = json.loads(body_path.read_text(encoding="utf-8"))
        body["executor_path"] = "evil_exec.py"
        body_path.write_text(json.dumps(body, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        index_path = evidence_dir / "evidence_index.jsonl"
        index = json.loads(index_path.read_text(encoding="utf-8").strip())
        index["sha256"] = sha256_file(body_path)
        index_path.write_text(json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        second = boundary.execute_approved_request(request)
        self.assertEqual((second["status"], second["decision"], second["run_task_call_count"]), ("HOLD", "HOLD", 0))

    def test_121_previous_fail_prevents_no_change(self) -> None:
        real = cli.run_executor

        def forged(*args: object, **kwargs: object) -> dict:
            execution = real(*args, **kwargs)
            result_path = Path(args[1])
            body = json.loads(result_path.read_text(encoding="utf-8"))
            body["observed_after"]["sha256"] = "0" * 64
            result_path.write_text(json.dumps(body, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            return execution

        request = self.request("ATTACK-121")
        with mock.patch.object(cli, "run_executor", side_effect=forged):
            first = self.execute(request)
        second = boundary.execute_approved_request(request)
        self.assertEqual(first["status"], "FAIL")
        self.assertEqual((second["status"], second["decision"], second["run_task_call_count"]), ("HOLD", "HOLD", 0))

    def test_122_genuine_pass_is_no_change_without_new_files(self) -> None:
        request = self.request("ATTACK-122")
        first = self.execute(request)
        evidence_dir = Path(first["evidence_dir"])
        before = {path.relative_to(evidence_dir): sha256_file(path) for path in evidence_dir.rglob("*") if path.is_file()}
        second = boundary.execute_approved_request(request)
        after = {path.relative_to(evidence_dir): sha256_file(path) for path in evidence_dir.rglob("*") if path.is_file()}
        self.assertEqual((second["status"], second["decision"], second["run_task_call_count"]), ("NO_CHANGE", "NO_CHANGE", 0))
        self.assertEqual(before, after)

    def test_123_strict_bool_int_and_unknown_fields_hold(self) -> None:
        attacks = (
            {"task_count": True},
            {"parallel_allowed": 0},
            {"network": 0},
            {"external_publish": 0},
            {"unknown_field": "not-approved"},
        )
        for number, changes in enumerate(attacks):
            with self.subTest(changes=changes):
                result = self.execute(self.request(f"ATTACK-123-{number}", **changes))
                self.assertEqual((result["status"], result["run_task_call_count"]), ("HOLD", 0))

    def test_124_reserved_request_ids_hold(self) -> None:
        for request_id in ("CON", "PRN", "AUX", "NUL", "COM1", "COM9", "LPT1", "LPT9"):
            with self.subTest(request_id=request_id):
                result = self.execute(self.request(request_id))
                self.assertEqual((result["status"], result["reason"], result["run_task_call_count"]), ("HOLD", "REQUEST_ID_RESERVED", 0))

    def test_125_final_target_deletion_is_recorded_and_blocked(self) -> None:
        real = cli.run_executor

        def deleting(*args: object, **kwargs: object) -> dict:
            execution = real(*args, **kwargs)
            self.target.unlink()
            return execution

        with mock.patch.object(cli, "run_executor", side_effect=deleting):
            result = self.execute(self.request("ATTACK-125"))
        self.assertEqual((result["status"], result["decision"]), ("FAIL", "BLOCK"))
        events = [json.loads(line) for line in (Path(result["evidence_dir"]) / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        final = [event for event in events if event["type"] == "RUNTIME_BOUNDARY_VALIDATION"][-1]
        self.assertIsNotNone(final["payload"]["observation_error"])

    def test_126_reparse_or_unconfirmed_identity_holds(self) -> None:
        with mock.patch.object(boundary, "_has_reparse_component", return_value=True):
            unsafe = self.execute(self.request("ATTACK-126-A"))
        with mock.patch.object(boundary, "_has_reparse_component", side_effect=OSError("unconfirmed")):
            unknown = self.execute(self.request("ATTACK-126-B"))
        self.assertEqual((unsafe["status"], unsafe["reason"], unsafe["run_task_call_count"]), ("HOLD", "TARGET_IDENTITY_UNSAFE", 0))
        self.assertEqual((unknown["status"], unknown["reason"], unknown["run_task_call_count"]), ("HOLD", "TARGET_IDENTITY_UNCONFIRMED", 0))

    def test_127_direct_core_outside_scope_and_fixture_production_bypass_block(self) -> None:
        outside = self.work / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        plan = self.plan("ATTACK-127")
        plan["runtime_request"].update(
            target_path=str(outside.resolve()),
            approved_root=str(self.work.resolve()),
            execution_context="PRODUCTION",
        )
        plan["runtime_request"]["preflight"] = {
            "path": str(outside.resolve()),
            "exists": True,
            "size": outside.stat().st_size,
            "sha256": sha256_file(outside),
        }
        plan["required_validators"][0]["criteria"].update(
            target_path=str(outside.resolve()),
            preflight=plan["runtime_request"]["preflight"],
        )
        evidence = self.work / "direct-outside"
        result = cli.run_task(self.write_plan(plan, "direct-outside.json"), ROOT, evidence)
        self.assertEqual((result["status"], result["execution"], result["gate"]), ("BLOCKED", "NOT_RUN", "BLOCK"))
        self.assertNotIn("RUN_STARTED", self.event_types(evidence))
        self.assertFalse((evidence / "runs").exists())


if __name__ == "__main__":
    unittest.main()
