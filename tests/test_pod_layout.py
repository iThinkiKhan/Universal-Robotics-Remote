"""Enclosure pod study: the recorded space claim is self-consistent and matches the module readings it cites."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cad"))
import pod_layout  # noqa: E402


class PodLayout(unittest.TestCase):
    def setUp(self):
        self.rec = pod_layout.load(1)
        self.bodies = {b["id"]: b for b in self.rec["bodies"]}

    def test_layout_is_consistent(self):
        self.assertEqual(pod_layout.check(self.rec), [])

    def test_checker_catches_a_collision_and_an_escape(self):
        bad = copy.deepcopy(self.rec)
        next(b for b in bad["bodies"] if b["id"] == "BAT2")["pos"][1] = 20.0
        self.assertTrue(any("BAT2" in p and "MCU1" in p for p in pod_layout.check(bad)))
        bad = copy.deepcopy(self.rec)
        next(b for b in bad["bodies"] if b["id"] == "WRM1")["size"][2] = 20.0
        self.assertTrue(any("WRM1 leaves" in p for p in pod_layout.check(bad)))

    def test_sizes_match_the_module_readings(self):
        disp = json.loads((ROOT / "measurements/modules/display-physical-20261112.json").read_text(encoding="utf-8"))
        s3 = json.loads((ROOT / "measurements/modules/esp32-s3-physical-20261112.json").read_text(encoding="utf-8"))
        self.assertEqual(self.bodies["DISP1"]["size"][:2], [disp["pcb"]["length_mm"]["value"], disp["pcb"]["width_mm"]["value"]])
        self.assertEqual(self.bodies["DISP1"]["size"][2], disp["screen"]["front_to_back_thickness_with_pcb_mm"]["value"])
        stack = disp["full_assembly"]["total_thickness_including_pcb_screen_sd_slot_mm"]["value"]
        self.assertAlmostEqual(self.bodies["DISP1"]["size"][2] + self.bodies["DISP1_SD"]["size"][2], stack)
        self.assertEqual(self.bodies["MCU1"]["size"][:2],
                         [s3["antenna"]["overall_length_including_antenna_mm"]["value"], s3["pcb"]["width_mm"]["value"]])
        parts = {c["id"]: c for c in json.loads((ROOT / "hardware/components.json").read_text(encoding="utf-8"))["components"]}
        self.assertEqual(self.bodies["BAT2"]["size"], parts["BAT2"]["dimensions_mm"])
        self.assertEqual(self.bodies["WRM1"]["size"][:2], [parts["WRM1"]["dimensions_mm"][1], parts["WRM1"]["dimensions_mm"][0]])

    def test_window_lies_on_the_display_and_is_the_measured_screen_size(self):
        x0, y0, x1, y1 = next(o for o in self.rec["openings"] if o["id"] == "WINDOW")["rect"]
        d = pod_layout.box(self.bodies["DISP1"])
        self.assertTrue(d[0] <= x0 and x1 <= d[3] and d[1] <= y0 and y1 <= d[4])
        self.assertAlmostEqual(x1 - x0, 69.25)
        self.assertAlmostEqual(y1 - y0, 50.0)

    def test_record_is_not_released_for_printing(self):
        self.assertIn("NOT FOR PRINTING", self.rec["state"])
        self.assertTrue(all(b["state"] and b["source"] for b in self.rec["bodies"]))


if __name__ == "__main__":
    unittest.main()
