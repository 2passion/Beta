"""Deterministic synthetic Executor fixture."""

import json
import sys
from pathlib import Path


output_path = Path(sys.argv[1])
output_path.parent.mkdir(parents=True, exist_ok=True)
with output_path.open("w", encoding="utf-8", newline="\n") as handle:
    json.dump({"status": "completed", "value": "phase1-ok"}, handle, sort_keys=True)
    handle.write("\n")
