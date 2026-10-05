"""Independent filesystem/event validator for MVP Test 7 Resume."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


STEPS = ("STEP-1", "STEP-2", "STEP-3", "STEP-4")
TASK_ID = "MVP-TEST-7-RESUME"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def events(directory: Path) -> list[dict[str, Any]]:
    path = directory / "events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def verify_checkpoint(path: Path, directory: Path, expected_version: str, allow_later_side_effects: bool = False) -> tuple[str, str | None]:
    if not path.is_file():
        return "HOLD", "CHECKPOINT_MISSING"
    cp = read_json(path)
    if cp.get("record_type") != "CHECKPOINT":
        return "HOLD", "CHUNK_NOT_CHECKPOINT"
    if cp.get("task_id") != TASK_ID:
        return "HOLD", "TASK_MISMATCH"
    if cp.get("plan_version") != expected_version:
        return "HOLD", "PLAN_VERSION_MISMATCH"
    if cp.get("validation_status") != "PASS":
        return "HOLD", "LAST_STEP_NOT_PASS"
    completed = cp.get("completed_step_ids")
    if not isinstance(completed, list) or completed != list(STEPS[:len(completed)]) or cp.get("last_verified_step") != (completed[-1] if completed else None):
        return "HOLD", "CHECKPOINT_SEQUENCE_INVALID"
    expected_next = STEPS[len(completed)] if len(completed) < len(STEPS) else None
    if cp.get("expected_next_step") != expected_next:
        return "HOLD", "NEXT_STEP_MISMATCH"
    refs, snap = cp.get("evidence_refs"), cp.get("side_effect_snapshot")
    if not isinstance(refs, list) or not refs or not isinstance(snap, dict) or set(snap) != set(completed):
        return "HOLD", "EVIDENCE_INVALID"
    checkpoint_run = cp.get("run_id")
    for ref in refs:
        step = ref.get("step_id")
        if step not in completed or ref.get("task_id") != TASK_ID or ref.get("run_id") != checkpoint_run:
            return "HOLD", "EVIDENCE_INVALID"
        ev_path, side_path = Path(str(ref.get("evidence_path", ""))), Path(str(ref.get("side_effect_path", "")))
        if not ev_path.is_file() or sha256_file(ev_path) != ref.get("evidence_sha256"):
            return "HOLD", "EVIDENCE_INVALID"
        ev = read_json(ev_path)
        if ev.get("task_id") != TASK_ID or ev.get("run_id") != checkpoint_run or ev.get("plan_version") != expected_version or ev.get("step_id") != step or ev.get("validation_status") != "PASS":
            return "HOLD", "EVIDENCE_INVALID"
        val_path = Path(str(ev.get("validation_path", "")))
        validation = read_json(val_path) if val_path.is_file() else {}
        if not val_path.is_file() or sha256_file(val_path) != ev.get("validation_sha256") or validation.get("status") != "PASS" or validation.get("task_id") != TASK_ID or validation.get("run_id") != checkpoint_run or validation.get("step_id") != step:
            return "HOLD", "VALIDATION_INVALID"
        if not side_path.is_file() or sha256_file(side_path) != ref.get("side_effect_sha256") or ev.get("side_effect_sha256") != ref.get("side_effect_sha256"):
            return "HOLD", "SIDE_EFFECT_DRIFT"
        if snap.get(step) != {"path": str(side_path), "sha256": ref.get("side_effect_sha256")}:
            return "HOLD", "SIDE_EFFECT_DRIFT"
    for step, side_ref in snap.items():
        side_path = Path(str(side_ref.get("path", "")))
        if not side_path.is_file() or sha256_file(side_path) != side_ref.get("sha256"):
            return "HOLD", "SIDE_EFFECT_DRIFT"
    recorded = [event for event in events(directory) if event.get("type") == "CHECKPOINT_RECORDED" and event.get("payload", {}).get("checkpoint_id") == cp.get("checkpoint_id")]
    if len(recorded) != 1:
        return "HOLD", "CHECKPOINT_EVENT_INVALID"
    record = recorded[0]
    if record.get("task_id") != TASK_ID or record.get("run_id") != checkpoint_run or record.get("plan_version") != expected_version or Path(str(record.get("payload", {}).get("path", ""))).resolve() != path.resolve() or record.get("payload", {}).get("sha256") != sha256_file(path):
        return "HOLD", "CHECKPOINT_EVENT_INVALID"
    actual = {path.stem for path in (directory / "side_effects").glob("STEP-*.json")} if (directory / "side_effects").is_dir() else set()
    expected = set(completed)
    if allow_later_side_effects:
        permitted = set(STEPS[:max((STEPS.index(step) + 1 for step in actual), default=0)])
        if not expected.issubset(actual) or actual != permitted:
            return "HOLD", "UNTRACKED_SIDE_EFFECT" if actual - set(STEPS) else "SIDE_EFFECT_DRIFT"
    elif actual != expected:
        return "HOLD", "UNTRACKED_SIDE_EFFECT" if actual - expected else "SIDE_EFFECT_DRIFT"
    return ("NO_CHANGE", None) if expected_next is None else ("RESUME_ALLOWED", expected_next)


def count(directory: Path, event_type: str, step: str | None = None) -> int:
    return sum(e.get("type") == event_type and (step is None or e.get("payload", {}).get("step_id") == step) for e in events(directory))


def file_snapshot(directory: Path) -> dict[str, str]:
    return {path.relative_to(directory).as_posix(): sha256_file(path) for path in sorted(directory.rglob("*")) if path.is_file()}


def measurements(directory: Path) -> dict[str, Any]:
    snapshot = file_snapshot(directory)
    return {
        "file_snapshot": snapshot,
        "managed_file_count": len(snapshot),
        "run_directory_count": len([path for path in (directory / "runs").glob("*") if path.is_dir()]) if (directory / "runs").is_dir() else 0,
        "runtime_evidence_count": len(list((directory / "evidence").glob("*.json"))) if (directory / "evidence").is_dir() else 0,
        "checkpoint_count": len(list((directory / "checkpoints").glob("*.json"))) if (directory / "checkpoints").is_dir() else 0,
        "event_count": len(events(directory)),
    }


def verify_run_identity(label: str, directory: Path, failures: list[str]) -> None:
    rows = events(directory)
    started = [event for event in rows if event.get("type") == "RUN_STARTED"]
    interrupted = [event for event in rows if event.get("type") == "RUN_INTERRUPTED"]
    resumed = [event for event in rows if event.get("type") == "RESUME_STARTED"]
    require(len(started) == 1 and len(interrupted) == 1 and len(resumed) == 1, f"Scenario {label} interrupted/resume event identity missing", failures)
    if not (len(started) == len(interrupted) == len(resumed) == 1):
        return
    interrupted_id, resume_id = started[0].get("run_id"), resumed[0].get("run_id")
    require(interrupted[0].get("run_id") == interrupted_id, f"Scenario {label} interrupted identity mismatch", failures)
    require(interrupted_id != resume_id, f"Scenario {label} resume reused interrupted identity", failures)
    require(not any(event.get("type") == "RUN_COMPLETED" and event.get("run_id") == interrupted_id for event in rows), f"Scenario {label} interrupted run was rewritten completed", failures)
    for step in ("STEP-1", "STEP-2"):
        require([event.get("run_id") for event in rows if event.get("type") == "STEP_COMPLETED" and event.get("payload", {}).get("step_id") == step] == [interrupted_id], f"Scenario {label} {step} interrupted ownership mismatch", failures)
    for step in ("STEP-3", "STEP-4"):
        require([event.get("run_id") for event in rows if event.get("type") == "STEP_COMPLETED" and event.get("payload", {}).get("step_id") == step] == [resume_id], f"Scenario {label} {step} resume ownership mismatch", failures)
    resume_index = rows.index(resumed[0])
    require(rows.index(interrupted[0]) < resume_index, f"Scenario {label} event ordering mismatch", failures)
    checkpoint_events = [event for event in rows if event.get("type") == "CHECKPOINT_RECORDED"]
    require(all(event.get("run_id") == interrupted_id for event in checkpoint_events[:2]), f"Scenario {label} interrupted checkpoint ownership mismatch", failures)
    require(all(event.get("run_id") == resume_id for event in checkpoint_events[2:]), f"Scenario {label} resume checkpoint ownership mismatch", failures)


def actual_manifest(root: Path) -> list[dict[str, str]]:
    return [
        {"scenario_id": path.relative_to(root).parts[0], "relative_path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in sorted(root.rglob("*")) if path.is_file()
    ]


def validate(result: dict[str, Any], criteria: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_version = str(criteria.get("test_plan_version"))
    require(result.get("mvp_test_id") == criteria.get("mvp_test_id"), "MVP Test identity mismatch", failures)
    require(result.get("plan_version") == criteria.get("test_plan_version"), "Plan version mismatch", failures)
    dirs = {key: Path(value) for key, value in result.get("scenario_dirs", {}).items()}
    require(set(dirs) == set("ABCDEFG"), "Scenario A-G directories missing", failures)
    if set(dirs) != set("ABCDEFG"):
        return failures

    a = result["scenarios"]["A"]
    a_source = verify_checkpoint(Path(a["source_checkpoint"]), dirs["A"], expected_version, allow_later_side_effects=True)
    a_final = verify_checkpoint(Path(a["final_checkpoint"]), dirs["A"], expected_version)
    require(a_source == ("RESUME_ALLOWED", "STEP-3"), "Scenario A source checkpoint invalid", failures)
    require(a_final == ("NO_CHANGE", None), "Scenario A final checkpoint invalid", failures)
    require(a["decision"].get("decision") == "RESUME_ALLOWED" and a["decision"].get("next_step") == "STEP-3", "Scenario A decision mismatch", failures)
    for step in STEPS:
        require(count(dirs["A"], "STEP_COMPLETED", step) == 1, f"Scenario A {step} execution count mismatch", failures)
    resume_events = events(dirs["A"])
    start_index = next((i for i, event in enumerate(resume_events) if event.get("type") == "RESUME_STARTED"), -1)
    resumed = [event.get("payload", {}).get("step_id") for event in resume_events[start_index + 1:] if event.get("type") == "STEP_RESUMED"]
    require(resumed == ["STEP-3", "STEP-4"], "Scenario A did not resume exact next incomplete step", failures)
    verify_run_identity("A", dirs["A"], failures)

    b = result["scenarios"]["B"]
    require(verify_checkpoint(Path(b["checkpoint"]), dirs["B"], expected_version) == ("HOLD", "SIDE_EFFECT_DRIFT"), "Scenario B drift not independently detected", failures)
    require(b["decision"].get("reason_code") == "SIDE_EFFECT_DRIFT" and count(dirs["B"], "STEP_RESUMED") == 0 and count(dirs["B"], "RESUME_DECISION") == 1, "Scenario B executed after HOLD", failures)

    c = result["scenarios"]["C"]
    require(c["decision"] == {"decision": "HOLD", "reason_code": "CHECKPOINT_MISSING", "next_step": None}, "Scenario C missing checkpoint mismatch", failures)
    require(verify_checkpoint(Path(c["chunk"]), dirs["C"], expected_version) == ("HOLD", "CHUNK_NOT_CHECKPOINT"), "Scenario C Chunk accepted as Checkpoint", failures)
    require(c["chunk_decision"].get("reason_code") == "CHUNK_NOT_CHECKPOINT" and count(dirs["C"], "STEP_RESUMED") == 0 and count(dirs["C"], "RESUME_DECISION") == 2, "Scenario C executed without checkpoint", failures)

    d = result["scenarios"]["D"]
    require(verify_checkpoint(Path(d["checkpoint"]), dirs["D"], expected_version) == ("HOLD", "PLAN_VERSION_MISMATCH"), "Scenario D version mismatch not detected", failures)
    require(d["decision"].get("reason_code") == "PLAN_VERSION_MISMATCH" and count(dirs["D"], "STEP_RESUMED") == 0 and count(dirs["D"], "RESUME_DECISION") == 1, "Scenario D executed after version mismatch", failures)

    e = result["scenarios"]["E"]
    require(verify_checkpoint(Path(e["checkpoint"]), dirs["E"], expected_version) == ("HOLD", "LAST_STEP_NOT_PASS"), "Scenario E non-PASS checkpoint not detected", failures)
    require(e["decision"].get("reason_code") == "LAST_STEP_NOT_PASS" and count(dirs["E"], "STEP_RESUMED") == 0 and count(dirs["E"], "RESUME_DECISION") == 1, "Scenario E executed after non-PASS", failures)

    f = result["scenarios"]["F"]
    require(verify_checkpoint(Path(f["final_checkpoint"]), dirs["F"], expected_version) == ("NO_CHANGE", None), "Scenario F final checkpoint invalid", failures)
    require(f["second_decision"].get("decision") == "NO_CHANGE", "Scenario F re-entry not idempotent", failures)
    current_f = measurements(dirs["F"])
    require(f["before_reentry"] == f["after_reentry"] == current_f, "Scenario F current filesystem/Evidence changed on re-entry", failures)
    for step in STEPS:
        require(count(dirs["F"], "STEP_COMPLETED", step) == 1, f"Scenario F {step} reran", failures)
    verify_run_identity("F", dirs["F"], failures)

    g = result["scenarios"]["G"]
    require(g["routing_decision"].get("reason_code") == "ROUTING_MISMATCH", "Scenario G routing boundary mismatch", failures)
    require(g["scope_decision"].get("decision") == "APPROVAL_REQUIRED", "Scenario G scope boundary mismatch", failures)
    require(count(dirs["G"], "STEP_RESUMED") == 0 and count(dirs["G"], "RESUME_DECISION") == 2, "Scenario G boundary allowed execution", failures)
    root = Path(str(result.get("scenario_root", "")))
    declared_manifest = result.get("scenario_manifest")
    measured_manifest = actual_manifest(root) if root.is_dir() else []
    require(isinstance(declared_manifest, list) and declared_manifest == measured_manifest, "Scenario manifest mismatch or unlinked file", failures)
    require(all(entry.get("scenario_id") in set("ABCDEFG") for entry in measured_manifest), "Scenario manifest identity mismatch", failures)
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
    print(json.dumps({"status": "PASS", "scenarios": "A-G", "checkpoint_contract": "independently_recomputed", "mutations": "M1-M11 enforced", "scenario_manifest_count": len(measured_manifest), "scenario_manifest": measured_manifest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    result_arg = Path(sys.argv[1])
    criteria_arg = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    raise SystemExit(main(result_arg, criteria_arg))
