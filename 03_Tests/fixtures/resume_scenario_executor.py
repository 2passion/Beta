"""Execute bounded MVP Test 7 Resume scenarios without treating output chunks as checkpoints."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
CORE_ROOT = PROJECT_ROOT / "02_Core"
FIXTURES = PROJECT_ROOT / "03_Tests/fixtures"
for item in (CORE_ROOT, FIXTURES):
    if str(item) not in sys.path:
        sys.path.insert(0, str(item))

from beta_core.event_store import EventStore
from beta_core.model import new_id, sha256_file, utc_now
from user_gate_scenario_executor import approved_context, decide_user_gate
from routing_scenario_executor import evaluate_routing


TASK_ID = "MVP-TEST-7-RESUME"
PLAN_VERSION = "1.1"
STEPS = ("STEP-1", "STEP-2", "STEP-3", "STEP-4")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def append(directory: Path, event_type: str, run_id: str, plan_version: str, payload: dict[str, Any]) -> None:
    EventStore(directory / "events.jsonl").append(
        event_type, task_id=TASK_ID, run_id=run_id, plan_version=plan_version,
        actor_role="ResumeHarness", payload=payload,
    )


def execute_step(directory: Path, run_id: str, plan_version: str, step_id: str) -> dict[str, Any]:
    side_effect = directory / "side_effects" / f"{step_id}.json"
    validation = directory / "validations" / f"{step_id}.json"
    evidence = directory / "evidence" / f"EVD-{step_id}.json"
    body = {"task_id": TASK_ID, "plan_version": plan_version, "run_id": run_id, "step_id": step_id, "value": f"result:{step_id}"}
    write_json(side_effect, body)
    append(directory, "STEP_COMPLETED", run_id, plan_version, {"step_id": step_id, "side_effect_path": str(side_effect.resolve())})
    write_json(validation, {"task_id": TASK_ID, "plan_version": plan_version, "run_id": run_id, "step_id": step_id, "status": "PASS"})
    append(directory, "VALIDATION_RESULT", run_id, plan_version, {"step_id": step_id, "status": "PASS", "path": str(validation.resolve())})
    evidence_body = {
        "evidence_id": f"EVD-{step_id}", "task_id": TASK_ID, "plan_version": plan_version,
        "run_id": run_id, "step_id": step_id, "validation_status": "PASS",
        "validation_path": str(validation.resolve()), "validation_sha256": sha256_file(validation),
        "side_effect_path": str(side_effect.resolve()), "side_effect_sha256": sha256_file(side_effect),
    }
    write_json(evidence, evidence_body)
    append(directory, "EVIDENCE_RECORDED", run_id, plan_version, {"step_id": step_id, "path": str(evidence.resolve()), "sha256": sha256_file(evidence)})
    return {
        "step_id": step_id, "task_id": TASK_ID, "run_id": run_id,
        "evidence_path": str(evidence.resolve()), "evidence_sha256": sha256_file(evidence),
        "side_effect_path": str(side_effect.resolve()), "side_effect_sha256": sha256_file(side_effect),
    }


def record_checkpoint(directory: Path, run_id: str, plan_version: str, completed: list[str], refs: list[dict[str, Any]], validation_status: str = "PASS") -> Path:
    checkpoint_id = new_id("CP")
    next_step = STEPS[len(completed)] if len(completed) < len(STEPS) else None
    checkpoint = {
        "checkpoint_id": checkpoint_id, "record_type": "CHECKPOINT", "task_id": TASK_ID,
        "plan_version": plan_version, "run_id": run_id, "completed_step_ids": completed,
        "last_verified_step": completed[-1] if completed else None, "validation_status": validation_status,
        "expected_next_step": next_step,
        "evidence_refs": [ref for ref in refs if ref["run_id"] == run_id],
        "side_effect_snapshot": {ref["step_id"]: {"path": ref["side_effect_path"], "sha256": ref["side_effect_sha256"]} for ref in refs},
        "sequence": len(completed), "created_at": utc_now(),
    }
    path = directory / "checkpoints" / f"{checkpoint_id}.json"
    write_json(path, checkpoint)
    append(directory, "CHECKPOINT_RECORDED", run_id, plan_version, {"checkpoint_id": checkpoint_id, "path": str(path.resolve()), "sha256": sha256_file(path), "expected_next_step": next_step})
    return path


def inspect_checkpoint(path: Path | None, directory: Path, current_version: str, expected_to: str = "Codex", actual_actor: str = "Codex", requested_scope: list[str] | None = None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {"decision": "HOLD", "reason_code": "CHECKPOINT_MISSING", "next_step": None}
    checkpoint = read_json(path)
    if checkpoint.get("record_type") != "CHECKPOINT":
        return {"decision": "HOLD", "reason_code": "CHUNK_NOT_CHECKPOINT", "next_step": None}
    if checkpoint.get("task_id") != TASK_ID:
        return {"decision": "HOLD", "reason_code": "TASK_MISMATCH", "next_step": None}
    if checkpoint.get("plan_version") != current_version:
        return {"decision": "HOLD", "reason_code": "PLAN_VERSION_MISMATCH", "next_step": None}
    if checkpoint.get("validation_status") != "PASS":
        return {"decision": "HOLD", "reason_code": "LAST_STEP_NOT_PASS", "next_step": None}
    completed = checkpoint.get("completed_step_ids")
    if not isinstance(completed, list) or completed != list(STEPS[:len(completed)]):
        return {"decision": "HOLD", "reason_code": "CHECKPOINT_SEQUENCE_INVALID", "next_step": None}
    if checkpoint.get("last_verified_step") != (completed[-1] if completed else None):
        return {"decision": "HOLD", "reason_code": "CHECKPOINT_SEQUENCE_INVALID", "next_step": None}
    expected_next = STEPS[len(completed)] if len(completed) < len(STEPS) else None
    if checkpoint.get("expected_next_step") != expected_next:
        return {"decision": "HOLD", "reason_code": "NEXT_STEP_MISMATCH", "next_step": None}
    refs = checkpoint.get("evidence_refs")
    snapshot = checkpoint.get("side_effect_snapshot")
    if not isinstance(refs, list) or not refs or not isinstance(snapshot, dict) or set(snapshot) != set(completed):
        return {"decision": "HOLD", "reason_code": "EVIDENCE_INVALID", "next_step": None}
    checkpoint_run = checkpoint.get("run_id")
    for ref in refs:
        step_id = ref.get("step_id")
        evidence_path = Path(str(ref.get("evidence_path", "")))
        side_path = Path(str(ref.get("side_effect_path", "")))
        if step_id not in completed or ref.get("task_id") != TASK_ID or ref.get("run_id") != checkpoint_run or not evidence_path.is_file() or sha256_file(evidence_path) != ref.get("evidence_sha256"):
            return {"decision": "HOLD", "reason_code": "EVIDENCE_INVALID", "next_step": None}
        evidence = read_json(evidence_path)
        if evidence.get("validation_status") != "PASS" or evidence.get("step_id") != step_id or evidence.get("plan_version") != current_version or evidence.get("task_id") != TASK_ID or evidence.get("run_id") != checkpoint_run:
            return {"decision": "HOLD", "reason_code": "EVIDENCE_INVALID", "next_step": None}
        validation_path = Path(str(evidence.get("validation_path", "")))
        validation_body = read_json(validation_path) if validation_path.is_file() else {}
        if not validation_path.is_file() or sha256_file(validation_path) != evidence.get("validation_sha256") or validation_body.get("task_id") != TASK_ID or validation_body.get("run_id") != checkpoint_run or validation_body.get("step_id") != step_id:
            return {"decision": "HOLD", "reason_code": "VALIDATION_INVALID", "next_step": None}
        if not side_path.is_file() or sha256_file(side_path) != ref.get("side_effect_sha256"):
            return {"decision": "HOLD", "reason_code": "SIDE_EFFECT_DRIFT", "next_step": None}
        if snapshot.get(step_id) != {"path": str(side_path), "sha256": ref.get("side_effect_sha256")}:
            return {"decision": "HOLD", "reason_code": "SIDE_EFFECT_DRIFT", "next_step": None}
    for step_id, side_ref in snapshot.items():
        side_path = Path(str(side_ref.get("path", "")))
        if not side_path.is_file() or sha256_file(side_path) != side_ref.get("sha256"):
            return {"decision": "HOLD", "reason_code": "SIDE_EFFECT_DRIFT", "next_step": None}
    actual = {path.stem for path in (directory / "side_effects").glob("STEP-*.json")} if (directory / "side_effects").is_dir() else set()
    if actual != set(completed):
        return {"decision": "HOLD", "reason_code": "UNTRACKED_SIDE_EFFECT" if actual - set(completed) else "SIDE_EFFECT_DRIFT", "next_step": None}
    route = evaluate_routing(expected_to, actual_actor, "WRITE", "Order-042", "Beta")
    if route.get("routing_result") != "MATCH":
        return {"decision": "HOLD", "reason_code": "ROUTING_MISMATCH", "next_step": None}
    scope = requested_scope or ["04_Evidence/mvp_test_7"]
    gate = decide_user_gate(approved_context(["04_Evidence/mvp_test_7"], scope))
    if gate["decision"] != "AUTO":
        return {"decision": gate["decision"], "reason_code": gate["reason_code"], "next_step": None}
    if expected_next is None:
        return {"decision": "NO_CHANGE", "reason_code": "ALREADY_COMPLETE", "next_step": None}
    return {"decision": "RESUME_ALLOWED", "reason_code": "VERIFIED_CHECKPOINT", "next_step": expected_next}


def resume(directory: Path, checkpoint_path: Path | None, current_version: str, **kwargs: Any) -> tuple[dict[str, Any], Path | None]:
    decision = inspect_checkpoint(checkpoint_path, directory, current_version, **kwargs)
    resume_id = new_id("RESUME")
    if decision["decision"] != "NO_CHANGE":
        append(directory, "RESUME_DECISION", resume_id, current_version, decision)
    if decision["decision"] != "RESUME_ALLOWED":
        return decision, None
    assert checkpoint_path is not None
    checkpoint = read_json(checkpoint_path)
    completed = list(checkpoint["completed_step_ids"])
    refs = list(checkpoint["evidence_refs"])
    append(directory, "RESUME_STARTED", resume_id, current_version, {"checkpoint_id": checkpoint["checkpoint_id"], "next_step": decision["next_step"]})
    final_path = None
    for step_id in STEPS[len(completed):]:
        append(directory, "STEP_RESUMED", resume_id, current_version, {"step_id": step_id})
        refs.append(execute_step(directory, resume_id, current_version, step_id))
        completed.append(step_id)
        final_path = record_checkpoint(directory, resume_id, current_version, list(completed), list(refs))
    append(directory, "RESUME_COMPLETED", resume_id, current_version, {"completed_step_ids": completed, "final_checkpoint": str(final_path.resolve())})
    return decision, final_path


def seed(directory: Path, completed_count: int = 2, plan_version: str = PLAN_VERSION, validation_status: str = "PASS") -> Path:
    run_id = new_id("RUN-INTERRUPTED")
    append(directory, "RUN_STARTED", run_id, plan_version, {"interrupted_fixture": True})
    refs: list[dict[str, Any]] = []
    checkpoint = None
    for step_id in STEPS[:completed_count]:
        refs.append(execute_step(directory, run_id, plan_version, step_id))
        checkpoint = record_checkpoint(directory, run_id, plan_version, [ref["step_id"] for ref in refs], list(refs), validation_status if len(refs) == completed_count else "PASS")
    append(directory, "RUN_INTERRUPTED", run_id, plan_version, {"last_checkpoint": str(checkpoint.resolve())})
    assert checkpoint is not None
    return checkpoint


def event_count(directory: Path, event_type: str, step_id: str | None = None) -> int:
    if not (directory / "events.jsonl").is_file():
        return 0
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    return sum(event.get("type") == event_type and (step_id is None or event.get("payload", {}).get("step_id") == step_id) for event in events)


def snapshot(directory: Path) -> dict[str, str]:
    return {path.relative_to(directory).as_posix(): sha256_file(path) for path in sorted(directory.rglob("*")) if path.is_file()}


def measurements(directory: Path) -> dict[str, Any]:
    files = snapshot(directory)
    return {
        "file_snapshot": files,
        "managed_file_count": len(files),
        "run_directory_count": len([path for path in (directory / "runs").glob("*") if path.is_dir()]) if (directory / "runs").is_dir() else 0,
        "runtime_evidence_count": len(list((directory / "evidence").glob("*.json"))) if (directory / "evidence").is_dir() else 0,
        "checkpoint_count": len(list((directory / "checkpoints").glob("*.json"))) if (directory / "checkpoints").is_dir() else 0,
        "event_count": len((directory / "events.jsonl").read_text(encoding="utf-8").splitlines()) if (directory / "events.jsonl").is_file() else 0,
    }


def manifest(root: Path) -> list[dict[str, str]]:
    return [
        {"scenario_id": path.relative_to(root).parts[0], "relative_path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in sorted(root.rglob("*")) if path.is_file()
    ]


def main(output_path: Path) -> None:
    root = output_path.parents[2].parent / "scenarios" / new_id("SCN")
    dirs = {label: root / label for label in "ABCDEFG"}

    cp_a = seed(dirs["A"])
    decision_a, final_a = resume(dirs["A"], cp_a, PLAN_VERSION)

    cp_b = seed(dirs["B"])
    Path(read_json(cp_b)["side_effect_snapshot"]["STEP-2"]["path"]).unlink()
    decision_b, _ = resume(dirs["B"], cp_b, PLAN_VERSION)

    run_c = new_id("RUN-UNTRACKED")
    execute_step(dirs["C"], run_c, PLAN_VERSION, "STEP-1")
    decision_c, _ = resume(dirs["C"], None, PLAN_VERSION)
    chunk = dirs["C"] / "user_output_chunk.json"
    write_json(chunk, {"record_type": "CHUNK", "text": "partial user-facing output", "completed_step_ids": ["STEP-1"]})
    chunk_decision, _ = resume(dirs["C"], chunk, PLAN_VERSION)

    cp_d = seed(dirs["D"], plan_version="0.9")
    decision_d, _ = resume(dirs["D"], cp_d, PLAN_VERSION)

    cp_e = seed(dirs["E"], validation_status="FAIL")
    decision_e, _ = resume(dirs["E"], cp_e, PLAN_VERSION)

    cp_f = seed(dirs["F"])
    first_f, final_f = resume(dirs["F"], cp_f, PLAN_VERSION)
    before_f = measurements(dirs["F"])
    second_f, _ = resume(dirs["F"], final_f, PLAN_VERSION)
    after_f = measurements(dirs["F"])

    cp_g = seed(dirs["G"])
    routing_g, _ = resume(dirs["G"], cp_g, PLAN_VERSION, actual_actor="Claude Code")
    scope_g, _ = resume(dirs["G"], cp_g, PLAN_VERSION, requested_scope=["04_Evidence/mvp_test_7", "02_Core"])

    result = {
        "mvp_test_id": "MVP-TEST-7", "mvp_test_name": "Resume", "plan_version": PLAN_VERSION,
        "change_reason_ref": "Order-044", "scenario_id": root.name, "scenario_root": str(root.resolve()),
        "scenario_dirs": {key: str(value.resolve()) for key, value in dirs.items()},
        "scenarios": {
            "A": {"decision": decision_a, "source_checkpoint": str(cp_a.resolve()), "final_checkpoint": str(final_a.resolve())},
            "B": {"decision": decision_b, "checkpoint": str(cp_b.resolve())},
            "C": {"decision": decision_c, "chunk_decision": chunk_decision, "chunk": str(chunk.resolve())},
            "D": {"decision": decision_d, "checkpoint": str(cp_d.resolve())},
            "E": {"decision": decision_e, "checkpoint": str(cp_e.resolve())},
            "F": {"first_decision": first_f, "second_decision": second_f, "final_checkpoint": str(final_f.resolve()), "before_reentry": before_f, "after_reentry": after_f},
            "G": {"routing_decision": routing_g, "scope_decision": scope_g, "checkpoint": str(cp_g.resolve())},
        },
        "execution_counts": {label: {step: event_count(directory, "STEP_COMPLETED", step) for step in STEPS} for label, directory in dirs.items()},
    }
    result["scenario_manifest"] = manifest(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
