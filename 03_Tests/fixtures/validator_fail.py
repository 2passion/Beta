"""Independent Validator fixture for FAIL and ERROR classification tests."""

import json
import sys


criteria = json.loads(sys.argv[2])
if criteria.get("mode") == "error":
    print(json.dumps({"reason": "synthetic validator error"}))
    raise SystemExit(2)
print(json.dumps({"reason": "synthetic criteria mismatch"}))
raise SystemExit(1)
