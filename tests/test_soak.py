import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("soak", ROOT / "tools/analyze_soak.py")
soak = importlib.util.module_from_spec(spec)
spec.loader.exec_module(soak)
EVIDENCE = ROOT / "tests/fixtures/soak"


class RecordedHardwareRegression(unittest.TestCase):
    def test_original_blocking_capture_is_rejected(self):
        report = soak.analyze(EVIDENCE / "bench-soak.log", minimum_seconds=0)
        self.assertFalse(report["checks"]["bounded_main_loop"])
        self.assertFalse(report["passed"])

    def test_incremental_capture_keeps_acquisition_and_loop_bounded(self):
        # Actual before/after status records from the repeated device capture.
        before = (EVIDENCE / "bench-0.1.1-status.log").read_text()
        after = (EVIDENCE / "bench-0.1.1-after-capture.log").read_text()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "capture-interval.log"
            path.write_text(before + after)
            report = soak.analyze(path, minimum_seconds=0)
        self.assertTrue(report["passed"], report)
        self.assertLess(report["max_loop_us"], 100000)


if __name__ == "__main__":
    unittest.main()
