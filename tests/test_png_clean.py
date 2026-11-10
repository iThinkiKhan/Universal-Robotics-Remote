import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('png_clean', ROOT / 'scripts/cad/png_clean.py')
png_clean = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png_clean)


def chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)


def sample_png(text_path):
    ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b'\x00\xff\x00\x00')
    return (png_clean.SIGNATURE + chunk(b'IHDR', ihdr) + chunk(b'pHYs', struct.pack('>IIB', 2835, 2835, 1))
            + chunk(b'tEXt', b'Title\x00' + text_path)
            + chunk(b'zTXt', b'Description\x00\x00' + zlib.compress(b'<View>' + text_path + b'</View>'))
            + chunk(b'IDAT', idat) + chunk(b'IEND', b''))


class PngClean(unittest.TestCase):
    def test_text_chunks_and_paths_are_removed_but_pixels_survive(self):
        secret = b'/build/output/render.png'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'r.png'
            original = sample_png(secret)
            path.write_bytes(original)
            self.assertIn(secret, original)
            self.assertTrue(png_clean.strip_png_metadata(path))
            cleaned = path.read_bytes()
            self.assertNotIn(secret, cleaned)
            self.assertNotIn(b'tEXt', cleaned)
            self.assertNotIn(b'zTXt', cleaned)
            for kept in (b'IHDR', b'pHYs', b'IDAT', b'IEND'):
                self.assertIn(kept, cleaned)
            self.assertFalse(png_clean.strip_png_metadata(path))      # idempotent

    def test_rejects_non_png(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'x.png'
            path.write_bytes(b'not a png')
            with self.assertRaises(ValueError):
                png_clean.strip_png_metadata(path)

    def test_published_renders_carry_no_text_chunks(self):
        for image in sorted((ROOT / 'exports').rglob('*.png')):
            data = image.read_bytes()
            for kind in (b'tEXt', b'zTXt', b'iTXt', b'eXIf'):
                self.assertNotIn(kind, data, f'{image.name} still has a {kind.decode()} chunk')


if __name__ == '__main__':
    unittest.main()
