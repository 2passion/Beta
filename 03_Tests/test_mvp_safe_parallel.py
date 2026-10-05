import hashlib
import json
import os
import shutil
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
from parallel_scenario_executor import classify, contract, execute_scenario, path_identity, task  # noqa: E402
from parallel_validator import path_identity as validator_path_identity  # noqa: E402
from parallel_validator import recompute  # noqa: E402


FIXTURES = ROOT / "03_Tests/fixtures"
PLAN = FIXTURES / "task_mvp_test_3_safe_parallel.json"
EXECUTOR = FIXTURES / "parallel_scenario_executor.py"
VALIDATOR = FIXTURES / "parallel_validator.py"


def criteria():
    return json.loads(PLAN.read_text(encoding="utf-8"))["required_validators"][0]["criteria"]


def write_json(path, value):
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
        {
            "scenario_id": path.relative_to(root).parts[0],
            "relative_path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]
    write_json(result_path, result)


def rewrite_evidence_hash(runtime_path, runtime):
    runtime["evidence_sha256"] = sha256_file(Path(runtime["evidence_path"]))
    write_json(runtime_path, runtime)


def prepare(temporary):
    result_path = Path(temporary) / "mvp_test_3/official/runs/PREP/executor_result.json"
    execution = run_executor(EXECUTOR, result_path, 20.0)
    if execution["status"] != "PASS":
        raise AssertionError(execution)
    return execution, result_path, json.loads(result_path.read_text(encoding="utf-8"))


def assert_blocked(test, execution, result_path):
    validation = run_validator("VAL-MVP-TEST-3-SAFE-PARALLEL", VALIDATOR, result_path, criteria(), 10.0)
    test.assertEqual(validation["status"], "FAIL")
    test.assertEqual(decide_gate(execution, [validation], evidence_recorded=True), "BLOCK")
    return json.loads(validation["stdout"])


def forge_decision(result_path, result, label, decision):
    directory = Path(result["scenario_dirs"][label])
    write_json(directory / "decision.json", decision)
    result["scenarios"][label]["decision"] = decision
    write_json(result_path, result)


class SafeParallelTests(unittest.TestCase):
    def test_83_scenarios_a_to_h(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "mvp_test_3/official", executor_timeout_seconds=20.0)
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("PASS", "PASS", "PROCEED"))

    def test_84_mutation_m1_hidden_dependency_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            forge_decision(result_path, result, "B", {"decision": "PARALLEL_ALLOWED", "reason_code": "INDEPENDENCE_PROVEN", "conflicts": []})
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario B decision independent recomputation mismatch", output["failures"])

    def test_85_mutation_m2_canonical_path_alias_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            forge_decision(result_path, result, "C", {"decision": "PARALLEL_ALLOWED", "reason_code": "INDEPENDENCE_PROVEN", "conflicts": []})
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario C decision independent recomputation mismatch", output["failures"])

    def test_86_mutation_m3_owner_forgery_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            forge_decision(result_path, result, "D", {"decision": "PARALLEL_ALLOWED", "reason_code": "INDEPENDENCE_PROVEN", "conflicts": []})
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario D decision independent recomputation mismatch", output["failures"])

    def test_87_mutation_m4_shared_resource_hidden_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            forge_decision(result_path, result, "E", {"decision": "PARALLEL_ALLOWED", "reason_code": "INDEPENDENCE_PROVEN", "conflicts": []})
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario E decision independent recomputation mismatch", output["failures"])

    def test_88_mutation_m5_fake_parallel_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            paths = sorted((Path(result["scenario_dirs"]["A"]) / "runtime").glob("*.json"))
            first, second = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
            second["started_ns"] = first["finished_ns"] + 1
            write_json(paths[1], second)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A actual concurrency overlap missing", output["failures"])

    def test_89_mutation_m6_unsafe_forced_parallel_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            forge_decision(result_path, result, "C", {"decision": "PARALLEL_ALLOWED", "reason_code": "FORCED", "conflicts": []})
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario C decision independent recomputation mismatch", output["failures"])

    def test_90_mutation_m7_failure_isolation_violation_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            path = Path(result["scenario_dirs"]["H"]) / "summary.json"
            summary = json.loads(path.read_text(encoding="utf-8"))
            summary["batch_result"] = "PASS"
            summary["recovery_candidates"] = []
            write_json(path, summary)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario H batch falsely passed", output["failures"])

    def test_91_mutation_m8_unknown_treated_independent_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            forge_decision(result_path, result, "G", {"decision": "PARALLEL_ALLOWED", "reason_code": "NO_VISIBLE_CONFLICT", "conflicts": []})
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario G decision independent recomputation mismatch", output["failures"])

    def test_92_mutation_m9_consistent_fake_parallel_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            runtime_paths = sorted((Path(result["scenario_dirs"]["A"]) / "runtime").glob("*.json"))
            runtimes = [json.loads(path.read_text(encoding="utf-8")) for path in runtime_paths]
            observation_path = Path(runtimes[1]["observation_path"])
            rows = [json.loads(line) for line in observation_path.read_text(encoding="utf-8").splitlines()]
            offset = runtimes[0]["finished_ns"] - rows[0]["observed_ns"] + 1
            for row in rows:
                row["observed_ns"] += offset
            observation_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")
            runtimes[1]["observation_sha256"] = sha256_file(observation_path)
            write_json(runtime_paths[1], runtimes[1])
            refresh_manifest(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A runtime/observation mismatch", output["failures"])
            self.assertIn("Scenario A independent observation overlap missing", output["failures"])

    def test_93_mutation_m10_unknown_required_values_never_parallel(self):
        mutations = {
            "none_routing": lambda contract: contract["tasks"][0].update({"routing_to": None}),
            "none_actor": lambda contract: contract["tasks"][0].update({"actual_actor": None}),
            "none_domain": lambda contract: contract["tasks"][0].update({"functional_domain": None}),
            "empty_domain": lambda contract: contract["tasks"][0].update({"functional_domain": ""}),
            "empty_scope": lambda contract: contract["tasks"][0].update({"requested_scope": []}),
            "unresolved_dependency": lambda contract: contract["tasks"][0].update({"depends_on": ["TASK-NOT-PRESENT"]}),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                execution, result_path, result = prepare(temporary)
                directory = Path(result["scenario_dirs"]["G"])
                contract = json.loads((Path(result["scenario_dirs"]["A"]) / "contract.json").read_text(encoding="utf-8"))
                mutate(contract)
                write_json(directory / "contract.json", contract)
                forged = {"decision": "PARALLEL_ALLOWED", "reason_code": "INDEPENDENCE_PROVEN", "conflicts": []}
                write_json(directory / "decision.json", forged)
                result["scenarios"]["G"]["decision"] = forged
                refresh_manifest(result_path, result)
                output = assert_blocked(self, execution, result_path)
                self.assertIn("Scenario G decision independent recomputation mismatch", output["failures"])

    def test_94_mutation_m11_uncertain_windows_alias_never_parallel(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            path = Path(result["scenario_dirs"]["C"]) / "path_cases.json"
            cases = json.loads(path.read_text(encoding="utf-8"))
            target = next(case for case in cases if case["name"] == "ads")
            target["decision"] = {"decision": "PARALLEL_ALLOWED", "reason_code": "INDEPENDENCE_PROVEN", "conflicts": []}
            write_json(path, cases)
            refresh_manifest(result_path, result)
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario C Windows path policy mismatch", output["failures"])

    def test_95_mutation_m12_task_run_output_validation_evidence_link_fails(self):
        attacks = ("shared_run_id", "forged_output_sha", "status_contradiction", "evidence_identity")
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as temporary:
                execution, result_path, result = prepare(temporary)
                directory = Path(result["scenario_dirs"]["A"])
                runtime_paths = sorted((directory / "runtime").glob("*.json"))
                runtimes = [json.loads(path.read_text(encoding="utf-8")) for path in runtime_paths]
                runtime = runtimes[1]
                if attack == "shared_run_id":
                    runtime["run_id"] = runtimes[0]["run_id"]
                    write_json(runtime_paths[1], runtime)
                    expected = "Scenario A run_id must be unique"
                elif attack == "forged_output_sha":
                    evidence_path = Path(runtime["evidence_path"])
                    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                    evidence["output_sha256"] = "0" * 64
                    write_json(evidence_path, evidence)
                    rewrite_evidence_hash(runtime_paths[1], runtime)
                    expected = "Scenario A Evidence linkage mismatch"
                elif attack == "status_contradiction":
                    output_path = Path(runtime["output_path"])
                    output = json.loads(output_path.read_text(encoding="utf-8"))
                    output["status"] = "failed"
                    write_json(output_path, output)
                    runtime["output_sha256"] = sha256_file(output_path)
                    evidence_path = Path(runtime["evidence_path"])
                    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                    evidence["output_sha256"] = runtime["output_sha256"]
                    write_json(evidence_path, evidence)
                    rewrite_evidence_hash(runtime_paths[1], runtime)
                    expected = "Scenario A output/validation contradiction"
                else:
                    evidence_path = Path(runtime["evidence_path"])
                    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                    evidence["task_id"] = "TASK-TAMPERED"
                    write_json(evidence_path, evidence)
                    rewrite_evidence_hash(runtime_paths[1], runtime)
                    expected = "Scenario A evidence identity mismatch"
                refresh_manifest(result_path, result)
                output = assert_blocked(self, execution, result_path)
                self.assertIn(expected, output["failures"])

    def test_96_mutation_m13_manifest_content_add_delete_fails(self):
        attacks = ("content", "add", "delete")
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as temporary:
                execution, result_path, result = prepare(temporary)
                root = Path(result["scenario_root"])
                if attack == "content":
                    path = root / "B" / "cycle_decision.json"
                    value = json.loads(path.read_text(encoding="utf-8"))
                    value["reason_code"] = "TAMPERED"
                    write_json(path, value)
                elif attack == "add":
                    write_json(root / "A" / "unregistered.json", {"tampered": True})
                else:
                    (root / "C" / "summary.json").unlink()
                output = assert_blocked(self, execution, result_path)
                self.assertIn("Scenario manifest mismatch or unlinked file", output["failures"])

    def test_97_mutation_m14_full_fake_parallel_fails_filesystem_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            execution, result_path, result = prepare(temporary)
            directory = Path(result["scenario_dirs"]["A"])
            runtime_paths = sorted((directory / "runtime").glob("*.json"))
            records = [json.loads(path.read_text(encoding="utf-8")) for path in runtime_paths]
            replay: list[tuple[Path, bytes]] = []
            for record, runtime_path in zip(records, runtime_paths):
                paths = [
                    Path(record["output_path"]),
                    Path(record["validation_path"]),
                    Path(record["evidence_path"]),
                    Path(record["observation_path"]),
                    runtime_path,
                ]
                replay.extend((path, path.read_bytes()) for path in paths)
            stamp = 1_800_000_000_000_000_000
            for path, payload in replay:
                path.write_bytes(payload)
                os.utime(path, ns=(stamp, stamp))
                stamp += 10_000_000
            output = assert_blocked(self, execution, result_path)
            self.assertIn("Scenario A filesystem stage interleaving missing", output["failures"])

    def test_98_mutation_m15_hold_conditions_precede_unknown_path(self):
        mutations = {
            "scope": (lambda value: value["tasks"][0].update({"requested_scope": ["fixture:outside"]}), "APPROVAL_SCOPE_REQUIRED"),
            "routing": (lambda value: value["tasks"][0].update({"actual_actor": "Claude-Code"}), "ROUTING_MISMATCH"),
            "validation": (lambda value: value["tasks"][0].update({"validation_independent": False}), "INDEPENDENT_VALIDATION_UNKNOWN"),
            "cycle": (lambda value: (value["tasks"][0].update({"depends_on": [value["tasks"][1]["task_id"]]}), value["tasks"][1].update({"depends_on": [value["tasks"][0]["task_id"]]})), "DEPENDENCY_CYCLE"),
            "owner": (lambda value: value["tasks"][0].update({"write_owner": "Codex,Claude"}), "OWNERSHIP_CONFLICT"),
        }
        for name, (mutate, reason) in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                execution, result_path, result = prepare(temporary)
                source = Path(result["scenario_dirs"]["A"]) / "contract.json"
                value = json.loads(source.read_text(encoding="utf-8"))
                value["tasks"][0]["write_set"] = [r"relative\unknown.json"]
                mutate(value)
                directory = Path(result["scenario_dirs"]["G"])
                shutil.rmtree(directory)
                summary = execute_scenario(directory, value)
                self.assertEqual(summary["decision"], {"decision": "HOLD", "reason_code": reason})
                self.assertEqual(summary["execution_count"], 0)
                self.assertFalse((directory / "runtime").exists())
                self.assertFalse((directory / "outputs").exists())
                result["scenarios"]["G"] = summary
                refresh_manifest(result_path, result)
                validation = run_validator("VAL-MVP-TEST-3-SAFE-PARALLEL", VALIDATOR, result_path, criteria(), 10.0)
                self.assertEqual(validation["status"], "PASS", validation)
                self.assertEqual(decide_gate(execution, [validation], evidence_recorded=True), "PROCEED")

    def test_99_mutation_m16_unsafe_windows_paths_never_parallel(self):
        unsafe = [
            r"C:\Beta\parallel\*.json",
            r"C:\Beta\parallel\NUL",
            r"C:\Beta\parallel\NUL.json",
            r"C:\Beta\parallel\COM1",
            r"C:\Beta\parallel\COM1.txt",
            "Ｃ:\\Beta\\parallel\\target.json",
        ]
        for index, path in enumerate(unsafe):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temporary:
                value = contract([
                    task(f"M16-{index}-1", "Codex-A", [path], f"m16-{index}-a"),
                    task(f"M16-{index}-2", "Codex-B", [fr"C:\Beta\parallel\safe-{index}.json"], f"m16-{index}-b"),
                ])
                self.assertEqual(path_identity(path)[0], "UNKNOWN")
                self.assertEqual(validator_path_identity(path)[0], "UNKNOWN")
                self.assertNotEqual(classify(value)["decision"], "PARALLEL_ALLOWED")
                self.assertEqual(classify(value), recompute(value))
                summary = execute_scenario(Path(temporary) / f"unsafe-{index}", value)
                self.assertNotEqual(summary["decision"]["decision"], "PARALLEL_ALLOWED")
        control = contract([
            task("M16-CONTROL-1", "Codex-A", [r"C:\Beta\parallel\left.json"], "m16-control-a"),
            task("M16-CONTROL-2", "Codex-B", [r"C:\Beta\parallel\right.json"], "m16-control-b"),
        ])
        self.assertEqual(classify(control)["decision"], "PARALLEL_ALLOWED")
        self.assertEqual(classify(control), recompute(control))

    def test_100_mutation_m17_invalid_owner_identifier_holds_without_execution(self):
        invalid = ["Codex,Claude", "Codex Claude", "Codex/Claude", " Codex", "Co+dex", "-Codex", ""]
        for index, owner in enumerate(invalid):
            with self.subTest(owner=owner), tempfile.TemporaryDirectory() as temporary:
                value = contract([
                    task(f"M17-{index}-1", owner, [fr"C:\Beta\parallel\owner-{index}-a.json"], f"m17-{index}-a"),
                    task(f"M17-{index}-2", "Codex-B", [fr"C:\Beta\parallel\owner-{index}-b.json"], f"m17-{index}-b"),
                ])
                expected = {"decision": "HOLD", "reason_code": "OWNERSHIP_CONFLICT"}
                self.assertEqual(classify(value), expected)
                self.assertEqual(recompute(value), expected)
                directory = Path(temporary) / f"owner-{index}"
                summary = execute_scenario(directory, value)
                self.assertEqual(summary["decision"], expected)
                self.assertEqual(summary["execution_count"], 0)
                self.assertFalse((directory / "runtime").exists())
                self.assertFalse((directory / "outputs").exists())


if __name__ == "__main__":
    unittest.main()
