"""The 3D harness model's tap data must agree with the registry, the connection list and the pad table."""
import csv
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('harness_taps', ROOT / 'scripts/cad/harness_taps.py')
taps_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(taps_module)


class HarnessTaps(unittest.TestCase):
    def setUp(self):
        self.taps, self.wires = taps_module.collect(ROOT)
        self.registry = json.loads((ROOT / 'electronics/harnesses.json').read_text(encoding='utf-8'))
        with (ROOT / 'measurements/boards/gamepad-gh-wii-u002-pads.csv').open(newline='', encoding='utf-8') as handle:
            self.pads = {r['id'] for r in csv.DictReader(handle)}

    def test_one_wire_per_registered_position(self):
        registered = {f"{h['id']}-W{p['pin']:02d}": p['signal'] for h in self.registry['harnesses'] for p in h['pins']}
        self.assertEqual({w['wire_id']: w['signal'] for w in self.wires}, registered)
        self.assertEqual(len(self.wires), 28)

    def test_every_tap_is_a_recorded_pad_and_every_wire_lands_somewhere(self):
        landed = set()
        for tap in self.taps:
            self.assertIn(tap['pad'], self.pads)
            landed |= {w['wire_id'] for w in tap['wires']}
        self.assertEqual(landed, {w['wire_id'] for w in self.wires})

    def test_held_positions_get_no_tap(self):
        self.assertNotIn('TP61', {t['pad'] for t in self.taps})      # POWER (K_POW) is held, not wired

    def test_unsettled_wires_are_flagged_on_each_candidate_pad(self):
        for wire in self.wires:
            on = [t for t in self.taps if any(w['wire_id'] == wire['wire_id'] for w in t['wires'])]
            self.assertEqual(len(on), len(wire['pads']), wire['wire_id'])
            for tap in on:
                self.assertEqual(tap['settled'] and len(wire['pads']) > 1, False, wire['wire_id'])

    def test_marker_colour_is_the_connector_or_the_shared_colour(self):
        for tap in self.taps:
            if len(tap['connectors']) == 1:
                self.assertEqual(tap['rgb'], taps_module.MARKER_RGB[tap['connectors'][0]])
            else:
                self.assertEqual(tap['rgb'], taps_module.SHARED_RGB)

    def test_the_built_model_matches_the_current_connection_list(self):
        report = json.loads((ROOT / 'cad/harness/gamepad-harness-r001-validation.json').read_text(encoding='utf-8'))
        self.assertEqual(report['tap_markers'], len(self.taps))
        self.assertEqual(report['wires'], len(self.wires))
        self.assertEqual(report['connection_list_sha256'],
                         taps_module.lf_sha256(ROOT / 'electronics/harness-sources-proposed.csv'))


if __name__ == '__main__':
    unittest.main()
