"""Independent validator for MVP Test 3 Safe Parallel."""

from __future__ import annotations

import hashlib
import json
import ntpath
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "02_Core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from beta_core.model import OWNER_PATTERN


REQUIRED_TASK_FIELDS = {
    "task_id", "depends_on", "write_owner", "write_set", "functional_domain",
    "shared_mutable_resources", "requested_scope", "routing_to", "actual_actor", "validation_independent",
}

RESERVED_DOS_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{index}" for index in range(1, 10)), *(f"LPT{index}" for index in range(1, 10))}


class MetadataResolutionError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def path_identity(path: Any) -> tuple[str, str | None]:
    if not isinstance(path, str) or not path.strip():
        return "UNKNOWN", None
    value = path.replace("/", "\\")
    if value.startswith("\\\\.\\") or value.startswith("\\\\") and not value.startswith("\\\\?\\"):
        return "UNKNOWN", None
    if value.startswith("\\\\?\\"):
        value = value[4:]
    if "*" in value or "?" in value or any(ord(character) > 127 for character in value):
        return "UNKNOWN", None
    drive, tail = ntpath.splitdrive(value)
    if not drive or not tail.startswith("\\") or "~" in value or any(":" in part for part in tail.split("\\")):
        return "UNKNOWN", None
    parts = [part if part == ".." else part.rstrip(" .") for part in tail.split("\\") if part not in ("", ".")]
    if any(not part or part.split(".", 1)[0].upper() in RESERVED_DOS_NAMES for part in parts):
        return "UNKNOWN", None
    return "KNOWN", ntpath.normcase(ntpath.normpath(drive + "\\" + "\\".join(parts)))


def overlap(left: str, right: str) -> bool:
    left_status, a = path_identity(left)
    right_status, b = path_identity(right)
    if left_status != "KNOWN" or right_status != "KNOWN" or a is None or b is None:
        return False
    return a == b or a.startswith(b.rstrip("\\") + "\\") or b.startswith(a.rstrip("\\") + "\\")


def cycle(tasks: list[dict[str, Any]]) -> bool:
    graph = {task["task_id"]: set(task["depends_on"]) for task in tasks}
    active: set[str] = set()
    done: set[str] = set()

    def visit(node: str) -> bool:
        if node in active:
            return True
        if node in done:
            return False
        active.add(node)
        if any(dependency in graph and visit(dependency) for dependency in graph.get(node, set())):
            return True
        active.remove(node)
        done.add(node)
        return False

    return any(visit(node) for node in graph)


def recompute(contract: dict[str, Any]) -> dict[str, Any]:
    tasks = contract.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 2 or any(not isinstance(task, dict) or not REQUIRED_TASK_FIELDS.issubset(task) for task in tasks):
        return {"decision": "HOLD", "reason_code": "INDEPENDENCE_UNKNOWN"}
    if any(not isinstance(task["task_id"], str) or not task["task_id"].strip() or not isinstance(task["depends_on"], list) or not isinstance(task["write_set"], list) or not task["write_set"] or not all(isinstance(path, str) and path.strip() for path in task["write_set"]) for task in tasks):
        return {"decision": "HOLD", "reason_code": "INDEPENDENCE_UNKNOWN"}
    if any(not isinstance(task["write_owner"], str) or OWNER_PATTERN.fullmatch(task["write_owner"]) is None for task in tasks):
        return {"decision": "HOLD", "reason_code": "OWNERSHIP_CONFLICT"}
    if len({task["task_id"] for task in tasks}) != 2 or any(isinstance(task.get("writers"), list) and len(task["writers"]) != 1 for task in tasks):
        return {"decision": "HOLD", "reason_code": "OWNERSHIP_CONFLICT"}
    if any(not isinstance(task["functional_domain"], str) or not task["functional_domain"].strip() or not isinstance(task["shared_mutable_resources"], list) or not all(isinstance(item, str) and item for item in task["shared_mutable_resources"]) or not isinstance(task["requested_scope"], list) or not task["requested_scope"] or not all(isinstance(item, str) and item for item in task["requested_scope"]) or not isinstance(task["routing_to"], str) or not task["routing_to"] or not isinstance(task.get("actual_actor"), str) or not task.get("actual_actor") for task in tasks):
        return {"decision": "HOLD", "reason_code": "INDEPENDENCE_UNKNOWN"}
    if not isinstance(contract.get("approved_scope"), list) or not contract["approved_scope"] or not all(isinstance(item, str) and item for item in contract["approved_scope"]):
        return {"decision": "HOLD", "reason_code": "INDEPENDENCE_UNKNOWN"}
    ids = {task["task_id"] for task in tasks}
    completed_dependencies = contract.get("completed_dependencies", [])
    if not isinstance(completed_dependencies, list) or not all(isinstance(item, str) and item for item in completed_dependencies):
        return {"decision": "HOLD", "reason_code": "INDEPENDENCE_UNKNOWN"}
    if cycle(tasks):
        return {"decision": "HOLD", "reason_code": "DEPENDENCY_CYCLE"}
    completed = set(completed_dependencies)
    if any(not isinstance(dep, str) or not dep or dep not in ids | completed for task in tasks for dep in task["depends_on"]):
        return {"decision": "HOLD", "reason_code": "DEPENDENCY_UNRESOLVED"}
    approved = set(contract.get("approved_scope", []))
    if any(not set(task["requested_scope"]).issubset(approved) for task in tasks):
        return {"decision": "HOLD", "reason_code": "APPROVAL_SCOPE_REQUIRED"}
    if any(task.get("routing_to") != task.get("actual_actor") for task in tasks):
        return {"decision": "HOLD", "reason_code": "ROUTING_MISMATCH"}
    if any(task["validation_independent"] is not True for task in tasks):
        return {"decision": "HOLD", "reason_code": "INDEPENDENT_VALIDATION_UNKNOWN"}
    conflicts: list[str] = []
    if any(set(task["depends_on"]) & ids for task in tasks):
        conflicts.append("DEPENDENCY_CONFLICT")
    if tasks[0]["write_owner"] == tasks[1]["write_owner"]:
        conflicts.append("OWNER_CONTEXT_CONFLICT")
    if any(overlap(left, right) for left in tasks[0]["write_set"] for right in tasks[1]["write_set"]):
        conflicts.append("WRITE_SET_CONFLICT")
    if any(path_identity(path)[0] != "KNOWN" for task in tasks for path in task["write_set"]):
        conflicts.append("WRITE_PATH_UNKNOWN")
    if tasks[0]["functional_domain"] == tasks[1]["functional_domain"]:
        conflicts.append("FUNCTIONAL_DOMAIN_CONFLICT")
    if set(tasks[0]["shared_mutable_resources"]) & set(tasks[1]["shared_mutable_resources"]):
        conflicts.append("SHARED_MUTABLE_RESOURCE")
    return {"decision": "SEQUENTIAL_REQUIRED", "reason_code": conflicts[0], "conflicts": conflicts} if conflicts else {"decision": "PARALLEL_ALLOWED", "reason_code": "INDEPENDENCE_PROVEN", "conflicts": []}


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def runtime_records(directory: Path) -> list[dict[str, Any]]:
    return [read_json(path) for path in sorted((directory / "runtime").glob("*.json"))] if (directory / "runtime").is_dir() else []


def validate_artifact(record: dict[str, Any], failures: list[str], label: str) -> None:
    for prefix in ("output", "validation", "evidence"):
        path = Path(str(record.get(f"{prefix}_path", "")))
        require(path.is_file(), f"Scenario {label} {prefix} missing", failures)
        if path.is_file():
            require(sha256_file(path) == record.get(f"{prefix}_sha256"), f"Scenario {label} {prefix} SHA mismatch", failures)
    validation_path = Path(str(record.get("validation_path", "")))
    evidence_path = Path(str(record.get("evidence_path", "")))
    if validation_path.is_file() and evidence_path.is_file():
        validation, evidence = read_json(validation_path), read_json(evidence_path)
        require(validation.get("task_id") == record.get("task_id") and validation.get("run_id") == record.get("run_id"), f"Scenario {label} validation identity mismatch", failures)
        require(evidence.get("task_id") == record.get("task_id") and evidence.get("run_id") == record.get("run_id"), f"Scenario {label} evidence identity mismatch", failures)
        require(validation.get("status") == record.get("validation_status") == evidence.get("validation_status"), f"Scenario {label} validation result mismatch", failures)
        output = read_json(Path(record["output_path"]))
        expected_output = "completed" if validation.get("status") == "PASS" else "failed"
        require(output.get("task_id") == record.get("task_id") and output.get("run_id") == record.get("run_id") and output.get("status") == expected_output, f"Scenario {label} output/validation contradiction", failures)
        require(evidence.get("output_sha256") == sha256_file(Path(record["output_path"])) and evidence.get("validation_sha256") == sha256_file(validation_path), f"Scenario {label} Evidence linkage mismatch", failures)


def validate_parallel(directory: Path, expected_statuses: dict[str, str], failures: list[str], label: str) -> None:
    records = runtime_records(directory)
    require(len(records) == 2, f"Scenario {label} parallel execution count mismatch", failures)
    if len(records) != 2:
        return
    require(len({record.get("thread_id") for record in records}) == 2, f"Scenario {label} worker identity not concurrent", failures)
    require(len({record.get("run_id") for record in records}) == 2, f"Scenario {label} run_id must be unique", failures)
    require(len({record.get("barrier_token") for record in records}) == 1 and records[0].get("barrier_token"), f"Scenario {label} barrier evidence missing", failures)
    require(max(record.get("started_ns", 0) for record in records) < min(record.get("finished_ns", 0) for record in records), f"Scenario {label} actual concurrency overlap missing", failures)
    require(all(record.get("started_ns", 0) <= record.get("barrier_passed_ns", 0) <= record.get("finished_ns", 0) for record in records), f"Scenario {label} barrier ordering invalid", failures)
    observed = []
    for record in records:
        path = Path(str(record.get("observation_path", "")))
        require(path.is_file() and sha256_file(path) == record.get("observation_sha256"), f"Scenario {label} worker observation missing or changed", failures)
        if path.is_file():
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            require([row.get("type") for row in rows] == ["WORKER_STARTED", "BARRIER_ARRIVED", "BARRIER_RELEASED", "WORKER_COMPLETED"], f"Scenario {label} worker observation sequence invalid", failures)
            require(all(row.get("task_id") == record.get("task_id") and row.get("run_id") == record.get("run_id") and row.get("sync_token") == record.get("barrier_token") for row in rows), f"Scenario {label} worker observation identity mismatch", failures)
            if len(rows) == 4:
                require([rows[0]["observed_ns"], rows[1]["observed_ns"], rows[2]["observed_ns"], rows[3]["observed_ns"]] == [record.get("started_ns"), record.get("barrier_arrived_ns"), record.get("barrier_passed_ns"), record.get("finished_ns")], f"Scenario {label} runtime/observation mismatch", failures)
                require(rows[0].get("worker_id") == record.get("thread_id"), f"Scenario {label} worker identity mismatch", failures)
                observed.append(rows)
    if len(observed) == 2:
        require(max(rows[0]["observed_ns"] for rows in observed) < min(rows[3]["observed_ns"] for rows in observed), f"Scenario {label} independent observation overlap missing", failures)
    metadata: list[dict[str, int]] = []
    for record in records:
        paths = {name: Path(str(record.get(f"{name}_path", ""))) for name in ("output", "validation", "evidence")}
        if not all(path.is_file() for path in paths.values()):
            continue
        times = {name: path.stat().st_mtime_ns for name, path in paths.items()}
        observation_path = Path(str(record.get("observation_path", "")))
        runtime_path = directory / "runtime" / f"{record.get('task_id')}.json"
        if observation_path.is_file() and runtime_path.is_file():
            times["observation"] = observation_path.stat().st_mtime_ns
            times["runtime"] = runtime_path.stat().st_mtime_ns
        metadata.append(times)
        require(times["output"] < times["validation"] < times["evidence"], f"Scenario {label} filesystem per-task ordering invalid", failures)
        if "observation" in times:
            require(times["evidence"] < times["observation"] <= times["runtime"], f"Scenario {label} filesystem completion ordering invalid", failures)
    if len(metadata) == 2:
        output_max = max(item["output"] for item in metadata)
        validation_min = min(item["validation"] for item in metadata)
        validation_max = max(item["validation"] for item in metadata)
        evidence_min = min(item["evidence"] for item in metadata)
        if output_max == validation_min or validation_max == evidence_min:
            raise MetadataResolutionError(f"Scenario {label} filesystem timestamp resolution insufficient")
        require(output_max < validation_min and validation_max < evidence_min, f"Scenario {label} filesystem stage interleaving missing", failures)
    require({record["task_id"]: record.get("validation_status") for record in records} == expected_statuses, f"Scenario {label} per-task validation mismatch", failures)
    for record in records:
        validate_artifact(record, failures, label)


def validate_sequential(directory: Path, contract: dict[str, Any], failures: list[str], label: str) -> None:
    records = runtime_records(directory)
    require(len(records) == 2, f"Scenario {label} sequential execution count mismatch", failures)
    if len(records) != 2:
        return
    ordered = sorted(records, key=lambda record: record["started_ns"])
    require(len({record.get("run_id") for record in records}) == 2, f"Scenario {label} run_id must be unique", failures)
    require(ordered[0]["finished_ns"] <= ordered[1]["started_ns"], f"Scenario {label} concurrent write occurred", failures)
    tasks = contract["tasks"]
    dependency_order = [task["task_id"] for task in tasks if not task["depends_on"]] + [task["task_id"] for task in tasks if task["depends_on"]]
    expected = dependency_order if any(task["depends_on"] for task in tasks) else sorted(task["task_id"] for task in tasks)
    require([record["task_id"] for record in ordered] == expected, f"Scenario {label} deterministic fallback order mismatch", failures)
    for record in records:
        validate_artifact(record, failures, label)


def actual_manifest(root: Path) -> list[dict[str, str]]:
    return [{"scenario_id": path.relative_to(root).parts[0], "relative_path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)} for path in sorted(root.rglob("*")) if path.is_file()]


def validate(result: dict[str, Any], criteria: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    require(result.get("mvp_test_id") == criteria.get("mvp_test_id"), "MVP Test identity mismatch", failures)
    require(result.get("plan_version") == criteria.get("test_plan_version"), "Plan version mismatch", failures)
    dirs = {key: Path(value) for key, value in result.get("scenario_dirs", {}).items()}
    require(set(dirs) == set("ABCDEFGH"), "Scenario A-H directories missing", failures)
    if set(dirs) != set("ABCDEFGH"):
        return failures
    decisions: dict[str, dict[str, Any]] = {}
    contracts: dict[str, dict[str, Any]] = {}
    for label, directory in dirs.items():
        contract = read_json(directory / "contract.json")
        reported = read_json(directory / "decision.json")
        expected = recompute(contract)
        contracts[label], decisions[label] = contract, expected
        require(reported == expected, f"Scenario {label} decision independent recomputation mismatch", failures)
        require(result["scenarios"][label]["decision"] == expected, f"Scenario {label} result decision mismatch", failures)
        records = runtime_records(directory)
        require(all(record.get("task_id") in {task["task_id"] for task in contract.get("tasks", [])} for record in records), f"Scenario {label} runtime task not in contract", failures)
    require(decisions["A"]["decision"] == "PARALLEL_ALLOWED", "Scenario A was not independently safe", failures)
    validate_parallel(dirs["A"], {"TASK-A1": "PASS", "TASK-A2": "PASS"}, failures, "A")
    require(decisions["B"]["reason_code"] == "DEPENDENCY_CONFLICT", "Scenario B dependency conflict missing", failures)
    validate_sequential(dirs["B"], contracts["B"], failures, "B")
    cycle_contract = read_json(dirs["B"] / "cycle_contract.json")
    cycle_decision = read_json(dirs["B"] / "cycle_decision.json")
    require(recompute(cycle_contract) == cycle_decision == {"decision": "HOLD", "reason_code": "DEPENDENCY_CYCLE"}, "Scenario B dependency cycle not held", failures)
    require(decisions["C"]["reason_code"] == "WRITE_SET_CONFLICT", "Scenario C canonical path conflict missing", failures)
    validate_sequential(dirs["C"], contracts["C"], failures, "C")
    path_cases = read_json(dirs["C"] / "path_cases.json")
    require(all(recompute(case["contract"]) == case["decision"] and (case["decision"]["decision"] == "PARALLEL_ALLOWED") == (case["name"] == "sibling-control") for case in path_cases), "Scenario C Windows path policy mismatch", failures)
    require(decisions["D"] == {"decision": "HOLD", "reason_code": "OWNERSHIP_CONFLICT"} and not runtime_records(dirs["D"]), "Scenario D ownership HOLD execution mismatch", failures)
    d_summary = read_json(dirs["D"] / "summary.json")
    require(all(case.get("decision") == {"decision": "HOLD", "reason_code": "OWNERSHIP_CONFLICT"} for case in d_summary.get("owner_cases", [])) and len(d_summary.get("owner_cases", [])) == 7, "Scenario D invalid owner contract mismatch", failures)
    require(d_summary.get("owner_control", {}).get("decision") == "PARALLEL_ALLOWED", "Scenario D valid owner control mismatch", failures)
    require(decisions["E"]["reason_code"] == "SHARED_MUTABLE_RESOURCE", "Scenario E shared resource conflict missing", failures)
    validate_sequential(dirs["E"], contracts["E"], failures, "E")
    require(decisions["F"]["decision"] == "HOLD" and decisions["F"]["reason_code"] in {"APPROVAL_SCOPE_REQUIRED", "ROUTING_MISMATCH"} and not runtime_records(dirs["F"]), "Scenario F permission/routing HOLD mismatch", failures)
    require(decisions["G"].get("decision") == "HOLD" and not runtime_records(dirs["G"]), "Scenario G unknown independence mismatch", failures)
    require(decisions["H"]["decision"] == "PARALLEL_ALLOWED", "Scenario H was not independently safe", failures)
    validate_parallel(dirs["H"], {"TASK-H1": "PASS", "TASK-H2": "FAIL"}, failures, "H")
    h_summary = read_json(dirs["H"] / "summary.json")
    h_statuses = {record["task_id"]: read_json(Path(record["validation_path"]))["status"] for record in runtime_records(dirs["H"])}
    derived_batch = "PASS" if all(status == "PASS" for status in h_statuses.values()) else "PARTIAL_FAILURE"
    derived_recovery = sorted(task_id for task_id, status in h_statuses.items() if status != "PASS")
    require(h_summary.get("batch_result") == derived_batch, "Scenario H batch falsely passed", failures)
    require(h_summary.get("recovery_candidates") == derived_recovery, "Scenario H recovery isolation mismatch", failures)
    require(sum(record["task_id"] == "TASK-H1" for record in runtime_records(dirs["H"])) == 1, "Scenario H PASS task reran", failures)
    actual_evidence = len(list(Path(result["scenario_root"]).rglob("evidence/*.json")))
    require(result.get("scenario_evidence_count") == actual_evidence, "Scenario evidence count mismatch", failures)
    require(result.get("ownership_reuse", {}).get("source") == "beta_core.model.OWNER_PATTERN" and result.get("ownership_reuse", {}).get("pattern") == OWNER_PATTERN.pattern, "Ownership reuse evidence missing", failures)
    measured_manifest = actual_manifest(Path(result["scenario_root"]))
    require(result.get("scenario_manifest") == measured_manifest, "Scenario manifest mismatch or unlinked file", failures)
    return failures


def main(result_path: Path, criteria: dict[str, Any]) -> int:
    try:
        result = read_json(result_path)
        failures = validate(result, criteria)
        measured_manifest = actual_manifest(Path(result["scenario_root"]))
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 2
    if failures:
        print(json.dumps({"status": "FAIL", "failures": failures}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps({"status": "PASS", "scenarios": "A-H", "mutations": "M1-M17 enforced", "scenario_id": result["scenario_id"], "scenario_evidence_count": result["scenario_evidence_count"], "scenario_manifest_count": len(measured_manifest), "scenario_manifest": measured_manifest, "concurrency": "runtime_observation_filesystem_cross_checked", "owner_pattern_source": "beta_core.model.OWNER_PATTERN"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}))
