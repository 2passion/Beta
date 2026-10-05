"""Minimal Safe Parallel classifier and deterministic scenario executor."""

from __future__ import annotations

import json
import ntpath
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
CORE_ROOT = PROJECT_ROOT / "02_Core"
FIXTURES = PROJECT_ROOT / "03_Tests/fixtures"
for item in (CORE_ROOT, FIXTURES):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from beta_core.model import OWNER_PATTERN, new_id, sha256_file
from routing_scenario_executor import evaluate_routing


PLAN_VERSION = "1.2"
REQUIRED_TASK_FIELDS = {
    "task_id", "depends_on", "write_owner", "write_set", "functional_domain",
    "shared_mutable_resources", "requested_scope", "routing_to", "actual_actor", "validation_independent",
}

RESERVED_DOS_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{index}" for index in range(1, 10)), *(f"LPT{index}" for index in range(1, 10))}


def write_json(path: Path, value: Any, exclusive: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def append_observation(path: Path, event_type: str, task_id: str, run_id: str, token: str) -> dict[str, Any]:
    record = {"event_id": new_id("OBS"), "type": event_type, "task_id": task_id, "run_id": run_id, "worker_id": threading.get_native_id(), "sync_token": token, "observed_ns": time.monotonic_ns()}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return record


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    normalized = ntpath.normcase(ntpath.normpath(drive + "\\" + "\\".join(parts)))
    return "KNOWN", normalized


def paths_overlap(left: str, right: str) -> bool:
    left_status, a = path_identity(left)
    right_status, b = path_identity(right)
    if left_status != "KNOWN" or right_status != "KNOWN" or a is None or b is None:
        return False
    return a == b or a.startswith(b.rstrip("\\") + "\\") or b.startswith(a.rstrip("\\") + "\\")


def has_cycle(tasks: list[dict[str, Any]]) -> bool:
    graph = {task["task_id"]: set(task["depends_on"]) for task in tasks}
    active: set[str] = set()
    done: set[str] = set()

    def visit(node: str) -> bool:
        if node in active:
            return True
        if node in done:
            return False
        active.add(node)
        for dependency in graph.get(node, set()):
            if dependency in graph and visit(dependency):
                return True
        active.remove(node)
        done.add(node)
        return False

    return any(visit(node) for node in graph)


def classify(contract: dict[str, Any]) -> dict[str, Any]:
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
    if has_cycle(tasks):
        return {"decision": "HOLD", "reason_code": "DEPENDENCY_CYCLE"}
    completed = set(completed_dependencies)
    if any(not isinstance(dep, str) or not dep or dep not in ids | completed for task in tasks for dep in task["depends_on"]):
        return {"decision": "HOLD", "reason_code": "DEPENDENCY_UNRESOLVED"}
    approved = set(contract.get("approved_scope", []))
    if any(not set(task["requested_scope"]).issubset(approved) for task in tasks):
        return {"decision": "HOLD", "reason_code": "APPROVAL_SCOPE_REQUIRED"}
    if any(evaluate_routing(task["routing_to"], task.get("actual_actor"), "WRITE", "Order-051", "Beta")["routing_result"] != "MATCH" for task in tasks):
        return {"decision": "HOLD", "reason_code": "ROUTING_MISMATCH"}
    if any(task["validation_independent"] is not True for task in tasks):
        return {"decision": "HOLD", "reason_code": "INDEPENDENT_VALIDATION_UNKNOWN"}
    reasons: list[str] = []
    if any(set(task["depends_on"]) & ids for task in tasks):
        reasons.append("DEPENDENCY_CONFLICT")
    if tasks[0]["write_owner"] == tasks[1]["write_owner"]:
        reasons.append("OWNER_CONTEXT_CONFLICT")
    if any(paths_overlap(left, right) for left in tasks[0]["write_set"] for right in tasks[1]["write_set"]):
        reasons.append("WRITE_SET_CONFLICT")
    if any(path_identity(path)[0] != "KNOWN" for task in tasks for path in task["write_set"]):
        reasons.append("WRITE_PATH_UNKNOWN")
    if tasks[0]["functional_domain"] == tasks[1]["functional_domain"]:
        reasons.append("FUNCTIONAL_DOMAIN_CONFLICT")
    if set(tasks[0]["shared_mutable_resources"]) & set(tasks[1]["shared_mutable_resources"]):
        reasons.append("SHARED_MUTABLE_RESOURCE")
    if reasons:
        return {"decision": "SEQUENTIAL_REQUIRED", "reason_code": reasons[0], "conflicts": reasons}
    return {"decision": "PARALLEL_ALLOWED", "reason_code": "INDEPENDENCE_PROVEN", "conflicts": []}


def task(name: str, owner: str, write_set: list[str], domain: str, *, depends: list[str] | None = None, resources: list[str] | None = None, scope: list[str] | None = None, routing_to: str = "Codex", actual_actor: str = "Codex", validation_independent: bool = True, task_id: str | None = None) -> dict[str, Any]:
    return {
        "task_id": task_id or f"TASK-{name}", "depends_on": depends or [], "write_owner": owner,
        "write_set": write_set, "functional_domain": domain, "shared_mutable_resources": resources or [],
        "requested_scope": scope or [f"fixture:{name}"], "routing_to": routing_to,
        "actual_actor": actual_actor, "validation_independent": validation_independent,
    }


def contract(tasks: list[dict[str, Any]], scopes: list[str] | None = None) -> dict[str, Any]:
    return {"tasks": tasks, "approved_scope": scopes or [item for task_item in tasks for item in task_item.get("requested_scope", [])]}


def write_contract(directory: Path, value: dict[str, Any]) -> Path:
    path = directory / "contract.json"
    write_json(path, value)
    return path


def task_artifacts(directory: Path, spec: dict[str, Any], run_id: str, status: str, runtime: dict[str, Any], stage_barrier: threading.Barrier | None = None) -> dict[str, Any]:
    task_id = spec["task_id"]
    output = directory / "outputs" / f"{task_id}.json"
    validation = directory / "validations" / f"{task_id}.json"
    evidence = directory / "evidence" / f"EVD-{task_id}.json"
    write_json(output, {"task_id": task_id, "run_id": run_id, "status": "completed" if status == "PASS" else "failed"})
    if stage_barrier is not None:
        stage_barrier.wait(timeout=5)
    write_json(validation, {"task_id": task_id, "run_id": run_id, "status": status})
    if stage_barrier is not None:
        stage_barrier.wait(timeout=5)
    write_json(evidence, {
        "task_id": task_id, "run_id": run_id, "validation_status": status,
        "output_path": str(output.resolve()), "output_sha256": sha256_file(output),
        "validation_path": str(validation.resolve()), "validation_sha256": sha256_file(validation),
    })
    if stage_barrier is not None:
        stage_barrier.wait(timeout=5)
    runtime.update({"output_path": str(output.resolve()), "output_sha256": sha256_file(output), "validation_path": str(validation.resolve()), "validation_sha256": sha256_file(validation), "evidence_path": str(evidence.resolve()), "evidence_sha256": sha256_file(evidence), "validation_status": status})
    write_json(directory / "runtime" / f"{task_id}.json", runtime)
    return runtime


def run_parallel(directory: Path, tasks: list[dict[str, Any]], statuses: dict[str, str]) -> dict[str, Any]:
    barrier = threading.Barrier(3)
    stage_barrier = threading.Barrier(2)
    token = new_id("BARRIER")
    records: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    def worker(spec: dict[str, Any]) -> None:
        task_id = spec["task_id"]
        try:
            run_id = new_id("RUN")
            observation_path = directory / "observations" / f"{task_id}.jsonl"
            started = append_observation(observation_path, "WORKER_STARTED", task_id, run_id, token)
            arrived = append_observation(observation_path, "BARRIER_ARRIVED", task_id, run_id, token)
            record = {"task_id": task_id, "run_id": run_id, "thread_id": threading.get_native_id(), "barrier_token": token, "started_ns": started["observed_ns"], "barrier_arrived_ns": arrived["observed_ns"]}
            barrier.wait(timeout=5)
            released = append_observation(observation_path, "BARRIER_RELEASED", task_id, run_id, token)
            record["barrier_passed_ns"] = released["observed_ns"]
            task_artifacts(directory, spec, run_id, statuses[task_id], record, stage_barrier)
            completed = append_observation(observation_path, "WORKER_COMPLETED", task_id, run_id, token)
            record["finished_ns"] = completed["observed_ns"]
            record["observation_path"] = str(observation_path.resolve())
            record["observation_sha256"] = sha256_file(observation_path)
            write_json(directory / "runtime" / f"{task_id}.json", record, exclusive=False)
            records[task_id] = record
        except Exception as exc:
            errors.append(f"{task_id}:{type(exc).__name__}:{exc}")

    threads = [threading.Thread(target=worker, args=(spec,), name=spec["task_id"]) for spec in tasks]
    for thread in threads:
        thread.start()
    barrier.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=5)
    if errors or any(thread.is_alive() for thread in threads):
        raise RuntimeError(f"parallel fixture failed: {errors}")
    return records


def stable_order(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    first, second = tasks
    if first["task_id"] in second["depends_on"]:
        return [first, second]
    if second["task_id"] in first["depends_on"]:
        return [second, first]
    return sorted(tasks, key=lambda item: item["task_id"])


def run_sequential(directory: Path, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for spec in stable_order(tasks):
        run_id = new_id("RUN")
        start = time.monotonic_ns()
        record = {"task_id": spec["task_id"], "run_id": run_id, "worker_id": "SEQUENTIAL-MAIN", "started_ns": start, "barrier_token": None}
        record = task_artifacts(directory, spec, run_id, "PASS", record)
        record["finished_ns"] = time.monotonic_ns()
        write_json(directory / "runtime" / f"{spec['task_id']}.json", record, exclusive=False)
        records.append(record)
    return records


def execute_scenario(directory: Path, value: dict[str, Any], statuses: dict[str, str] | None = None) -> dict[str, Any]:
    contract_path = write_contract(directory, value)
    decision = classify(value)
    write_json(directory / "decision.json", decision)
    tasks = value.get("tasks", [])
    records: Any = []
    if decision["decision"] == "PARALLEL_ALLOWED":
        records = run_parallel(directory, tasks, statuses or {task_item["task_id"]: "PASS" for task_item in tasks})
    elif decision["decision"] == "SEQUENTIAL_REQUIRED":
        records = run_sequential(directory, tasks)
    summary = {"contract_path": str(contract_path.resolve()), "decision": decision, "runtime": records, "execution_count": len(records)}
    write_json(directory / "summary.json", summary)
    return summary


def scenario_manifest(root: Path) -> list[dict[str, str]]:
    return [{"scenario_id": path.relative_to(root).parts[0], "relative_path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)} for path in sorted(root.rglob("*")) if path.is_file()]


def main(output_path: Path) -> None:
    root = output_path.parents[2].parent / "scenarios" / new_id("SCN")
    dirs = {label: root / label for label in "ABCDEFGH"}
    a_tasks = [task("A1", "Codex-A", [r"C:\Beta\parallel\a.json"], "domain-a"), task("A2", "Codex-B", [r"C:\Beta\parallel\b.json"], "domain-b")]
    a = execute_scenario(dirs["A"], contract(a_tasks))
    b_tasks = [task("B1", "Codex-A", [r"C:\Beta\parallel\b1.json"], "domain-b1"), task("B2", "Codex-B", [r"C:\Beta\parallel\b2.json"], "domain-b2", depends=["TASK-B1"])]
    b = execute_scenario(dirs["B"], contract(b_tasks))
    cycle_tasks = [task("BC1", "Codex-A", [r"C:\Beta\parallel\bc1.json"], "cycle-a", depends=["TASK-BC2"]), task("BC2", "Codex-B", [r"C:\Beta\parallel\bc2.json"], "cycle-b", depends=["TASK-BC1"])]
    cycle_contract = contract(cycle_tasks)
    write_json(dirs["B"] / "cycle_contract.json", cycle_contract)
    cycle_decision = classify(cycle_contract)
    write_json(dirs["B"] / "cycle_decision.json", cycle_decision)
    b["cycle_decision"] = cycle_decision
    c_tasks = [task("C1", "Codex-A", [r"C:\Beta\parallel\out\..\target.json"], "domain-c1"), task("C2", "Codex-B", [r"c:\beta\parallel\target.json"], "domain-c2")]
    c = execute_scenario(dirs["C"], contract(c_tasks))
    path_pairs = [
        ("trailing", r"C:\Beta\parallel\same.json. ", r"c:\beta\parallel\same.json"),
        ("extended", r"\\?\C:\Beta\parallel\same2.json", r"C:\Beta\parallel\same2.json"),
        ("relative", r"relative\target.json", r"C:\Beta\parallel\target.json"),
        ("unc", r"\\server\share\target.json", r"C:\Beta\parallel\target.json"),
        ("ads", r"C:\Beta\parallel\target.json:stream", r"C:\Beta\parallel\target.json"),
        ("short83", r"C:\BETA~1\target.json", r"C:\Beta\parallel\target.json"),
        ("wildcard", r"C:\Beta\parallel\*.json", r"C:\Beta\parallel\target.json"),
        ("reserved-nul", r"C:\Beta\parallel\NUL.json", r"C:\Beta\parallel\target.json"),
        ("reserved-com1", r"C:\Beta\parallel\COM1.txt", r"C:\Beta\parallel\target.json"),
        ("unicode", "Ｃ:\\Beta\\parallel\\target.json", r"C:\Beta\parallel\other.json"),
        ("sibling-control", r"C:\Beta\parallel\left.json", r"C:\Beta\parallel\right.json"),
    ]
    path_cases = []
    for name, left, right in path_pairs:
        value = contract([task(f"CP-{name}-1", "Codex-A", [left], f"path-{name}-a"), task(f"CP-{name}-2", "Codex-B", [right], f"path-{name}-b")])
        path_cases.append({"name": name, "contract": value, "decision": classify(value)})
    write_json(dirs["C"] / "path_cases.json", path_cases)
    c["path_cases"] = path_cases
    write_json(dirs["C"] / "summary.json", c, exclusive=False)
    d_task = task("D1", "Codex-A", [r"C:\Beta\parallel\d.json"], "domain-d", task_id="TASK-DUP")
    d_other = task("D2", "Codex-B", [r"C:\Beta\parallel\e.json"], "domain-e", task_id="TASK-DUP")
    d_task["writers"] = ["Codex-A", "Claude"]
    d = execute_scenario(dirs["D"], contract([d_task, d_other]))
    invalid_owners = ["Codex,Claude", "Codex Claude", "Codex/Claude", " Codex", "Co+dex", "-Codex", ""]
    d["owner_cases"] = [
        {"owner": owner, "decision": classify(contract([task(f"DO-{index}-1", owner, [fr"C:\Beta\parallel\do{index}a.json"], f"owner-{index}-a"), task(f"DO-{index}-2", "Codex-B", [fr"C:\Beta\parallel\do{index}b.json"], f"owner-{index}-b")]))}
        for index, owner in enumerate(invalid_owners)
    ]
    d["owner_control"] = classify(contract([task("DO-CONTROL-1", "Codex-A", [r"C:\Beta\parallel\owner-a.json"], "owner-control-a"), task("DO-CONTROL-2", "Codex-B", [r"C:\Beta\parallel\owner-b.json"], "owner-control-b")]))
    write_json(dirs["D"] / "summary.json", d, exclusive=False)
    e_tasks = [task("E1", "Codex-A", [r"C:\Beta\parallel\e1.json"], "domain-e1", resources=["registry:beta"]), task("E2", "Codex-B", [r"C:\Beta\parallel\e2.json"], "domain-e2", resources=["registry:beta"])]
    e = execute_scenario(dirs["E"], contract(e_tasks))
    f_tasks = [task("F1", "Codex-A", [r"C:\Beta\parallel\f1.json"], "domain-f1"), task("F2", "Codex-B", [r"C:\Beta\parallel\f2.json"], "domain-f2", scope=["fixture:outside"], actual_actor="Claude Code")]
    f = execute_scenario(dirs["F"], contract(f_tasks, scopes=["fixture:F1"]))
    g_tasks = [task("G1", "Codex-A", [r"C:\Beta\parallel\g1.json"], "domain-g1"), task("G2", "Codex-B", [r"C:\Beta\parallel\g2.json"], "domain-g2")]
    del g_tasks[1]["write_set"]
    g = execute_scenario(dirs["G"], contract(g_tasks))
    h_tasks = [task("H1", "Codex-A", [r"C:\Beta\parallel\h1.json"], "domain-h1"), task("H2", "Codex-B", [r"C:\Beta\parallel\h2.json"], "domain-h2")]
    h = execute_scenario(dirs["H"], contract(h_tasks), {"TASK-H1": "PASS", "TASK-H2": "FAIL"})
    h["batch_result"] = "PARTIAL_FAILURE"
    h["recovery_candidates"] = ["TASK-H2"]
    write_json(dirs["H"] / "summary.json", h, exclusive=False)
    result = {
        "mvp_test_id": "MVP-TEST-3", "mvp_test_name": "Safe Parallel", "plan_version": PLAN_VERSION,
        "change_reason_ref": "Order-051", "scenario_id": root.name, "scenario_root": str(root.resolve()),
        "scenario_dirs": {key: str(value.resolve()) for key, value in dirs.items()},
        "scenarios": {"A": a, "B": b, "C": c, "D": d, "E": e, "F": f, "G": g, "H": h},
        "scenario_evidence_count": len(list(root.rglob("evidence/*.json"))),
        "ownership_reuse": {"mode": "DIRECT_CORE_PATTERN_REUSE", "source": "beta_core.model.OWNER_PATTERN", "pattern": OWNER_PATTERN.pattern, "reason": "Reuse the Core/Test 2 owner identifier contract directly without adding an Architecture abstraction."},
    }
    result["scenario_manifest"] = scenario_manifest(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, result)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
