"""Synthetic executor created only inside an isolated MVP Test scenario."""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("x", encoding="utf-8", newline="\n") as handle:
    json.dump({"status": "completed", "value": "phase1-ok"}, handle, sort_keys=True)
    handle.write("\n")
