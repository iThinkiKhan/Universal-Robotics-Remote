"""Placement study: DevKitC geometry from the Espressif drawing, pose maths, wire lengths and the recorded pose."""
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/cad"))
import placement  # noqa: E402

IDENTITY = {"cx": 0.0, "cy": 0.0, "rot_deg": 0.0, "flip": False}


class DevKitCGeometry(unittest.TestCase):
    def setUp(self):
        self.board = placement.devkit()
        self.pins = self.board["pins"]

    def test_board_and_pin_counts(self):
        self.assertEqual((self.board["width"], self.board["length"]), (27.94, 48.26))
        self.assertEqual(len(self.pins), 38)
        self.assertEqual(sum(1 for p in self.pins if p["side"] == "J2"), 19)

    def test_row_spacing_pitch_and_margins(self):
        left = sorted((p for p in self.pins if p["side"] == "J2"), key=lambda p: p["pos"])
        right = sorted((p for p in self.pins if p["side"] == "J3"), key=lambda p: p["pos"])
        for a, b in zip(left, right):
            self.assertAlmostEqual(b["u"] - a["u"], 25.40)
            self.assertAlmostEqual(a["v"], b["v"])
        for a, b in zip(left, left[1:]):
            self.assertAlmostEqual(a["v"] - b["v"], 2.54)
        self.assertAlmostEqual(left[0]["u"], 1.27)
        self.assertAlmostEqual(left[-1]["v"], 1.27)                     # pos 19 (5V) is at the USB end
        self.assertAlmostEqual(self.board["length"] - left[0]["v"], 1.27)

    def test_usb_end_is_the_5v_and_clk_end(self):
        names = {(p["side"], p["pos"]): p["name"] for p in self.pins}
        self.assertEqual(names[("J2", 19)], "5V")
        self.assertEqual(names[("J3", 19)], "CLK")
        self.assertEqual(names[("J2", 1)], "3V3")

    def test_pins_the_registry_uses_are_where_the_datasheet_puts_them(self):
        by_gpio = {p["gpio"]: p for p in self.pins if p["gpio"] is not None}
        self.assertEqual((by_gpio[36]["side"], by_gpio[36]["pos"]), ("J2", 3))
        self.assertEqual((by_gpio[23]["side"], by_gpio[23]["pos"]), ("J3", 2))
        self.assertEqual((by_gpio[18]["side"], by_gpio[18]["pos"]), ("J3", 9))


class PoseMaths(unittest.TestCase):
    def setUp(self):
        self.board = placement.devkit()

    def test_pose_is_rigid(self):
        a, b = (3.0, 7.0), (20.0, 40.0)
        for pose in ({"cx": 50, "cy": 20, "rot_deg": 37, "flip": False}, {"cx": 10, "cy": 5, "rot_deg": 200, "flip": True}):
            d0 = math.dist(a, b)
            d1 = math.dist(placement.to_gamepad(a, pose, self.board), placement.to_gamepad(b, pose, self.board))
            self.assertAlmostEqual(d0, d1)

    def test_centre_goes_to_the_pose_centre_and_quarter_turn_swaps_axes(self):
        centre = (self.board["width"] / 2, self.board["length"] / 2)
        self.assertEqual(placement.to_gamepad(centre, {"cx": 9, "cy": 4, "rot_deg": 90, "flip": True}, self.board), (9, 4))
        xs = [c[0] for c in placement.corners({"cx": 0, "cy": 0, "rot_deg": 90, "flip": False}, self.board)]
        self.assertAlmostEqual(max(xs) - min(xs), self.board["length"])

    def test_flip_mirrors_which_row_is_on_which_side(self):
        j2 = next(p for p in self.board["pins"] if p["side"] == "J2" and p["pos"] == 1)
        plain = placement.to_gamepad((j2["u"], j2["v"]), IDENTITY, self.board)
        flipped = placement.to_gamepad((j2["u"], j2["v"]), {**IDENTITY, "flip": True}, self.board)
        self.assertAlmostEqual(plain[0] + flipped[0], 0.0)  # mirrored about the board centre, which sits at the pose centre (0, 0)
        self.assertAlmostEqual(plain[1], flipped[1])


class Lengths(unittest.TestCase):
    def setUp(self):
        self.board, self.gp, self.wires = placement.devkit(), placement.gamepad_data(), placement.button_wires()

    def test_every_wire_that_ends_on_the_devkitc_is_counted_once(self):
        self.assertEqual(len(self.wires), 20)  # 15 buttons + 5 ground returns; K_POW held, sticks go to the S3
        self.assertEqual(len({w["wire_id"] for w in self.wires}), 20)
        self.assertEqual(sum(1 for w in self.wires if w["far"] == "GND"), 5)

    def test_length_matches_hand_calculation(self):
        pose = {"cx": 60.0, "cy": 30.0, "rot_deg": 0.0, "flip": False}
        ls = {w["wire_id"]: w["length_mm"] for w in placement.lengths(pose, self.board, self.gp, self.wires)}
        pin = next(p for p in self.board["pins"] if p["gpio"] == 36)
        px, py = placement.to_gamepad((pin["u"], pin["v"]), pose, self.board)
        pad = self.gp["pads"]["TP19"]  # J2F-W01 R-UP
        self.assertAlmostEqual(ls["J2F-W01"], math.dist((px, py), (pad["x"], pad["y"])))

    def test_unsettled_pad_uses_the_longer_candidate(self):
        pose = {"cx": 60.0, "cy": 30.0, "rot_deg": 0.0, "flip": False}
        w = next(x for x in placement.lengths(pose, self.board, self.gp, self.wires) if x["signal"] == "K--")
        self.assertEqual(len(w["pads"]), 2)
        pin = next(p for p in self.board["pins"] if p["gpio"] == 19)
        end = placement.to_gamepad((pin["u"], pin["v"]), pose, self.board)
        longest = max(math.dist((self.gp["pads"][i]["x"], self.gp["pads"][i]["y"]), end) for i in w["pads"])
        self.assertAlmostEqual(w["length_mm"], longest)

    def test_ground_returns_use_the_nearest_gnd_pin(self):
        pose = {"cx": 60.0, "cy": 30.0, "rot_deg": 0.0, "flip": False}
        gnds = [placement.to_gamepad((p["u"], p["v"]), pose, self.board) for p in self.board["pins"] if p["name"] == "GND"]
        self.assertEqual(len(gnds), 3)
        w = next(x for x in placement.lengths(pose, self.board, self.gp, self.wires) if x["wire_id"] == "J2D-W05")
        pad = self.gp["pads"][w["pads"][0]]
        self.assertAlmostEqual(w["length_mm"], min(math.dist((pad["x"], pad["y"]), g) for g in gnds))


class RecordedPose(unittest.TestCase):
    def test_recorded_pose_fits_inside_the_gamepad_bounding_rectangle_and_is_not_beaten_by_the_origin(self):
        poses = json.loads((ROOT / "cad/assembly/placement-poses.json").read_text(encoding="utf-8"))
        pose = poses["r001"]["devkitc"]
        board, gp, wires = placement.devkit(), placement.gamepad_data(), placement.button_wires()
        self.assertTrue(placement.inside_bbox(pose, board, gp["bbox"], 2.0))
        recorded = placement.score(pose, board, gp, wires)[0]
        for rot in (0, 90, 180, 270):  # a few hand poses the search must beat or match
            alt = {"cx": 62.0, "cy": 31.0, "rot_deg": float(rot), "flip": False}
            if placement.inside_bbox(alt, board, gp["bbox"], 2.0):
                self.assertLessEqual(recorded, placement.score(alt, board, gp, wires)[0] + 1e-6)

    def test_built_model_validation_agrees_with_the_pure_python_numbers(self):
        report = json.loads((ROOT / "cad/assembly/placement-r001-validation.json").read_text(encoding="utf-8"))
        poses = json.loads((ROOT / "cad/assembly/placement-poses.json").read_text(encoding="utf-8"))
        board, gp, wires = placement.devkit(), placement.gamepad_data(), placement.button_wires()
        ls = placement.lengths(poses["r001"]["devkitc"], board, gp, wires)
        self.assertEqual(report["pose"], poses["r001"]["devkitc"])
        self.assertAlmostEqual(report["total_length_xy_mm"], sum(w["length_mm"] for w in ls), places=1)
        self.assertEqual(report["wires"], len(ls))
        self.assertEqual(report["devkitc_pins"], 38)
        self.assertTrue(report["native_reopened"])


if __name__ == "__main__":
    unittest.main()
