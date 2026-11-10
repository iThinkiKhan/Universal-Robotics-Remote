import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hardware", ROOT / "tools/generate_hardware.py")
hardware = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hardware)


class HardwareContract(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((ROOT / "hardware/signals.json").read_text())
        self.harnesses = json.loads((ROOT / "electronics/harnesses.json").read_text())

    def test_current_contract(self):
        hardware.validate(self.registry, self.harnesses)

    def test_duplicate_pin_is_rejected(self):
        self.registry["signals"][-1]["gpio"] = 5
        with self.assertRaisesRegex(ValueError, "Pin conflict"):
            hardware.validate(self.registry, self.harnesses)

    def test_straps_usb_memory_and_uart_are_rejected_for_axes(self):
        for pin in [0, 3, 19, 20, 26, 35, 36, 37, 43, 44, 45, 46, 49, True]:
            with self.subTest(pin=pin):
                registry = copy.deepcopy(self.registry)
                next(s for s in registry["signals"] if s["id"] == "R-Y")["gpio"] = pin
                with self.assertRaises(ValueError):
                    hardware.validate(registry, self.harnesses)

    def test_non_adc1_axis_is_rejected(self):
        next(s for s in self.registry["signals"] if s["id"] == "R-Y")["gpio"] = 14
        with self.assertRaisesRegex(ValueError, "ADC1"):
            hardware.validate(self.registry, self.harnesses)

    def test_unknown_harness_signal_is_rejected(self):
        self.harnesses["harnesses"][0]["pins"][0]["signal"] = "R-XX"
        with self.assertRaisesRegex(ValueError, "Unknown harness signal"):
            hardware.validate(self.registry, self.harnesses)

    def test_duplicate_connector_position_is_rejected(self):
        self.harnesses["harnesses"][0]["pins"][1]["pin"] = 1
        with self.assertRaisesRegex(ValueError, "connector position"):
            hardware.validate(self.registry, self.harnesses)

    def test_early_gamepad_activation_is_rejected(self):
        self.registry["gamepad_enabled"] = True
        with self.assertRaisesRegex(ValueError, "disabled"):
            hardware.validate(self.registry, self.harnesses)

    def test_existing_wiring_cannot_silently_change(self):
        next(s for s in self.registry["signals"] if s["id"] == "tft_sck")["gpio"] = 14
        with self.assertRaisesRegex(ValueError, "assembly changed"):
            hardware.validate(self.registry, self.harnesses)


if __name__ == "__main__":
    unittest.main()
