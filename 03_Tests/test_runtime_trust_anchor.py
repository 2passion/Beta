from __future__ import annotations

import json
import copy
import pickle
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_Core"))

from beta_core import runtime_boundary as boundary  # noqa: E402
from beta_core import cli as core_cli  # noqa: E402
from beta_core import user_gate as user_gate_module  # noqa: E402
from beta_core.model import sha256_file  # noqa: E402
from beta_core.runtime_policy import POLICY_RELATIVE_PATH, RUNTIME_CODE_BASELINE_PATHS  # noqa: E402
from beta_core.user_gate import claim_user_gate_authorization, issue_fixture_user_gate_authorization  # noqa: E402


TEMP_PARENT = ROOT.parent / ".beta-order-064-tests"
APPROVAL_REF = "ORDER-064-ISOLATED-USER-GATE"


class RuntimeTrustAnchorTests(unittest.TestCase):
    def setUp(self) -> None:
        TEMP_PARENT.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_PARENT)
        self.work = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()
        try:
            TEMP_PARENT.rmdir()
        except OSError:
            pass

    def git(self, repo: Path, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False, shell=False
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout.strip()

    def make_repo(self, name: str) -> dict:
        repo = self.work / name
        core = repo / "02_Core" / "beta_core"
        core.mkdir(parents=True)
        for relative_path in RUNTIME_CODE_BASELINE_PATHS:
            source = ROOT / relative_path
            destination = repo / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        executor = core / "file_integrity_executor.py"
        validator = core / "file_integrity_validator.py"
        target = repo / "isolated-target.md"
        target.write_text("isolated trust-anchor target\n", encoding="utf-8")
        policy_path = repo / POLICY_RELATIVE_PATH
        policy = {
            "policy_version": "1.0",
            "production": {
                "approved_root": str(repo.resolve()),
                "target_path": str(target.resolve()),
                "operation": "READ_ONLY_INTEGRITY",
            },
            "test_fixture": {
                "approval_ref": "ORDER-064-TEST-FIXTURE",
                "approved_root": "03_Tests/.tmp",
            },
            "executor": {
                "path": "02_Core/beta_core/file_integrity_executor.py",
                "sha256": sha256_file(executor),
            },
            "validator": {
                "path": "02_Core/beta_core/file_integrity_validator.py",
                "sha256": sha256_file(validator),
                "validator_id": "FILE-INTEGRITY-INDEPENDENT",
            },
        }
        policy_path.write_text(json.dumps(policy, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Order 064 Test")
        self.git(repo, "config", "user.email", "order064@example.invalid")
        self.git(repo, "config", "core.autocrlf", "false")
        self.git(repo, "add", POLICY_RELATIVE_PATH, *RUNTIME_CODE_BASELINE_PATHS, target.name)
        self.git(repo, "commit", "-m", "test: approved runtime baseline")
        commit = self.git(repo, "rev-parse", "HEAD")
        approvals = repo / "04_Evidence" / "runtime" / "approvals"
        approvals.mkdir(parents=True)
        packet_path = approvals / f"{APPROVAL_REF}.json"
        packet = {
            "approval_ref": APPROVAL_REF,
            "approved_git_commit": commit,
            "target_path": str(target.resolve()),
            "approved_root": str(repo.resolve()),
            "operation": "READ_ONLY_INTEGRITY",
            "policy_path": POLICY_RELATIVE_PATH,
            "policy_sha256": sha256_file(policy_path),
            "executor_path": policy["executor"]["path"],
            "executor_sha256": policy["executor"]["sha256"],
            "validator_path": policy["validator"]["path"],
            "validator_sha256": policy["validator"]["sha256"],
            "parallel_allowed": False,
            "dependencies": [],
            "approved_at": "2026-10-06T00:00:00Z",
        }
        packet_path.write_text(json.dumps(packet, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return {
            "repo": repo, "executor": executor, "validator": validator, "target": target,
            "policy_path": policy_path, "policy": policy, "packet_path": packet_path,
            "packet": packet, "commit": commit,
        }

    def request(self, env: dict, request_id: str) -> dict:
        return {
            "request_id": request_id,
            "approval_ref": APPROVAL_REF,
            "operation": "READ_ONLY_INTEGRITY",
            "target_path": str(env["target"].resolve()),
            "approved_root": str(env["repo"].resolve()),
            "task_count": 1,
            "parallel_allowed": False,
            "dependencies": [],
            "expected_target_side_effect": "NONE",
            "network": False,
            "external_publish": False,
            "execution_context": "PRODUCTION",
        }

    def run_boundary(self, env: dict, request_id: str, *, authorize: bool = False, authorization: object = None) -> dict:
        evidence_root = env["repo"] / "04_Evidence" / "runtime" / "read_only_integrity"
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(boundary, "PROJECT_ROOT", env["repo"]))
            stack.enter_context(mock.patch.object(boundary, "APPROVED_ROOT", env["repo"]))
            stack.enter_context(mock.patch.object(boundary, "FIRST_RUNTIME_TARGET", env["target"]))
            stack.enter_context(mock.patch.object(boundary, "EVIDENCE_ROOT", evidence_root))
            request = self.request(env, request_id)
            if authorize and authorization is None:
                prepared = boundary.prepare_runtime_request(request)
                self.assertEqual(prepared["status"], "READY_FOR_FINAL_USER_GATE")
                authorization = issue_fixture_user_gate_authorization(
                    project_root=env["repo"],
                    runtime_request_hash=prepared["runtime_request_hash"],
                    runtime_code_baseline_hash=prepared["runtime_code_baseline_hash"],
                    approved_git_commit=prepared["approved_git_commit"],
                    decision_ref=f"FIXTURE-USER-GATE-{request_id}",
                    production_simulation=True,
                )
            return boundary.execute_approved_request(request, authorization)

    def prepare(self, env: dict, request: dict) -> dict:
        evidence_root = env["repo"] / "04_Evidence" / "runtime" / "read_only_integrity"
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(boundary, "PROJECT_ROOT", env["repo"]))
            stack.enter_context(mock.patch.object(boundary, "APPROVED_ROOT", env["repo"]))
            stack.enter_context(mock.patch.object(boundary, "FIRST_RUNTIME_TARGET", env["target"]))
            stack.enter_context(mock.patch.object(boundary, "EVIDENCE_ROOT", evidence_root))
            return boundary.prepare_runtime_request(request)

    def authorization(self, env: dict, request_id: str):
        prepared = self.prepare(env, self.request(env, request_id))
        self.assertEqual(prepared["status"], "READY_FOR_FINAL_USER_GATE")
        authorization = issue_fixture_user_gate_authorization(
            project_root=env["repo"],
            runtime_request_hash=prepared["runtime_request_hash"],
            runtime_code_baseline_hash=prepared["runtime_code_baseline_hash"],
            approved_git_commit=prepared["approved_git_commit"],
            decision_ref=f"FIXTURE-USER-GATE-{request_id}",
            production_simulation=True,
        )
        return prepared, authorization

    def boundary_patches(self, env: dict) -> ExitStack:
        stack = ExitStack()
        stack.enter_context(mock.patch.object(boundary, "PROJECT_ROOT", env["repo"]))
        stack.enter_context(mock.patch.object(boundary, "APPROVED_ROOT", env["repo"]))
        stack.enter_context(mock.patch.object(boundary, "FIRST_RUNTIME_TARGET", env["target"]))
        stack.enter_context(mock.patch.object(
            boundary,
            "EVIDENCE_ROOT",
            env["repo"] / "04_Evidence" / "runtime" / "read_only_integrity",
        ))
        return stack

    def inject_marker(self, path: Path, marker: Path) -> None:
        text = path.read_text(encoding="utf-8")
        injection = f"from pathlib import Path as _TOCTOUPath\n_TOCTOUPath({str(marker)!r}).write_text('ran')\n"
        path.write_text(
            text.replace("from __future__ import annotations\n", "from __future__ import annotations\n\n" + injection, 1),
            encoding="utf-8",
        )

    def malicious_baseline(self, env: dict, marker: Path) -> str:
        executor_text = env["executor"].read_text(encoding="utf-8")
        injection = f"from pathlib import Path as _AttackPath\n_AttackPath({str(marker)!r}).write_text('ran')\n"
        env["executor"].write_text(
            executor_text.replace("from __future__ import annotations\n", "from __future__ import annotations\n\n" + injection, 1),
            encoding="utf-8",
        )
        policy = json.loads(env["policy_path"].read_text(encoding="utf-8"))
        policy["executor"]["sha256"] = sha256_file(env["executor"])
        policy["validator"]["sha256"] = sha256_file(env["validator"])
        env["policy_path"].write_text(json.dumps(policy, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        self.git(env["repo"], "add", POLICY_RELATIVE_PATH, policy["executor"]["path"], policy["validator"]["path"])
        self.git(env["repo"], "commit", "-m", "test: malicious forged baseline")
        commit = self.git(env["repo"], "rev-parse", "HEAD")
        packet = json.loads(env["packet_path"].read_text(encoding="utf-8"))
        packet.update(
            approved_git_commit=commit,
            policy_sha256=sha256_file(env["policy_path"]),
            executor_sha256=policy["executor"]["sha256"],
            validator_sha256=policy["validator"]["sha256"],
        )
        env["packet_path"].write_text(json.dumps(packet, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return commit

    def assert_hold_zero(self, result: dict) -> None:
        self.assertIn(result["status"], {"HOLD", "APPROVAL_REQUIRED"})
        self.assertEqual(result["run_task_call_count"], 0)

    def test_128_actual_executor_change_holds(self) -> None:
        env = self.make_repo("executor-change")
        env["executor"].write_text(env["executor"].read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        self.assert_hold_zero(self.run_boundary(env, "TA-128"))

    def test_129_actual_validator_change_holds(self) -> None:
        env = self.make_repo("validator-change")
        env["validator"].write_text(env["validator"].read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        self.assert_hold_zero(self.run_boundary(env, "TA-129"))

    def test_130_executor_and_policy_simultaneous_change_holds(self) -> None:
        env = self.make_repo("executor-policy-change")
        env["executor"].write_text(env["executor"].read_text(encoding="utf-8") + "\n# simultaneous\n", encoding="utf-8")
        policy = json.loads(env["policy_path"].read_text(encoding="utf-8"))
        policy["executor"]["sha256"] = sha256_file(env["executor"])
        env["policy_path"].write_text(json.dumps(policy, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        self.assert_hold_zero(self.run_boundary(env, "TA-130"))

    def test_131_validator_and_policy_simultaneous_change_holds(self) -> None:
        env = self.make_repo("validator-policy-change")
        env["validator"].write_text(env["validator"].read_text(encoding="utf-8") + "\n# simultaneous\n", encoding="utf-8")
        policy = json.loads(env["policy_path"].read_text(encoding="utf-8"))
        policy["validator"]["sha256"] = sha256_file(env["validator"])
        env["policy_path"].write_text(json.dumps(policy, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        self.assert_hold_zero(self.run_boundary(env, "TA-131"))

    def test_132_policy_approval_edit_cannot_self_issue(self) -> None:
        env = self.make_repo("policy-self-approval")
        policy = json.loads(env["policy_path"].read_text(encoding="utf-8"))
        policy["production"].update(approval_status="ISSUED", approval_ref=APPROVAL_REF)
        env["policy_path"].write_text(json.dumps(policy, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        self.assert_hold_zero(self.run_boundary(env, "TA-132"))

    def test_133_policy_path_substitution_holds(self) -> None:
        env = self.make_repo("policy-path")
        alternate = env["repo"] / "alternate-policy.json"
        shutil.copy2(env["policy_path"], alternate)
        packet = json.loads(env["packet_path"].read_text(encoding="utf-8"))
        packet["policy_path"] = "alternate-policy.json"
        packet["policy_sha256"] = sha256_file(alternate)
        env["packet_path"].write_text(json.dumps(packet, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        self.assert_hold_zero(self.run_boundary(env, "TA-133"))

    def test_134_policy_deleted_or_corrupt_holds(self) -> None:
        for label in ("deleted", "corrupt"):
            with self.subTest(label=label):
                env = self.make_repo(f"policy-{label}")
                if label == "deleted":
                    env["policy_path"].unlink()
                else:
                    env["policy_path"].write_text("{broken", encoding="utf-8")
                self.assert_hold_zero(self.run_boundary(env, f"TA-134-{label}"))

    def _genuine_pass(self, name: str, request_id: str) -> tuple[dict, dict]:
        env = self.make_repo(name)
        first = self.run_boundary(env, request_id, authorize=True)
        self.assertEqual((first["status"], first["decision"]), ("PASS", "PROCEED"))
        return env, first

    def test_135_executor_result_tamper_and_rehash_prevents_no_change(self) -> None:
        env, first = self._genuine_pass("result-tamper", "TA-135")
        evidence_dir = Path(first["evidence_dir"])
        result_path = evidence_dir / "runs" / first["core_result"]["run_id"] / "executor_result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["request_id"] = "FORGED"
        result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        events_path = evidence_dir / "events.jsonl"
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
        for event in events:
            if event["type"] == "CHECKPOINT_RECORDED":
                event["payload"]["state_sha256"] = sha256_file(result_path)
        events_path.write_text("".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events), encoding="utf-8")
        second = self.run_boundary(env, "TA-135")
        self.assertEqual((second["status"], second["decision"], second["run_task_call_count"]), ("HOLD", "HOLD", 0))

    def test_136_runs_directory_deleted_prevents_no_change(self) -> None:
        env, first = self._genuine_pass("runs-delete", "TA-136")
        shutil.rmtree(Path(first["evidence_dir"]) / "runs")
        second = self.run_boundary(env, "TA-136")
        self.assertEqual((second["status"], second["run_task_call_count"]), ("HOLD", 0))

    def test_137_checkpoint_sha_mismatch_prevents_no_change(self) -> None:
        env, first = self._genuine_pass("checkpoint-tamper", "TA-137")
        events_path = Path(first["evidence_dir"]) / "events.jsonl"
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
        for event in events:
            if event["type"] == "CHECKPOINT_RECORDED":
                event["payload"]["state_sha256"] = "0" * 64
        events_path.write_text("".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events), encoding="utf-8")
        second = self.run_boundary(env, "TA-137")
        self.assertEqual((second["status"], second["run_task_call_count"]), ("HOLD", 0))

    def test_138_validator_record_output_tamper_prevents_no_change(self) -> None:
        env, first = self._genuine_pass("validator-output-tamper", "TA-138")
        evidence_dir = Path(first["evidence_dir"])
        events_path = evidence_dir / "events.jsonl"
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
        for event in events:
            if event["type"] == "VALIDATION_RESULT":
                output = json.loads(event["payload"]["stdout"])
                output["run_id"] = "RUN-FORGED"
                event["payload"]["stdout"] = json.dumps(output, sort_keys=True) + "\n"
        events_path.write_text("".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events), encoding="utf-8")
        second = self.run_boundary(env, "TA-138")
        self.assertEqual((second["status"], second["run_task_call_count"]), ("HOLD", 0))

    def test_139_genuine_pass_is_no_change(self) -> None:
        env, _ = self._genuine_pass("genuine-pass", "TA-139")
        second = self.run_boundary(env, "TA-139")
        self.assertEqual((second["status"], second["decision"], second["run_task_call_count"]), ("NO_CHANGE", "NO_CHANGE", 0))

    def test_140_git_baseline_mismatch_holds(self) -> None:
        env = self.make_repo("baseline-mismatch")
        packet = json.loads(env["packet_path"].read_text(encoding="utf-8"))
        packet["approved_git_commit"] = "0" * 40
        env["packet_path"].write_text(json.dumps(packet, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        self.assert_hold_zero(self.run_boundary(env, "TA-140"))

    def test_141_uncommitted_runtime_file_change_holds(self) -> None:
        env = self.make_repo("uncommitted-runtime")
        env["policy_path"].write_text(env["policy_path"].read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self.assert_hold_zero(self.run_boundary(env, "TA-141"))

    def test_142_forged_packet_alone_cannot_authorize(self) -> None:
        env = self.make_repo("forged-packet-only")
        result = self.run_boundary(env, "FG-142")
        self.assertEqual((result["status"], result["reason"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", "FINAL_USER_GATE_REQUIRED", 0))
        self.assertFalse((env["repo"] / "04_Evidence/runtime/read_only_integrity").exists())

    def test_143_copied_or_modified_packet_cannot_authorize(self) -> None:
        env = self.make_repo("copied-packet")
        copied = env["packet_path"].with_name("COPIED-PACKET.json")
        shutil.copy2(env["packet_path"], copied)
        result = self.run_boundary(env, "FG-143")
        self.assertEqual((result["status"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))

    def test_144_malicious_commit_and_consistent_packet_without_gate_run_zero(self) -> None:
        env = self.make_repo("malicious-commit-packet")
        marker = self.work / "malicious-marker-144.txt"
        self.malicious_baseline(env, marker)
        prepared = self.prepare(env, self.request(env, "FG-144"))
        self.assertEqual(prepared["status"], "READY_FOR_FINAL_USER_GATE")
        result = self.run_boundary(env, "FG-144")
        self.assertEqual((result["status"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))
        self.assertFalse(marker.exists())

    def test_145_dangling_side_tag_commit_packet_without_gate_run_zero(self) -> None:
        env = self.make_repo("side-tag-commit")
        baseline = env["commit"]
        marker = self.work / "side-marker-145.txt"
        side_commit = self.malicious_baseline(env, marker)
        self.git(env["repo"], "tag", "forged-side", side_commit)
        self.git(env["repo"], "checkout", "--detach", baseline)
        blob = self.git(env["repo"], "show", f"{side_commit}:02_Core/beta_core/file_integrity_executor.py")
        env["executor"].write_text(blob, encoding="utf-8")
        policy_blob = self.git(env["repo"], "show", f"{side_commit}:{POLICY_RELATIVE_PATH}")
        env["policy_path"].write_text(policy_blob, encoding="utf-8")
        result = self.run_boundary(env, "FG-145")
        self.assertEqual((result["status"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))
        self.assertFalse(marker.exists())

    def test_146_combined_full_forgery_without_gate_run_zero(self) -> None:
        env = self.make_repo("combined-full-forgery")
        marker = self.work / "combined-marker-146.txt"
        self.malicious_baseline(env, marker)
        result = self.run_boundary(env, "FG-146", authorization={"approved": True})
        self.assertEqual((result["status"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))
        self.assertFalse(marker.exists())

    def test_147_arbitrary_boolean_or_string_never_authorizes(self) -> None:
        for number, authorization in enumerate((True, "approved", {"approved": True}), start=1):
            with self.subTest(authorization=authorization):
                env = self.make_repo(f"arbitrary-authorization-{number}")
                result = self.run_boundary(env, f"FG-147-{number}", authorization=authorization)
                self.assertEqual((result["status"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))

    def test_148_wrong_request_hash_authorization_run_zero(self) -> None:
        env = self.make_repo("wrong-request-hash")
        authorization = issue_fixture_user_gate_authorization(
            project_root=env["repo"],
            runtime_request_hash="0" * 64,
            runtime_code_baseline_hash="0" * 64,
            approved_git_commit=env["commit"],
            decision_ref="FIXTURE-USER-GATE-WRONG-HASH",
            production_simulation=True,
        )
        result = self.run_boundary(env, "FG-148", authorization=authorization)
        self.assertEqual((result["status"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))

    def test_149_exact_hash_fixture_gate_allows_one_isolated_execution(self) -> None:
        env = self.make_repo("exact-hash")
        result = self.run_boundary(env, "FG-149", authorize=True)
        self.assertEqual((result["status"], result["decision"], result["run_task_call_count"]), ("PASS", "PROCEED", 1))

    def test_150_payload_mutation_invalidates_prior_authorization(self) -> None:
        env = self.make_repo("payload-mutation")
        original = self.request(env, "FG-150-A")
        prepared = self.prepare(env, original)
        authorization = issue_fixture_user_gate_authorization(
            project_root=env["repo"],
            runtime_request_hash=prepared["runtime_request_hash"],
            runtime_code_baseline_hash=prepared["runtime_code_baseline_hash"],
            approved_git_commit=prepared["approved_git_commit"],
            decision_ref="FIXTURE-USER-GATE-PAYLOAD-MUTATION",
            production_simulation=True,
        )
        mutated_id = "FG-150-B"
        result = self.run_boundary(env, mutated_id, authorization=authorization)
        self.assertEqual((result["status"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))

    def test_151_consumed_authorization_replay_run_zero(self) -> None:
        env = self.make_repo("authorization-replay")
        request = self.request(env, "FG-151")
        prepared = self.prepare(env, request)
        authorization = issue_fixture_user_gate_authorization(
            project_root=env["repo"],
            runtime_request_hash=prepared["runtime_request_hash"],
            runtime_code_baseline_hash=prepared["runtime_code_baseline_hash"],
            approved_git_commit=prepared["approved_git_commit"],
            decision_ref="FIXTURE-USER-GATE-REPLAY",
            production_simulation=True,
        )
        first = self.run_boundary(env, "FG-151", authorization=authorization)
        self.assertEqual(first["status"], "PASS")
        shutil.rmtree(Path(first["evidence_dir"]))
        replay = self.run_boundary(env, "FG-151", authorization=authorization)
        self.assertEqual((replay["status"], replay["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))

    def test_152_packet_deleted_after_gate_preparation_cannot_authorize(self) -> None:
        env = self.make_repo("packet-deleted")
        request = self.request(env, "FG-152")
        prepared = self.prepare(env, request)
        authorization = issue_fixture_user_gate_authorization(
            project_root=env["repo"],
            runtime_request_hash=prepared["runtime_request_hash"],
            runtime_code_baseline_hash=prepared["runtime_code_baseline_hash"],
            approved_git_commit=prepared["approved_git_commit"],
            decision_ref="FIXTURE-USER-GATE-PACKET-DELETED",
            production_simulation=True,
        )
        env["packet_path"].unlink()
        result = self.run_boundary(env, "FG-152", authorization=authorization)
        self.assertEqual(result["run_task_call_count"], 0)

    def test_153_evidence_contract_links_gate_hash_commit_and_reference(self) -> None:
        env = self.make_repo("evidence-contract")
        result = self.run_boundary(env, "FG-153", authorize=True)
        body_path = Path(result["core_result"]["evidence"]["path"])
        body = json.loads(body_path.read_text(encoding="utf-8"))
        index = json.loads((Path(result["evidence_dir"]) / "evidence_index.jsonl").read_text(encoding="utf-8").strip())
        self.assertEqual(body["runtime_request_hash"], result["runtime_request_hash"])
        self.assertEqual(body["approved_git_commit"], env["commit"])
        self.assertEqual(body["user_gate_decision_ref"], "FIXTURE-USER-GATE-FG-153")
        self.assertEqual(index["runtime_request_hash"], body["runtime_request_hash"])
        self.assertEqual(index["approved_git_commit"], body["approved_git_commit"])
        self.assertEqual(index["user_gate_decision_ref"], body["user_gate_decision_ref"])

    def test_154_windows_slash_and_backslash_paths_canonicalize_equal(self) -> None:
        env = self.make_repo("path-normalization")
        request = self.request(env, "FG-154")
        request["approved_root"] = str(env["repo"].resolve()).replace("\\", "/")
        request["target_path"] = str(env["target"].resolve()).replace("\\", "/")
        prepared = self.prepare(env, request)
        self.assertEqual(prepared["status"], "READY_FOR_FINAL_USER_GATE")
        authorization = issue_fixture_user_gate_authorization(
            project_root=env["repo"],
            runtime_request_hash=prepared["runtime_request_hash"],
            runtime_code_baseline_hash=prepared["runtime_code_baseline_hash"],
            approved_git_commit=prepared["approved_git_commit"],
            decision_ref="FIXTURE-USER-GATE-PATH-NORMALIZATION",
            production_simulation=True,
        )
        evidence_root = env["repo"] / "04_Evidence/runtime/read_only_integrity"
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(boundary, "PROJECT_ROOT", env["repo"]))
            stack.enter_context(mock.patch.object(boundary, "APPROVED_ROOT", env["repo"]))
            stack.enter_context(mock.patch.object(boundary, "FIRST_RUNTIME_TARGET", env["target"]))
            stack.enter_context(mock.patch.object(boundary, "EVIDENCE_ROOT", evidence_root))
            result = boundary.execute_approved_request(request, authorization)
        self.assertEqual((result["status"], result["decision"]), ("PASS", "PROCEED"))

    def test_155_concurrent_same_authorization_allows_exactly_one_run(self) -> None:
        env = self.make_repo("atomic-two-thread")
        request_id = "ATOMIC-155"
        _, authorization = self.authorization(env, request_id)
        barrier = threading.Barrier(2)

        def invoke() -> dict:
            barrier.wait(timeout=5)
            return boundary.execute_approved_request(self.request(env, request_id), authorization)

        with self.boundary_patches(env), ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(invoke) for _ in range(2)]
            results = [future.result(timeout=30) for future in futures]
        self.assertEqual(sum(result.get("status") == "PASS" for result in results), 1)
        self.assertEqual(sum(result.get("run_task_call_count", 0) for result in results), 1)

    def test_156_artificial_claim_delay_still_consumes_once(self) -> None:
        env = self.make_repo("atomic-delay")
        prepared, authorization = self.authorization(env, "ATOMIC-156")
        original = user_gate_module._inspect_locked
        barrier = threading.Barrier(4)

        def delayed(*args, **kwargs):
            time.sleep(0.05)
            return original(*args, **kwargs)

        def claim():
            barrier.wait(timeout=5)
            return claim_user_gate_authorization(
                authorization,
                project_root=env["repo"],
                execution_context="PRODUCTION",
                runtime_request_hash=prepared["runtime_request_hash"],
                runtime_code_baseline_hash=prepared["runtime_code_baseline_hash"],
                approved_git_commit=prepared["approved_git_commit"],
            )

        with mock.patch.object(user_gate_module, "_inspect_locked", side_effect=delayed):
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = [future.result(timeout=10) for future in [pool.submit(claim) for _ in range(4)]]
        self.assertEqual(sum(not errors for _, errors in results), 1)
        self.assertEqual(sum(bool(errors) for _, errors in results), 3)

    def test_157_copy_deepcopy_and_pickle_are_rejected(self) -> None:
        env = self.make_repo("serialization")
        _, authorization = self.authorization(env, "ATOMIC-157")
        for operation in (lambda: copy.copy(authorization), lambda: copy.deepcopy(authorization), lambda: pickle.dumps(authorization)):
            with self.assertRaises(TypeError):
                operation()

    def test_158_claim_then_executor_replacement_executes_no_malicious_process(self) -> None:
        env = self.make_repo("claim-executor-swap")
        marker = self.work / "marker-158.txt"
        real_claim = core_cli.claim_user_gate_authorization

        def claim_then_swap(*args, **kwargs):
            result = real_claim(*args, **kwargs)
            if not result[1]:
                self.inject_marker(env["executor"], marker)
            return result

        with mock.patch.object(core_cli, "claim_user_gate_authorization", side_effect=claim_then_swap):
            result = self.run_boundary(env, "TOCTOU-158", authorize=True)
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(marker.exists())

    def test_159_policy_validation_then_executor_replacement_is_blocked(self) -> None:
        env = self.make_repo("policy-executor-swap")
        marker = self.work / "marker-159.txt"
        original = core_cli.validate_runtime_plan_policy
        swapped = False

        def validate_then_swap(*args, **kwargs):
            nonlocal swapped
            result = original(*args, **kwargs)
            if not swapped and not result[1]:
                swapped = True
                self.inject_marker(env["executor"], marker)
            return result

        with mock.patch.object(core_cli, "validate_runtime_plan_policy", side_effect=validate_then_swap):
            result = self.run_boundary(env, "TOCTOU-159", authorize=True)
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(marker.exists())

    def test_160_executor_then_validator_replacement_is_blocked(self) -> None:
        env = self.make_repo("executor-validator-swap")
        marker = self.work / "marker-160.txt"
        original = core_cli.run_executor

        def execute_then_swap(*args, **kwargs):
            result = original(*args, **kwargs)
            self.inject_marker(env["validator"], marker)
            return result

        with mock.patch.object(core_cli, "run_executor", side_effect=execute_then_swap):
            result = self.run_boundary(env, "TOCTOU-160", authorize=True)
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(marker.exists())

    def test_161_boundary_to_run_task_executor_replacement_is_blocked(self) -> None:
        env = self.make_repo("boundary-core-swap")
        marker = self.work / "marker-161.txt"
        original = boundary.run_task

        def swap_then_core(*args, **kwargs):
            self.inject_marker(env["executor"], marker)
            return original(*args, **kwargs)

        with mock.patch.object(boundary, "run_task", side_effect=swap_then_core):
            result = self.run_boundary(env, "TOCTOU-161", authorize=True)
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(marker.exists())

    def test_162_runtime_code_baseline_mismatch_requires_new_gate(self) -> None:
        env = self.make_repo("code-baseline-mismatch")
        _, authorization = self.authorization(env, "BASELINE-162")
        gate_path = env["repo"] / "02_Core" / "beta_core" / "gate.py"
        gate_path.write_text(gate_path.read_text(encoding="utf-8") + "\n# mutation\n", encoding="utf-8")
        result = self.run_boundary(env, "BASELINE-162", authorization=authorization)
        self.assertEqual((result["status"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))

    def test_163_request_and_code_baseline_are_linked_in_evidence(self) -> None:
        env = self.make_repo("baseline-evidence")
        result = self.run_boundary(env, "BASELINE-163", authorize=True)
        body = json.loads(Path(result["core_result"]["evidence"]["path"]).read_text(encoding="utf-8"))
        index = json.loads((Path(result["evidence_dir"]) / "evidence_index.jsonl").read_text(encoding="utf-8").strip())
        self.assertEqual(body["runtime_request_hash"], result["runtime_request_hash"])
        self.assertEqual(body["runtime_code_baseline_hash"], result["runtime_code_baseline_hash"])
        self.assertEqual(index["runtime_code_baseline_hash"], body["runtime_code_baseline_hash"])
        self.assertEqual(body["approved_git_commit"], env["commit"])

    def test_164_no_change_does_not_consume_new_authorization(self) -> None:
        env = self.make_repo("no-change-auth")
        first = self.run_boundary(env, "NOCHANGE-164", authorize=True)
        self.assertEqual(first["status"], "PASS")
        _, second_authorization = self.authorization(env, "NOCHANGE-164")
        duplicate = self.run_boundary(env, "NOCHANGE-164", authorization=second_authorization)
        self.assertEqual(duplicate["status"], "NO_CHANGE")
        shutil.rmtree(Path(first["evidence_dir"]))
        rerun = self.run_boundary(env, "NOCHANGE-164", authorization=second_authorization)
        self.assertEqual(rerun["status"], "PASS")

    def test_165_four_concurrent_same_requests_have_no_unhandled_exception(self) -> None:
        env = self.make_repo("atomic-four-thread")
        request_id = "ATOMIC-165"
        _, authorization = self.authorization(env, request_id)
        barrier = threading.Barrier(4)

        def invoke() -> dict:
            barrier.wait(timeout=5)
            return boundary.execute_approved_request(self.request(env, request_id), authorization)

        with self.boundary_patches(env), ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(invoke) for _ in range(4)]
            results = [future.result(timeout=30) for future in futures]
        self.assertEqual(sum(result.get("status") == "PASS" for result in results), 1)
        self.assertEqual(sum(result.get("run_task_call_count", 0) for result in results), 1)

    def test_166_verified_snapshot_runs_when_original_is_replaced_after_snapshot(self) -> None:
        env = self.make_repo("snapshot-original-swap")
        marker = self.work / "marker-166.txt"
        original = core_cli.run_executor

        def swap_original_after_snapshot(snapshot_path, *args, **kwargs):
            self.assertNotEqual(Path(snapshot_path).resolve(), env["executor"].resolve())
            self.inject_marker(env["executor"], marker)
            return original(snapshot_path, *args, **kwargs)

        with mock.patch.object(core_cli, "run_executor", side_effect=swap_original_after_snapshot):
            result = self.run_boundary(env, "TOCTOU-166", authorize=True)
        self.assertEqual(result["core_result"]["execution"], "PASS")
        self.assertFalse(marker.exists())

    def test_167_executor_snapshot_post_hash_mutation_executes_zero(self) -> None:
        env = self.make_repo("executor-snapshot-mutation")
        marker = self.work / "marker-167.txt"
        original = core_cli.run_executor

        def mutate_snapshot(snapshot_path, *args, **kwargs):
            self.inject_marker(Path(snapshot_path), marker)
            return original(snapshot_path, *args, **kwargs)

        with mock.patch.object(core_cli, "run_executor", side_effect=mutate_snapshot):
            result = self.run_boundary(env, "SNAPSHOT-167", authorize=True)
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(marker.exists())

    def test_168_validator_snapshot_post_hash_mutation_executes_zero(self) -> None:
        env = self.make_repo("validator-snapshot-mutation")
        marker = self.work / "marker-168.txt"
        original = core_cli.run_validator

        def mutate_snapshot(validator_id, snapshot_path, *args, **kwargs):
            self.inject_marker(Path(snapshot_path), marker)
            return original(validator_id, snapshot_path, *args, **kwargs)

        with mock.patch.object(core_cli, "run_validator", side_effect=mutate_snapshot):
            result = self.run_boundary(env, "SNAPSHOT-168", authorize=True)
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(marker.exists())

    def test_169_executor_snapshot_module_shadowing_is_blocked(self) -> None:
        env = self.make_repo("executor-shadow")
        marker = self.work / "marker-169.txt"
        original = core_cli.run_executor

        def add_shadow(snapshot_path, *args, **kwargs):
            Path(snapshot_path).with_name("json.py").write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('shadow')\n",
                encoding="utf-8",
            )
            return original(snapshot_path, *args, **kwargs)

        with mock.patch.object(core_cli, "run_executor", side_effect=add_shadow):
            result = self.run_boundary(env, "SNAPSHOT-169", authorize=True)
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(marker.exists())

    def test_170_validator_snapshot_module_shadowing_is_blocked(self) -> None:
        env = self.make_repo("validator-shadow")
        marker = self.work / "marker-170.txt"
        original = core_cli.run_validator

        def add_shadow(validator_id, snapshot_path, *args, **kwargs):
            Path(snapshot_path).with_name("json.py").write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('shadow')\n",
                encoding="utf-8",
            )
            return original(validator_id, snapshot_path, *args, **kwargs)

        with mock.patch.object(core_cli, "run_validator", side_effect=add_shadow):
            result = self.run_boundary(env, "SNAPSHOT-170", authorize=True)
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(marker.exists())

    def _assert_core_module_mutation_requires_new_gate(self, number: int, filename: str) -> None:
        env = self.make_repo(f"baseline-{number}-{filename.replace('.', '-')}")
        request_id = f"BASELINE-{number}"
        prepared, authorization = self.authorization(env, request_id)
        module = env["repo"] / "02_Core" / "beta_core" / filename
        module.write_text(module.read_text(encoding="utf-8") + "\n# post-gate mutation\n", encoding="utf-8")
        changed = self.prepare(env, self.request(env, request_id))
        self.assertNotEqual(changed["runtime_code_baseline_hash"], prepared["runtime_code_baseline_hash"])
        result = self.run_boundary(env, request_id, authorization=authorization)
        self.assertEqual((result["status"], result["run_task_call_count"]), ("APPROVAL_REQUIRED", 0))

    def test_171_model_change_is_in_runtime_code_baseline(self) -> None:
        self._assert_core_module_mutation_requires_new_gate(171, "model.py")

    def test_172_event_store_change_is_in_runtime_code_baseline(self) -> None:
        self._assert_core_module_mutation_requires_new_gate(172, "event_store.py")

    def test_173_package_init_change_is_in_runtime_code_baseline(self) -> None:
        self._assert_core_module_mutation_requires_new_gate(173, "__init__.py")

    def test_174_new_production_core_python_file_changes_baseline(self) -> None:
        env = self.make_repo("baseline-new-core-file")
        request = self.request(env, "BASELINE-174")
        before = self.prepare(env, request)
        new_module = env["repo"] / "02_Core" / "beta_core" / "new_runtime_module.py"
        new_module.write_text("VALUE = 'production core'\n", encoding="utf-8")
        after = self.prepare(env, request)
        self.assertNotEqual(after["runtime_code_baseline_hash"], before["runtime_code_baseline_hash"])
        self.assertIn(
            "02_Core/beta_core/new_runtime_module.py",
            {item["relative_path"] for item in after["runtime_code_baseline"]},
        )

    def test_175_snapshot_evidence_sha_and_event_linkage(self) -> None:
        env = self.make_repo("snapshot-evidence-linkage")
        result = self.run_boundary(env, "SNAPSHOT-175", authorize=True)
        body = json.loads(Path(result["core_result"]["evidence"]["path"]).read_text(encoding="utf-8"))
        index = json.loads((Path(result["evidence_dir"]) / "evidence_index.jsonl").read_text(encoding="utf-8").strip())
        events = [json.loads(line) for line in (Path(result["evidence_dir"]) / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        contracts = [body["executor_snapshot"], *body["validator_snapshots"]]
        self.assertEqual(index["executor_snapshot"], body["executor_snapshot"])
        self.assertEqual(index["validator_snapshots"], body["validator_snapshots"])
        self.assertEqual([event["payload"] for event in events if event["type"] == "EXECUTION_SNAPSHOT_RECORDED"], contracts)
        for contract in contracts:
            snapshot = Path(result["evidence_dir"]) / contract["relative_path"]
            self.assertEqual(sha256_file(snapshot), contract["sha256"])
            self.assertEqual(contract["lifecycle"], "PRESERVED_FOR_NO_CHANGE")
            self.assertIs(contract["python_isolated_mode"], True)

    def test_176_no_change_revalidates_preserved_snapshot_sha(self) -> None:
        env = self.make_repo("snapshot-no-change")
        result = self.run_boundary(env, "SNAPSHOT-176", authorize=True)
        duplicate = self.run_boundary(env, "SNAPSHOT-176")
        self.assertEqual(duplicate["status"], "NO_CHANGE")
        body = json.loads(Path(result["core_result"]["evidence"]["path"]).read_text(encoding="utf-8"))
        snapshot = Path(result["evidence_dir"]) / body["executor_snapshot"]["relative_path"]
        snapshot.write_text(snapshot.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
        blocked = self.run_boundary(env, "SNAPSHOT-176")
        self.assertEqual((blocked["status"], blocked["run_task_call_count"]), ("HOLD", 0))

    def test_177_snapshot_lifecycle_is_run_local_and_preserved(self) -> None:
        env = self.make_repo("snapshot-lifecycle")
        result = self.run_boundary(env, "SNAPSHOT-177", authorize=True)
        run_id = result["core_result"]["run_id"]
        snapshot_dir = Path(result["evidence_dir"]) / "runs" / run_id / "execution_snapshot"
        self.assertEqual(
            {path.name for path in snapshot_dir.iterdir()},
            {"executor.py", "validator-FILE-INTEGRITY-INDEPENDENT.py"},
        )
        self.assertTrue(all(path.is_file() for path in snapshot_dir.iterdir()))

    def test_178_unexpected_preserved_snapshot_sibling_blocks_no_change(self) -> None:
        env = self.make_repo("snapshot-unexpected-sibling")
        result = self.run_boundary(env, "SNAPSHOT-178", authorize=True)
        run_id = result["core_result"]["run_id"]
        snapshot_dir = Path(result["evidence_dir"]) / "runs" / run_id / "execution_snapshot"
        (snapshot_dir / "unexpected.py").write_text("raise SystemExit('must not run')\n", encoding="utf-8")
        blocked = self.run_boundary(env, "SNAPSHOT-178")
        self.assertEqual((blocked["status"], blocked["run_task_call_count"]), ("HOLD", 0))


if __name__ == "__main__":
    unittest.main()
