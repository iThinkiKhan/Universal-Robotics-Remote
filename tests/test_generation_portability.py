import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hardware_generator', ROOT / 'tools/generate_hardware.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class GeneratorPortability(unittest.TestCase):
    def test_windows_and_linux_registry_newlines_have_same_digest(self):
        raw = (ROOT / 'hardware/signals.json').read_bytes().replace(b'\r\n', b'\n')
        self.assertEqual(generator.registry_digest(raw), generator.registry_digest(raw.replace(b'\n', b'\r\n')))


if __name__ == '__main__':
    unittest.main()
