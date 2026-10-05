import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_Core"))
sys.path.insert(0, str(ROOT / "03_Tests" / "fixtures"))

from beta_core.cli import run_task  # noqa: E402
from routing_scenario_executor import evaluate_routing  # noqa: E402


PLAN = ROOT / "03_Tests/fixtures/task_order_035_routing.json"


class ExecutionRoutingTests(unittest.TestCase):
    def test_52_routing_match_and_mismatch_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_task(PLAN, ROOT, Path(temporary) / "routing")
            self.assertEqual((result["status"], result["validation"], result["gate"]), ("PASS", "PASS", "PROCEED"))

    def test_53_routing_mismatch_has_zero_side_effects(self) -> None:
        result = evaluate_routing("Claude Code", "Codex", "WRITE", "Order-035", "Beta")
        self.assertEqual((result["routing_result"], result["mismatch_reason"], result["write_allowed"]), ("HOLD", "ROUTING_MISMATCH", False))
        self.assertEqual((result["writer_call_count"], result["beta_write_count"], result["next_step_count"]), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
