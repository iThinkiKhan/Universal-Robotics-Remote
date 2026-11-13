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


class S3Geometry(unittest.TestCase):
    def setUp(self):
        self.board = placement.s3_board()
        self.by_pos = {(p["side"], p["pos"]): p for p in self.board["pins"]}

    def test_the_s3_matches_the_owner_readings(self):
        m = json.loads((ROOT / "measurements/modules/esp32-s3-physical-20261112.json").read_text(encoding="utf-8"))
        self.assertEqual(self.board["width"], m["pcb"]["width_mm"]["value"])
        self.assertEqual(self.board["length"], m["pcb"]["length_mm"]["value"])
        g = self.board["geometry"]
        self.assertEqual(g["pcb_thickness_mm"], m["pcb"]["thickness_mm"]["value"])
        self.assertEqual(g["antenna_width_mm"], m["antenna"]["width_mm"]["value"])
        self.assertAlmostEqual(self.board["length"] + g["antenna_projection_mm"], m["antenna"]["overall_length_including_antenna_mm"]["value"])
        self.assertEqual(g["usb"]["left_edge_u"], m["usbs"]["left_usb_left_edge_from_pcb_left_mm"]["value"])
        self.assertEqual(g["module"]["u_min"], m["esp_module"]["left_edge_from_pcb_left_mm"]["value"])
        self.assertEqual(g["row_centre_spacing_mm"], m["gpio_headers"]["pin_heads_row_spacing_mm"]["value"])
        self.assertEqual(g["first_pin_from_usb_end_mm"], m["gpio_headers"]["closest_pin_head_from_usb_end_mm"]["value"])

    def test_44_pins_two_rows_of_22(self):
        self.assertEqual(len(self.board["pins"]), 44)
        self.assertEqual(sum(1 for p in self.board["pins"] if p["side"] == "J1"), 22)

    def test_the_gpios_the_registry_uses_are_on_the_espressif_positions(self):
        want = {5: ("J1", 5), 6: ("J1", 6), 7: ("J1", 7), 18: ("J1", 11), 2: ("J3", 5), 1: ("J3", 4), 21: ("J3", 18)}
        for gpio, key in want.items():
            self.assertEqual(self.by_pos[key]["gpio"], gpio)
        signals = json.loads((ROOT / "hardware/signals.json").read_text(encoding="utf-8"))["signals"]
        for sid in ("L-X", "L-Y", "R-X", "R-Y", "L-3", "R-3", "button_link_rx"):
            gpio = next(x["gpio"] for x in signals if x["id"] == sid)
            self.assertIn(gpio, want)

    def test_none_of_the_pins_used_is_unavailable_on_an_octal_psram_board(self):
        signals = json.loads((ROOT / "hardware/signals.json").read_text(encoding="utf-8"))["signals"]
        for sid in ("L-X", "L-Y", "R-X", "R-Y", "L-3", "R-3", "button_link_rx"):
            self.assertNotIn(next(x["gpio"] for x in signals if x["id"] == sid), (35, 36, 37))

    def test_pin_pitch_and_ends(self):
        left = sorted((p for p in self.board["pins"] if p["side"] == "J1"), key=lambda p: p["pos"])
        for a, b in zip(left, left[1:]):
            self.assertAlmostEqual(a["v"] - b["v"], 2.54)
        self.assertAlmostEqual(left[-1]["v"], 2.0)                       # pos 22 (5V and GND) is at the USB end
        self.assertLess(left[0]["v"], self.board["length"])             # pos 1 stays on the board
        self.assertAlmostEqual(self.by_pos[("J3", 1)]["u"] - self.by_pos[("J1", 1)]["u"], 25.5)

    def test_antenna_footprint_projects_6_5_mm_past_the_pcb(self):
        pcb, ant = placement.s3_footprint({"cx": 0, "cy": 0, "rot_deg": 0.0, "flip": False}, self.board)
        self.assertAlmostEqual(max(y for _, y in ant) - max(y for _, y in pcb), 6.5)
        self.assertAlmostEqual(max(x for x, _ in ant) - min(x for x, _ in ant), 18.0)


class Overlap(unittest.TestCase):
    SQUARE = [(0, 0), (10, 0), (10, 10), (0, 10)]

    def test_overlap_gap_and_rotation(self):
        far = [(x + 20, y) for x, y in self.SQUARE]
        near = [(x + 10.5, y) for x, y in self.SQUARE]
        self.assertFalse(placement.convex_overlap(self.SQUARE, far))
        self.assertFalse(placement.convex_overlap(self.SQUARE, near))
        self.assertTrue(placement.convex_overlap(self.SQUARE, near, gap=1.0))
        self.assertTrue(placement.convex_overlap(self.SQUARE, [(x + 5, y + 5) for x, y in self.SQUARE]))
        diamond = [(8, 5), (13, 0), (18, 5), (13, 10)]
        self.assertTrue(placement.convex_overlap(self.SQUARE, diamond))                        # its left tip is inside the square
        self.assertFalse(placement.convex_overlap(self.SQUARE, [(x + 3, y) for x, y in diamond]))


class S3Placement(unittest.TestCase):
    def setUp(self):
        self.poses = json.loads((ROOT / "cad/assembly/placement-poses.json").read_text(encoding="utf-8"))["r002"]
        self.dk_board, self.s3_board, self.gp = placement.devkit(), placement.s3_board(), placement.gamepad_data()

    def test_eight_stick_wires_reach_the_s3(self):
        wires = placement.s3_wires()
        self.assertEqual(len(wires), 8)
        self.assertEqual(sum(1 for w in wires if w["far"] == "GND"), 2)
        self.assertEqual({w["connector"] for w in wires}, {"J1L", "J1R"})

    def test_the_devkitc_pose_is_unchanged_from_r001(self):
        poses = json.loads((ROOT / "cad/assembly/placement-poses.json").read_text(encoding="utf-8"))
        self.assertEqual(self.poses["devkitc"], poses["r001"]["devkitc"])

    def test_recorded_s3_pose_is_inside_the_bounding_rectangle_and_is_the_square_on_optimum(self):
        pose = self.poses["s3"]
        bbox = self.gp["bbox"]
        for poly in placement.s3_footprint(pose, self.s3_board):
            for x, y in poly:
                self.assertTrue(bbox[0] + 2.0 <= x <= bbox[2] - 2.0 and bbox[1] + 2.0 <= y <= bbox[3] - 2.0)
        best = placement.s3_search(self.poses["devkitc"], coplanar=False, step_mm=1.0, rot_step=90)[0]
        recorded = sum(w["length_mm"] for w in placement.s3_lengths(pose, self.s3_board, self.poses["devkitc"], self.dk_board, self.gp))
        self.assertAlmostEqual(recorded, best["total_mm"], places=6)
        self.assertEqual(pose, best["pose"])

    def test_with_the_devkitc_in_the_same_layer_no_s3_pose_fits(self):
        self.assertEqual(placement.s3_search(self.poses["devkitc"], coplanar=True, step_mm=2.0, rot_step=90), [])

    def test_the_recorded_pose_overlaps_the_devkitc_so_it_needs_a_second_layer(self):
        dk = placement.corners(self.poses["devkitc"], self.dk_board)
        self.assertTrue(any(placement.convex_overlap(r, dk) for r in placement.s3_footprint(self.poses["s3"], self.s3_board)))

    def test_hand_length_of_the_uart_link(self):
        pose = {"cx": 60.0, "cy": 30.0, "rot_deg": 0.0, "flip": False}
        link = next(w for w in placement.s3_lengths(pose, self.s3_board, self.poses["devkitc"], self.dk_board, self.gp) if w["connector"] == "UART")
        dk = next(p for p in self.dk_board["pins"] if p["gpio"] == 17)
        s3 = next(p for p in self.s3_board["pins"] if p["gpio"] == 18)
        self.assertAlmostEqual(link["length_mm"], math.dist(placement.to_gamepad((dk["u"], dk["v"]), self.poses["devkitc"], self.dk_board),
                                                             placement.to_gamepad((s3["u"], s3["v"]), pose, self.s3_board)))

    def test_built_model_validation_agrees_with_the_pure_python_numbers(self):
        report = json.loads((ROOT / "cad/assembly/placement-r002-validation.json").read_text(encoding="utf-8"))
        ls = placement.s3_lengths(self.poses["s3"], self.s3_board, self.poses["devkitc"], self.dk_board, self.gp)
        self.assertEqual(report["s3_pose"], self.poses["s3"])
        self.assertEqual(report["s3_wires"], len(ls))
        self.assertAlmostEqual(report["s3_total_xy_mm"], sum(w["length_mm"] for w in ls), places=1)
        self.assertEqual(report["wire_objects"], 21 + 9)  # 20 DevKitC wires, K-- drawn to both candidate pads, plus 9 S3 wires
        self.assertTrue(report["native_reopened"])
        self.assertTrue(report["s3_overlaps_devkitc_in_xy"])
        self.assertAlmostEqual(report["display_pcb_volume_mm3"], 86 * 50 * 1.6 - 4 * math.pi * 1.575 ** 2 * 1.6, delta=0.2)
        self.assertAlmostEqual(report["mic_pcb_volume_mm3"], math.pi * 49 * 1.15 - 2 * 2 * 2 * 1.15, delta=4.0)


if __name__ == "__main__":
    unittest.main()
