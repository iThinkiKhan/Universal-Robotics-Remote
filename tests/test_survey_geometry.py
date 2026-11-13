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
    def test_public_record_has_no_invented_outline(self):
        survey = json.loads((ROOT / 'measurements/boards/gamepad-gh-wii-u002.json').read_text())
        if survey['outline']['state'] not in ('measured', 'traced'):
            self.assertEqual(survey['outline']['points_mm'], [])  # nothing may be traced until measured
            self.assertIsNone(geo.resolve(survey)['outline'])

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

    def test_traced_outline_needs_method_and_uncertainty(self):
        pts = [[0, 0], [100, 0], [100, 50], [0, 50]]
        base = {'state': 'traced', 'points_mm': pts}
        for bad in (base, {**base, 'method': 'photo'}, {**base, 'method': 'photo', 'uncertainty_mm': 0},
                    {**base, 'method': ' ', 'uncertainty_mm': 0.4}, {**base, 'method': 'photo', 'uncertainty_mm': True}):
            with self.assertRaises(ValueError):
                geo.resolve(record(outline=bad))
        ok = geo.resolve(record(outline={**base, 'method': 'rectified photo', 'uncertainty_mm': 0.4}))
        self.assertEqual(ok['outline']['state'], 'traced')

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

    def test_holes_without_outline_are_cut_from_the_envelope_only(self):
        s = record(outline={'state': 'unmeasured', 'points_mm': []},
                   mounting_holes=[{'id': 'A', 'x_mm': 20, 'y_mm': 25, 'state': 'measured'}])
        result = geo.resolve(s)
        self.assertIsNone(result['outline'])
        self.assertTrue(result['envelope_holes'])
        self.assertAlmostEqual(result['volume_mm3'], (5000 - math.pi * 4) * 1.6)

    def test_holes_without_outline_need_w_h_and_t(self):
        s = record(outline={'state': 'unmeasured', 'points_mm': []},
                   mounting_holes=[{'id': 'A', 'x_mm': 20, 'y_mm': 25, 'state': 'measured'}])
        s['readings'] = [r for r in s['readings'] if r['id'] != 'T']
        with self.assertRaisesRegex(ValueError, 'W, H and T'):
            geo.resolve(s)

    def test_envelope_holes_must_fit_inside_the_rectangle(self):
        s = record(outline={'state': 'unmeasured', 'points_mm': []},
                   mounting_holes=[{'id': 'A', 'x_mm': 99, 'y_mm': 25, 'state': 'measured'}])
        with self.assertRaisesRegex(ValueError, 'breaks through'):
            geo.resolve(s)

    def test_near_wall_readings_become_centres(self):
        s = record(mounting_holes=[
            {'id': 'R', 'x_near_mm': 10, 'y_near_mm': 20, 'diameter_mm': 4, 'state': 'measured'},
            {'id': 'S', 'x_near_mm': 30, 'y_near_mm': 20, 'diameter_mm': 3, 'slot_length_mm': 6, 'state': 'measured'},
            {'id': 'T2', 'x_near_mm': 50, 'y_near_mm': 20, 'diameter_mm': 3, 'slot_length_mm': 6,
             'angle_deg': 90, 'state': 'measured'}])
        centres = {h['id']: h['center'] for h in geo.resolve(s)['holes']}
        self.assertEqual(centres['R'], (12, 22))
        self.assertEqual(centres['S'], (33, 21.5))      # 6 long along X, 3 wide along Y
        self.assertEqual(centres['T2'], (51.5, 23))      # 3 wide along X, 6 long along Y

    def test_near_wall_and_centre_together_rejected(self):
        s = record(mounting_holes=[{'id': 'R', 'x_near_mm': 10, 'y_near_mm': 20, 'x_mm': 12, 'y_mm': 22,
                                    'diameter_mm': 4, 'state': 'measured'}])
        with self.assertRaisesRegex(ValueError, 'not both'):
            geo.resolve(s)

    def test_near_wall_slot_must_be_axis_aligned(self):
        s = record(mounting_holes=[{'id': 'S', 'x_near_mm': 30, 'y_near_mm': 20, 'diameter_mm': 3,
                                    'slot_length_mm': 6, 'angle_deg': 45, 'state': 'measured'}])
        with self.assertRaisesRegex(ValueError, '0 or 90'):
            geo.resolve(s)

    def test_partially_measured_hole_is_listed_but_not_built(self):
        s = record(mounting_holes=[{'id': 'A', 'x_near_mm': None, 'y_near_mm': 49.2, 'state': 'partial'}])
        self.assertEqual(geo.resolve(s)['holes'], [])

    def test_public_record_resolves_and_holes_sit_where_near_wall_plus_half_size_says(self):
        survey = json.loads((ROOT / 'measurements/boards/gamepad-gh-wii-u002.json').read_text())
        result = geo.resolve(survey)
        for hole in result['holes']:
            raw = next(h for h in survey['mounting_holes'] if h['id'] == hole['id'])
            if 'x_near_mm' in raw:
                extent_x = raw.get('slot_length_mm', raw.get('diameter_mm', 0))
                if raw.get('angle_deg', 0) % 180 == 90:
                    extent_x = raw['diameter_mm']
                self.assertAlmostEqual(hole['center'][0], raw['x_near_mm'] + extent_x / 2)


if __name__ == '__main__':
    unittest.main()
