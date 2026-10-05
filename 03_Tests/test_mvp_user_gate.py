import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_Core"))
sys.path.insert(0, str(ROOT / "03_Tests/fixtures"))

from beta_core.cli import run_task  # noqa: E402
from beta_core.executor import run_executor  # noqa: E402
from beta_core.gate import decide_gate  # noqa: E402
from beta_core.validator_runner import run_validator  # noqa: E402
from user_gate_scenario_executor import (  # noqa: E402
    AUTO_KEYS,
    BASE_AUTO_KEYS,
    approved_context,
    decision_execution_entry,
    decide_user_gate,
    routing_entry,
    scenario_plan,
)


FIXTURES = ROOT / "03_Tests/fixtures"
PLAN = FIXTURES / "task_mvp_test_6_user_gate.json"
EXECUTOR = FIXTURES / "user_gate_scenario_executor.py"
VALIDATOR = FIXTURES / "user_gate_validator.py"


def criteria():
    return json.loads(PLAN.read_text(encoding="utf-8"))["required_validators"][0]["criteria"]


def prepare(temporary):
    result_path = Path(temporary) / "mvp_test_6/official/runs/PREP/executor_result.json"
    execution = run_executor(EXECUTOR, result_path, 20.0)
    if execution["status"] != "PASS":
        raise AssertionError(execution)
    return execution, result_path, json.loads(result_path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def assert_blocked(test, execution, result_path):
    validation = run_validator("VAL-MVP-TEST-6-USER-GATE", VALIDATOR, result_path, criteria(), 10.0)
    test.assertEqual(validation["status"], "FAIL")
    test.assertEqual(decide_gate(execution, [validation], evidence_recorded=True), "BLOCK")
    return json.loads(validation["stdout"])


class UserGateTests(unittest.TestCase):
    def test_54_scenarios_a_to_f(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "mvp_test_6/official", executor_timeout_seconds=20.0)
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("PASS", "PASS", "PROCEED"))

    def test_55_auto_requires_all_eight_conditions(self):
        context = approved_context(["fixture:test"], ["fixture:test"])
        context["postflight_possible"] = False
        result = decide_user_gate(context)
        self.assertEqual((result["decision"], result["reason_code"], result["side_effect_allowed"]), ("HOLD", "AUTO_CONDITIONS_INCOMPLETE", False))

    def test_56_approval_required_pre_side_effect_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            b_dir = Path(result["scenario_dirs"]["B"])
            events_path = b_dir / "events.jsonl"
            original = events_path.read_text(encoding="utf-8")
            fake = json.dumps({"type": "RUN_STARTED", "payload": {}, "task_id": "MUTATION-B"}, sort_keys=True)
            events_path.write_text(fake + "\n" + original, encoding="utf-8", newline="\n")
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario B pre-approval side effects must be zero", output["failures"])

    def test_57_hold_runtime_side_effect_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            c_dir = Path(result["delta_dirs"]["D5"])
            (c_dir / "runs/FAKE-RUN").mkdir(parents=True)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario C runtime side effects must be zero", output["failures"])

    def test_58_idempotent_duplicate_write_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            managed = Path(result["scenario_dirs"]["E"]) / "managed"
            write_json(managed / "EVD-duplicate.json", {"duplicate": True})
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario E filesystem changed on re-entry", output["failures"])

    def test_59_routing_mismatch_write_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            path = Path(result["scenario_dirs"]["F"]) / "routing_evidence.json"
            evidence = json.loads(path.read_text(encoding="utf-8"))
            evidence["beta_write_delta"] = 1
            write_json(path, evidence)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario F routing mismatch side effects must be zero", output["failures"])

    def test_60_unverified_failure_auto_fix_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            result["recovery"]["new_failure"].update({"decision": "AUTO_RECOVERY_ALLOWED", "automatic_fix_count": 1})
            write_json(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Recovery new_failure independent eligibility mismatch", output["failures"])

    def test_61_mutation_g_approval_boolean_cannot_bypass_and(self):
        context = {key: False for key in BASE_AUTO_KEYS}
        context["approval_granted"] = True
        result = decide_user_gate(context)
        self.assertEqual((result["decision"], result["side_effect_allowed"]), ("HOLD", False))

    def test_62_mutation_h_each_single_condition_blocks_auto(self):
        for missing in BASE_AUTO_KEYS:
            with self.subTest(missing=missing):
                context = approved_context(["fixture:test"], ["fixture:test"])
                context[missing] = False
                result = decide_user_gate(context)
                self.assertNotEqual(result["decision"], "AUTO")
                self.assertFalse(result["side_effect_allowed"])
        context = approved_context(["fixture:test"], ["fixture:expanded"])
        self.assertEqual(decide_user_gate(context)["decision"], "APPROVAL_REQUIRED")

    def test_63_mutation_i_prior_approval_cannot_cover_expanded_scope(self):
        context = approved_context(["fixture:read"], ["fixture:read", "fixture:write"])
        context["approval_granted"] = True
        result = decide_user_gate(context)
        self.assertEqual((result["decision"], result["side_effect_allowed"]), ("APPROVAL_REQUIRED", False))

    def test_64_mutation_j_real_rewrite_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            state_path = Path(result["scenario_dirs"]["E"]) / "managed/state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["status"] = "rewritten"
            write_json(state_path, state)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario E filesystem changed on re-entry", output["failures"])

    def test_65_mutation_k_fake_recovery_labels_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            result["recovery"]["new_failure"].update({
                "fingerprint_applicable": True,
                "prevention_verified": True,
                "scope_match": True,
                "fix_contract_valid": True,
                "postflight_possible": True,
                "decision": "AUTO_RECOVERY_ALLOWED",
            })
            write_json(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Recovery new_failure independent eligibility mismatch", output["failures"])

    def test_66_mutation_l_false_routing_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            path = Path(result["scenario_dirs"]["F"]) / "routing_evidence.json"
            evidence = json.loads(path.read_text(encoding="utf-8"))
            evidence.update({"routing_result": "MATCH", "mismatch_reason": None, "write_allowed": True})
            write_json(path, evidence)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario F routing independent recomputation mismatch", output["failures"])

    def test_67_mutation_m1_approval_required_never_enters_routing(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "m1"
            context = {**{key: True for key in BASE_AUTO_KEYS}, "request": {"requested_scope": ["fixture:M1"]}}
            decision = decide_user_gate(context)
            calls = []

            def forbidden(_measured_run_task):
                calls.append("called")

            gate, route, result = decision_execution_entry(decision, directory, "Codex", "Codex", forbidden)
            self.assertEqual(decision["decision"], "APPROVAL_REQUIRED")
            self.assertIsNone(route)
            self.assertIsNone(result)
            self.assertEqual(calls, [])
            self.assertTrue(all(gate[key] == 0 for key in (
                "routing_entry_call_count", "writer_call_count", "run_task_call_count",
                "downstream_call_count", "run_started_delta", "run_directory_delta",
                "runtime_evidence_delta", "managed_write_delta",
            )))

    def test_68_mutation_m2_hold_c3_false_never_enters_routing(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "m2"
            context = approved_context(["fixture:M2"], ["fixture:M2"])
            context["fixture_runtime_pass"] = False
            decision = decide_user_gate(context)
            gate, route, result = decision_execution_entry(
                decision, directory, "Codex", "Codex", lambda _runner: self.fail("HOLD entered routing"),
            )
            self.assertEqual(decision["decision"], "HOLD")
            self.assertIsNone(route)
            self.assertIsNone(result)
            self.assertEqual(gate["routing_entry_call_count"], 0)
            self.assertEqual(gate["managed_write_delta"], 0)

    def test_69_mutation_m3_scope_expansion_never_enters_routing(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "m3"
            context = approved_context(["fixture:read"], ["fixture:read", "fixture:write"])
            decision = decide_user_gate(context)
            gate, route, result = decision_execution_entry(
                decision, directory, "Codex", "Codex", lambda _runner: self.fail("scope expansion entered routing"),
            )
            self.assertEqual(decision["decision"], "APPROVAL_REQUIRED")
            self.assertIsNone(route)
            self.assertIsNone(result)
            self.assertEqual(gate["routing_entry_call_count"], 0)
            self.assertEqual(gate["run_task_call_count"], 0)

    def test_70_mutation_m4_removed_guard_actual_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            forced_dir = Path(result["delta_dirs"]["D4"])
            forced_dir.mkdir(parents=True)

            def forced_downstream(measured_run_task):
                plan_path = forced_dir / "forced_plan.json"
                write_json(plan_path, scenario_plan("M4"))
                return measured_run_task(plan_path, ROOT, forced_dir)

            routing_entry(forced_dir, "Codex", "Codex", "WRITE", forced_downstream)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Decision D4 non-AUTO execution side effects", output["failures"])


if __name__ == "__main__":
    unittest.main()
