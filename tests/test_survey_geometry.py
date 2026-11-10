"""Tests for scripts/cad/survey_geometry.py using SYNTHETIC shapes defined here only.

None of these numbers are measurements of the gamepad.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('survey_geometry', ROOT / 'scripts/cad/survey_geometry.py')
geo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geo)


def record(**over):
    base = {
        'origin_description': 'SYNTHETIC datum: lower-left of bounding box',
        'readings': [
            {'id': 'W', 'value_mm': 100.0, 'state': 'measured'},
            {'id': 'H', 'value_mm': 50.0, 'state': 'measured'},
            {'id': 'T', 'value_mm': 1.6, 'state': 'measured'},
            {'id': 'A', 'value_mm': 4.0, 'state': 'measured'},
        ],
        'outline': {'state': 'measured', 'points_mm': [[0, 0], [100, 0], [100, 50], [0, 50]]},
        'mounting_holes': [],
    }
    base.update(over)
    return base


class SurveyGeometry(unittest.TestCase):
    def test_public_record_without_outline_builds_nothing(self):
        record_path = ROOT / 'measurements/boards/gamepad-gh-wii-u002.json'
        survey = json.loads(record_path.read_text())
        if survey['outline']['points_mm'] or survey['mounting_holes']:
            self.skipTest('Measured geometry has been recorded; covered by the other tests')
        result = geo.resolve(survey)
        self.assertIsNone(result['outline'])
        self.assertEqual(result['holes'], [])

    def test_rectangle_volume(self):
        result = geo.resolve(record())
        self.assertAlmostEqual(result['outline']['net_area_mm2'], 5000)
        self.assertAlmostEqual(result['volume_mm3'], 5000 * 1.6)

    def test_hole_diameter_comes_from_reading_with_same_id(self):
        s = record(mounting_holes=[{'id': 'A', 'x_mm': 20, 'y_mm': 25, 'state': 'measured'}])
        result = geo.resolve(s)
        self.assertAlmostEqual(result['holes'][0]['radius'], 2.0)
        self.assertAlmostEqual(result['outline']['net_area_mm2'], 5000 - math.pi * 4)

    def test_pending_hole_is_listed_but_not_built(self):
        s = record(mounting_holes=[{'id': 'B', 'x_mm': None, 'y_mm': None, 'state': 'pending'}])
        self.assertEqual(geo.resolve(s)['holes'], [])

    def test_slot(self):
        s = record(mounting_holes=[{'id': 'E', 'x_mm': 50, 'y_mm': 25, 'diameter_mm': 4,
                                    'slot_length_mm': 10, 'angle_deg': 0, 'state': 'measured'}])
        hole = geo.resolve(s)['holes'][0]
        self.assertAlmostEqual(hole['p1'][0], 47)
        self.assertAlmostEqual(hole['p2'][0], 53)

    def test_arc_corner_stays_within_box_and_simple(self):
        r = 10
        pts = [[r, 0], [100, 0], [100, 50], [0, 50], [0, r],
               {'to': [r, 0], 'via': [r - r * math.cos(math.pi / 4), r - r * math.sin(math.pi / 4)]}]
        result = geo.resolve(record(outline={'state': 'measured', 'points_mm': pts}))
        self.assertAlmostEqual(result['outline']['bbox'][0], 0, places=6)
        self.assertAlmostEqual(result['outline']['net_area_mm2'], 5000 - r * r * (1 - math.pi / 4), delta=0.05)

    def test_requires_datum(self):
        with self.assertRaisesRegex(ValueError, 'origin_description'):
            geo.resolve(record(origin_description=None))

    def test_points_without_measured_state_rejected(self):
        s = record()
        s['outline']['state'] = 'unmeasured'
        with self.assertRaisesRegex(ValueError, 'not .measured'):
            geo.resolve(s)

    def test_outline_must_agree_with_measured_width_and_height(self):
        s = record()
        s['outline']['points_mm'] = [[0, 0], [90, 0], [90, 50], [0, 50]]
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            geo.resolve(s)

    def test_hole_outside_or_on_edge_rejected(self):
        for x in (150, 1.0):
            s = record(mounting_holes=[{'id': 'A', 'x_mm': x, 'y_mm': 25, 'state': 'measured'}])
            with self.assertRaises(ValueError):
                geo.resolve(s)

    def test_overlapping_holes_rejected(self):
        s = record(mounting_holes=[{'id': 'A', 'x_mm': 20, 'y_mm': 25, 'state': 'measured'},
                                   {'id': 'B', 'x_mm': 23, 'y_mm': 25, 'diameter_mm': 4, 'state': 'measured'}])
        with self.assertRaisesRegex(ValueError, 'overlap'):
            geo.resolve(s)

    def test_self_crossing_outline_rejected(self):
        s = record(outline={'state': 'measured', 'points_mm': [[0, 0], [100, 50], [100, 0], [0, 50]]})
        with self.assertRaisesRegex(ValueError, 'crosses'):
            geo.resolve(s)

    def test_nonfinite_and_boolean_values_rejected(self):
        for bad in (float('nan'), True, '5', None):
            s = record(mounting_holes=[{'id': 'A', 'x_mm': bad, 'y_mm': 25, 'state': 'measured'}])
            with self.assertRaises(ValueError):
                geo.resolve(copy.deepcopy(s))

    def test_holes_without_outline_rejected(self):
        s = record(outline={'state': 'unmeasured', 'points_mm': []},
                   mounting_holes=[{'id': 'A', 'x_mm': 20, 'y_mm': 25, 'state': 'measured'}])
        with self.assertRaisesRegex(ValueError, 'outline'):
            geo.resolve(s)


if __name__ == '__main__':
    unittest.main()
