"""Independent Validator fixture that checks an actual Executor result."""

import json
import sys
from pathlib import Path


result_path = Path(sys.argv[1])
criteria = json.loads(sys.argv[2])
try:
    result = json.loads(result_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(json.dumps({"error": str(exc)}))
    raise SystemExit(2)

passed = result.get("status") == "completed" and result.get("value") == criteria.get("expected_value")
print(json.dumps({"checked": str(result_path), "passed": passed}, sort_keys=True))
raise SystemExit(0 if passed else 1)
