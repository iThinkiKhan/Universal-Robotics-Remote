"""Virtual tests of the proposed harness: the netlist built from the records, and the proposed button link."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


netlist = load("harness_netlist", "tools/harness_netlist.py")
link = load("button_link", "tools/button_link.py")
REGISTRY = json.loads((ROOT / "hardware/signals.json").read_text(encoding="utf-8"))
HARNESSES = json.loads((ROOT / "electronics/harnesses.json").read_text(encoding="utf-8"))


class Netlist(unittest.TestCase):
    def setUp(self):
        self.rows = netlist.build()
        self.signal_rows = [r for r in self.rows if r["signal"] != "GND" and r["connector"] != "J3"]

    def test_committed_netlist_is_current(self):
        self.assertEqual((ROOT / "electronics/netlist-proposed.csv").read_text(encoding="utf-8"), netlist.to_csv(self.rows))

    def test_every_wired_signal_reaches_exactly_one_far_pin(self):
        wired = [r for r in self.signal_rows if "reserved" not in r["far_pin"]]
        self.assertEqual(len(wired), 21)  # 4 axes + 2 clicks + 15 buttons
        for r in wired:
            self.assertRegex(r["far_pin"], r"^GPIO\d+$", r["wire_id"])
        pins = [(r["far_board"], r["far_pin"]) for r in wired]
        self.assertEqual(len(pins), len(set(pins)), "two signals share one far-end pin")

    def test_sticks_go_to_the_s3_and_buttons_to_the_wroom(self):
        for r in self.signal_rows:
            expected = "ESP32-S3" if r["connector"].startswith("J1") else "DevKitC V4 (WROOM-32U)"
            self.assertEqual(r["far_board"], expected, r["wire_id"])

    def test_s3_pins_avoid_everything_already_wired_or_off_limits(self):
        taken = {s["gpio"] for s in REGISTRY["signals"] if s["state"] in ("installed", "reserved")}
        off_limits = {0, 3, 19, 20, 45, 46, 43, 44} | set(range(22, 38))
        for r in self.signal_rows:
            if r["far_board"] == "ESP32-S3":
                gpio = int(r["far_pin"][4:])
                self.assertNotIn(gpio, taken, r["wire_id"])
                self.assertNotIn(gpio, off_limits, r["wire_id"])
        # the link receiver and the stick signals use different S3 pins
        s3_pins = [s["gpio"] for s in REGISTRY["signals"] if s["gpio"] is not None]
        self.assertEqual(len(s3_pins), len(set(s3_pins)))

    def test_wroom_pins_avoid_straps_flash_console_and_the_uart(self):
        bad = {0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 15, REGISTRY["wroom"]["uart_tx_gpio"]}
        for r in self.signal_rows:
            if r["far_board"].startswith("DevKitC"):
                self.assertNotIn(int(r["far_pin"][4:].split()[0]), bad, r["wire_id"])

    def test_power_is_reserved_not_wired(self):
        power = [r for r in self.rows if r["signal"] == "K_POW"]
        self.assertEqual(len(power), 1)
        self.assertIn("not wired", power[0]["far_pin"])
        self.assertEqual(power[0]["status"], "hold")

    def test_one_spare_pin_is_kept_for_a_return_link(self):
        spare = {e["gpio"] for e in REGISTRY["wroom"]["spare"]}
        self.assertIn(16, spare)  # UART2 RX
        used = {e["gpio"] for e in REGISTRY["wroom"]["inputs"] + REGISTRY["wroom"]["reserved"]}
        self.assertEqual(used | spare, set(REGISTRY["wroom"]["candidates"]))

    def test_every_connector_has_a_ground_and_fits_xh(self):
        for h in HARNESSES["harnesses"]:
            rows = [r for r in self.rows if r["connector"] == h["id"]]
            if h["pins"]:
                self.assertTrue(any(r["signal"] == "GND" for r in rows), h["id"])
                self.assertLessEqual(len(rows), 6, h["id"])


class ButtonLink(unittest.TestCase):
    def test_frame_time_and_budget(self):
        self.assertAlmostEqual(link.frame_time_ms(), 0.434, places=3)
        self.assertLess(link.frame_time_ms() + link.SEND_PERIOD_MS, link.TIMEOUT_MS)  # one lost frame does not trip the timeout
        self.assertGreater(link.TIMEOUT_MS, 3 * link.SEND_PERIOD_MS)

    def test_bit_order_follows_the_registry(self):
        order = link.button_order()
        self.assertEqual(order, HARNESSES["wroom_inputs"])
        self.assertEqual(len(order), 15)
        self.assertLess(len(order), link.POWER_BIT + 1)  # POWER keeps bit 15

    def test_every_mask_round_trips(self):
        for mask in range(1 << 15):
            rx = link.Receiver()
            rx.feed(link.encode(7, mask), 0)
            self.assertEqual(rx.mask, mask)

    def test_any_single_bit_error_in_a_frame_is_rejected(self):
        frame = link.encode(3, 0x1234)
        for bit in range(8 * (link.FRAME_LEN - 1)):  # every bit after SYNC
            bad = bytearray(frame)
            bad[1 + bit // 8] ^= 1 << (bit % 8)
            rx = link.Receiver()
            rx.feed(bytes(bad), 0)
            self.assertIsNone(rx.last_ok_ms, f"bit {bit} accepted")

    def test_resynchronises_after_garbage_and_a_truncated_frame(self):
        rx = link.Receiver()
        rx.feed(b"\x00\xff\x13" + link.encode(1, 0b101)[:3], 0)
        rx.feed(link.encode(2, 0b101), 5)
        self.assertEqual(rx.mask, 0b101)
        self.assertEqual(rx.last_seq, 2)

    def test_sequence_gaps_are_counted(self):
        rx = link.Receiver()
        rx.feed(link.encode(10, 1), 0)
        rx.feed(link.encode(13, 1), 10)
        self.assertEqual(rx.dropped, 2)
        rx.feed(link.encode(255, 1), 20)
        rx.feed(link.encode(0, 1), 30)
        self.assertEqual(rx.dropped, 2 + (255 - 13 - 1) + 0)

    def test_press_and_release_are_seen_within_one_frame(self):
        order = link.button_order()
        rx, samples = link.simulate({20: 1 << order.index("H"), 60: 0}, 100)
        self.assertEqual(dict(samples)[19]["pressed"], set())
        self.assertEqual(dict(samples)[20]["pressed"], {"H"})   # same millisecond: sent on change
        self.assertEqual(dict(samples)[60]["pressed"], set())

    def test_one_lost_frame_does_not_trip_the_timeout_but_a_dead_link_does(self):
        dropped_once = lambda t, f: b"" if t == 30 else f
        rx, samples = link.simulate({0: 1}, 100, corrupt=dropped_once)
        self.assertTrue(all(s["status"] == "ok" for _, s in samples), "a single lost frame tripped link-lost")
        rx, samples = link.simulate({0: 1}, 200, corrupt=lambda t, f: f if t < 40 else b"")
        status = dict(samples)
        self.assertEqual(status[40 + 0]["status"], "ok")
        self.assertEqual(status[200]["status"], "link-lost")
        self.assertEqual(status[200]["pressed"], set())
        first_lost = next(t for t, s in samples if s["status"] == "link-lost")
        self.assertLessEqual(first_lost - 30, link.TIMEOUT_MS + link.SEND_PERIOD_MS)

    def test_every_button_pressed_at_once_means_gamepad_off_not_input(self):
        rx, samples = link.simulate({10: link.WIRED_MASK}, 50)
        self.assertEqual(dict(samples)[30]["status"], "gamepad-off")
        self.assertEqual(dict(samples)[30]["pressed"], set())

    def test_corrupted_frames_never_produce_a_phantom_press(self):
        import random
        rng = random.Random(1)
        flip = lambda t, f: bytes(b ^ (1 << rng.randrange(8)) if rng.random() < 0.15 else b for b in f)
        rx, samples = link.simulate({0: 0}, 2000, corrupt=flip)
        for t, s in samples:
            self.assertEqual(s["pressed"], set(), f"phantom press at {t} ms")


class DevKitCDatasheet(unittest.TestCase):
    """The proposed WROOM pins against the Espressif header tables and module datasheet recorded in hardware/devkitc-v4-header.json."""
    def setUp(self):
        self.board = json.loads((ROOT / "hardware/devkitc-v4-header.json").read_text(encoding="utf-8"))
        self.exposed = {e["gpio"] for side in ("j2_left", "j3_right") for e in self.board[side] if "gpio" in e}
        self.module = self.board["module"]
        self.wroom = REGISTRY["wroom"]

    def test_headers_have_19_positions_each(self):
        for side in ("j2_left", "j3_right"):
            self.assertEqual([e["pos"] for e in self.board[side]], list(range(1, 20)))

    def test_every_mapped_pin_is_on_the_header(self):
        for e in self.wroom["inputs"] + self.wroom["reserved"] + self.wroom["spare"]:
            self.assertIn(e["gpio"], self.exposed, e)
        self.assertIn(self.wroom["uart_tx_gpio"], self.exposed)

    def test_no_mapped_pin_is_a_strap_flash_or_console_pin(self):
        bad = set(self.module["strapping_gpios"]) | set(self.module["flash_gpios"]) | {1, 3}
        for e in self.wroom["inputs"] + self.wroom["reserved"] + self.wroom["spare"]:
            self.assertNotIn(e["gpio"], bad, e)

    def test_input_only_list_matches_the_datasheet(self):
        self.assertEqual(set(self.wroom["input_only"]), set(self.module["input_only_gpios"]))

    def test_candidates_are_exactly_the_free_header_gpios(self):
        free = self.exposed - set(self.module["strapping_gpios"]) - set(self.module["flash_gpios"]) - {1, 3, self.wroom["uart_tx_gpio"]}
        self.assertEqual(set(self.wroom["candidates"]), free)

    def test_gamepad_released_level_clears_the_input_high_threshold_and_power_is_not_wired(self):
        vdd = 3.3
        self.assertGreater(3.0, self.module["vih_min_fraction_of_vdd"] * vdd)  # about 3.0 V released, owner-reported
        # K_POW may be at battery voltage; the input limit is VDD + 0.3 V, so it stays reserved, not wired
        self.assertEqual([e["signal"] for e in self.wroom["reserved"]], ["K_POW"])


if __name__ == "__main__":
    unittest.main()
