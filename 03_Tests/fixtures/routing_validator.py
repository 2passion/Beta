"""Independent validator for the Order-035 routing contract fixture."""

import json
import sys
from pathlib import Path


result_path = Path(sys.argv[1])
criteria = json.loads(sys.argv[2])
failures = []
try:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    match = result["match"]
    mismatch = result["mismatch_fixture"]
    if not (match.get("expected_to") == match.get("actual_executor") == criteria.get("expected_executor")):
        failures.append("routing MATCH identity mismatch")
    if not (match.get("action") == "WRITE" and match.get("routing_result") == "MATCH" and match.get("write_allowed") is True):
        failures.append("routing MATCH contract invalid")
    if mismatch.get("routing_result") != "HOLD" or mismatch.get("mismatch_reason") != "ROUTING_MISMATCH":
        failures.append("routing mismatch must HOLD with ROUTING_MISMATCH")
    if any(mismatch.get(key) != 0 for key in ("writer_call_count", "beta_write_count", "next_step_count")):
        failures.append("routing mismatch side effects must be zero")
    if mismatch.get("write_allowed") is not False:
        failures.append("routing mismatch must not allow writes")
except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
    failures.append(f"routing validator error: {exc}")
print(json.dumps({"validation_status": "PASS" if not failures else "FAIL", "failures": failures}, sort_keys=True))
raise SystemExit(0 if not failures else 1)
