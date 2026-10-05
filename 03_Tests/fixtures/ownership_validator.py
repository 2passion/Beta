"""Independent MVP Test 2 Validator that reads Scenario runtime records."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_events(directory: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def has_reason(event: dict[str, Any], required_terms: tuple[str, ...]) -> bool:
    reasons = event.get("payload", {}).get("reasons")
    if not isinstance(reasons, list) or not all(isinstance(reason, str) for reason in reasons):
        return False
    normalized = " ".join(reasons).lower()
    return all(term.lower() in normalized for term in required_terms)


def main() -> int:
    result_path = Path(sys.argv[1]).resolve()
    criteria = json.loads(sys.argv[2])
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        allowed_root = (result_path.parents[3] / "scenarios").resolve()
        directories = {key: Path(value).resolve() for key, value in result["scenario_evidence_dirs"].items()}
        failures: list[str] = []
        require(result.get("mvp_test_id") == criteria.get("mvp_test_id"), "MVP Test ID mismatch", failures)
        require(result.get("mvp_test_name") == criteria.get("mvp_test_name"), "MVP Test name mismatch", failures)
        require(result.get("test_plan_id") == criteria.get("test_plan_id"), "Test Plan ID mismatch", failures)
        require(result.get("test_plan_version") == criteria.get("test_plan_version"), "Test Plan version mismatch", failures)
        for key, directory in directories.items():
            require(directory.is_relative_to(allowed_root), f"Scenario {key} path is outside allowed root", failures)

        events_a = read_events(directories["A"])
        starts_a = [event for event in events_a if event["type"] == "RUN_STARTED"]
        require(len(starts_a) == 1, "Scenario A must have one RUN_STARTED", failures)
        if starts_a:
            require(starts_a[0]["payload"].get("write_owner") == "Codex", "Scenario A owner must be Codex", failures)
            require((directories["A"] / "runs" / starts_a[0]["run_id"]).is_dir(), "Scenario A Run folder missing", failures)
        require(any(event["type"] == "RUN_COMPLETED" for event in events_a), "Scenario A RUN_COMPLETED missing", failures)
        require(any(event["type"] == "VALIDATION_RESULT" and event["payload"].get("status") == "PASS" for event in events_a), "Scenario A Validation PASS missing", failures)
        require(any(event["type"] == "GATE_DECISION" and event["payload"].get("decision") == "PROCEED" for event in events_a), "Scenario A Gate PROCEED missing", failures)
        require(any(event["type"] == "EVIDENCE_RECORDED" for event in events_a), "Scenario A Evidence missing", failures)

        events_b = read_events(directories["B"])
        blocked_b = [event for event in events_b if event["type"] == "BLOCKED"]
        require(len(blocked_b) == 1, "Scenario B must have exactly one BLOCKED", failures)
        if blocked_b:
            require(
                has_reason(blocked_b[0], ("write_owner", "one identifier")),
                "Scenario B BLOCK reason must be the single-owner contract",
                failures,
            )
        require(not any(event["type"] == "RUN_STARTED" for event in events_b), "Scenario B must not RUN_STARTED", failures)
        require(not any(event["type"] in {"RUN_COMPLETED", "EXECUTION_ERROR"} for event in events_b), "Scenario B must not execute", failures)
        require(not any(event["type"] == "EVIDENCE_RECORDED" for event in events_b), "Scenario B must not record success Evidence", failures)
        runs_b = directories["B"] / "runs"
        require(not runs_b.exists() or not any(runs_b.iterdir()), "Scenario B Run folder must be absent", failures)
        require(not any(directories["B"].glob("EVD-*.json")), "Scenario B Evidence file must be absent", failures)

        events_c = read_events(directories["C"])
        starts_c_v1 = [event for event in events_c if event["type"] == "RUN_STARTED" and event["plan_version"] == "1.0"]
        blocked_c_v1 = [event for event in events_c if event["type"] == "BLOCKED" and event["plan_version"] == "1.0"]
        starts_c_v2 = [event for event in events_c if event["type"] == "RUN_STARTED" and event["plan_version"] == "2.0"]
        require(len(starts_c_v1) == 1 and starts_c_v1[0]["payload"].get("write_owner") == "Codex", "Scenario C baseline owner record invalid", failures)
        require(len(blocked_c_v1) == 1, "Scenario C same-version change must BLOCK", failures)
        if blocked_c_v1:
            blocked = blocked_c_v1[0]
            contract = blocked.get("payload", {}).get("contract")
            baseline_hash = sha256_file(Path(__file__).resolve().parent / "ownership_c_v1_codex.json")
            attempted_hash = sha256_file(Path(__file__).resolve().parent / "ownership_c_v1_changed_owner.json")
            require(
                has_reason(blocked, ("task_plan_sha256", "existing task_id/plan_version")),
                "Scenario C BLOCK reason must be the same-version Task Plan hash contract",
                failures,
            )
            require(isinstance(contract, dict), "Scenario C BLOCK contract missing", failures)
            if isinstance(contract, dict):
                require(contract.get("first_task_plan_sha256") == baseline_hash, "Scenario C first Task Plan hash mismatch", failures)
                require(contract.get("task_plan_sha256") == attempted_hash, "Scenario C attempted Task Plan hash mismatch", failures)
            require(not (directories["C"] / "runs" / blocked["run_id"]).exists(), "Scenario C blocked Run folder must be absent", failures)
            require(not any(event["run_id"] == blocked["run_id"] and event["type"] in {"RUN_STARTED", "RUN_COMPLETED", "EXECUTION_ERROR", "EVIDENCE_RECORDED"} for event in events_c), "Scenario C blocked attempt must not execute or record Evidence", failures)
        require(len(starts_c_v2) == 1 and starts_c_v2[0]["payload"].get("write_owner") == "Claude-Code", "Scenario C new-version owner record invalid", failures)
        if starts_c_v1 and starts_c_v2:
            require(starts_c_v1[0]["run_id"] != starts_c_v2[0]["run_id"], "Scenario C new version needs a new Run", failures)
            require((directories["C"] / "runs" / starts_c_v1[0]["run_id"]).is_dir(), "Scenario C baseline Run not preserved", failures)
            require((directories["C"] / "runs" / starts_c_v2[0]["run_id"]).is_dir(), "Scenario C new-version Run folder missing", failures)
        require(any(event["type"] == "GATE_DECISION" and event["plan_version"] == "2.0" and event["payload"].get("decision") == "PROCEED" for event in events_c), "Scenario C new-version Gate PROCEED missing", failures)

        evidence_links = []
        for key, directory in directories.items():
            for path in sorted(directory.glob("EVD-*.json")) + ([directory / "events.jsonl"] if (directory / "events.jsonl").is_file() else []) + ([directory / "evidence_index.jsonl"] if (directory / "evidence_index.jsonl").is_file() else []):
                evidence_links.append({"scenario": key, "path": str(path), "sha256": sha256_file(path)})
        require(bool(evidence_links), "Scenario Evidence links missing", failures)
        output = {
            "mvp_test_id": criteria["mvp_test_id"],
            "mvp_test_name": criteria["mvp_test_name"],
            "test_plan_id": criteria["test_plan_id"],
            "test_plan_version": criteria["test_plan_version"],
            "validation_status": "PASS" if not failures else "FAIL",
            "scenario_root": str(allowed_root),
            "scenario_internal_runs": {
                "A": [event["run_id"] for event in starts_a],
                "B_BLOCKED": [event["run_id"] for event in blocked_b],
                "C_BASE": [event["run_id"] for event in starts_c_v1],
                "C_SAME_VERSION_BLOCKED": [event["run_id"] for event in blocked_c_v1],
                "C_NEW_VERSION": [event["run_id"] for event in starts_c_v2],
            },
            "scenario_evidence": evidence_links,
            "failures": failures,
        }
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
        return 0 if not failures else 1
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"validation_status": "ERROR", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
