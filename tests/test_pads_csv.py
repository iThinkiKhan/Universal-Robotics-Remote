"""Tests for the test-pad table and its loader (SYNTHETIC cases are defined here only)."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('survey_geometry', ROOT / 'scripts/cad/survey_geometry.py')
geo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geo)

COLUMNS = ['id', 'label', 'group', 'shape', 'x_mm', 'y_mm', 'diameter_mm', 'width_mm', 'length_mm',
           'label_confidence', 'state', 'method', 'uncertainty_mm', 'date', 'evidence', 'notes']


def write(folder, rows):
    path = Path(folder) / 'pads.csv'
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({**{c: '' for c in COLUMNS}, **row})
    return path


def pad(pid='T1', **over):
    base = {'id': pid, 'label': 'X', 'group': 'g', 'shape': 'round', 'x_mm': '30', 'y_mm': '25', 'diameter_mm': '1.2',
            'label_confidence': 'high', 'state': 'traced', 'method': 'synthetic', 'uncertainty_mm': '0.4'}
    base.update(over)
    return base


def board(**over):
    survey = {
        'origin_description': 'SYNTHETIC datum',
        'readings': [{'id': 'W', 'value_mm': 100.0, 'state': 'measured'}, {'id': 'H', 'value_mm': 50.0, 'state': 'measured'},
                     {'id': 'T', 'value_mm': 1.6, 'state': 'measured'}],
        'outline': {'state': 'measured', 'points_mm': [[0, 0], [100, 0], [100, 50], [0, 50]]},
        'mounting_holes': [{'id': 'H1', 'x_mm': 50, 'y_mm': 25, 'diameter_mm': 4, 'state': 'measured'}],
    }
    survey.update(over)
    return survey


class PadLoader(unittest.TestCase):
    def load(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            return geo.load_pads(write(folder, rows))

    def test_valid_round_rect_and_oval(self):
        pads = self.load([pad('A'), pad('B', shape='rect', diameter_mm='', width_mm='1', length_mm='3'),
                          pad('C', shape='oval', diameter_mm='', width_mm='1.5', length_mm='2.4', x_mm='40')])
        self.assertEqual([p['shape'] for p in pads], ['round', 'rect', 'oval'])
        self.assertEqual((pads[1]['w'], pads[1]['l']), (1.0, 3.0))

    def test_unlabeled_pad_is_allowed_and_stays_unlabeled(self):
        self.assertEqual(self.load([pad(label='')])[0]['label'], '')

    def test_rejections(self):
        bad = [
            [pad('A'), pad('A', x_mm='40')],                                   # duplicate id
            [pad('A', shape='hexagon')],                                       # unknown shape
            [pad('A', diameter_mm='')],                                        # round without a diameter
            [pad('A', shape='rect', diameter_mm='', width_mm='1')],            # rect without a length
            [pad('A', x_mm='abc')],                                            # not a number
            [pad('A', diameter_mm='-1')],                                      # not positive
            [pad('A', state='pending')],                                       # only measured / traced rows belong here
            [pad('A', label_confidence='certain')],                            # unknown confidence word
            [pad('A', uncertainty_mm='')],                                     # traced without uncertainty
            [pad('A', method='')],                                             # traced without method
        ]
        for rows in bad:
            with self.assertRaises(ValueError, msg=str(rows)):
                self.load(rows)


class PadValidation(unittest.TestCase):
    def check(self, pads, **over):
        geo.validate_pads(pads, geo.resolve(board(**over)))

    def pads(self, *rows):
        with tempfile.TemporaryDirectory() as folder:
            return geo.load_pads(write(folder, list(rows)))

    def test_pad_on_the_board_passes(self):
        self.check(self.pads(pad('A', x_mm='10', y_mm='10')))

    def test_pad_outside_the_outline_or_over_the_edge_rejected(self):
        for x in ('150', '0.2'):
            with self.assertRaises(ValueError):
                self.check(self.pads(pad('A', x_mm=x, y_mm='10')))

    def test_pad_over_a_hole_rejected(self):
        with self.assertRaisesRegex(ValueError, 'overlaps hole'):
            self.check(self.pads(pad('A', x_mm='51', y_mm='25')))

    def test_duplicate_positions_rejected(self):
        with self.assertRaisesRegex(ValueError, 'less than 0.5 mm'):
            self.check(self.pads(pad('A', x_mm='10', y_mm='10'), pad('B', x_mm='10.2', y_mm='10')))

    def test_pads_need_an_outline(self):
        with self.assertRaisesRegex(ValueError, 'outline'):
            self.check(self.pads(pad('A', x_mm='10', y_mm='10')), outline={'state': 'unmeasured', 'points_mm': []})


class PublicPadTable(unittest.TestCase):
    def setUp(self):
        self.survey = json.loads((ROOT / 'measurements/boards/gamepad-gh-wii-u002.json').read_text(encoding='utf-8'))
        self.path = ROOT / 'measurements/boards/gamepad-gh-wii-u002-pads.csv'

    def test_the_recorded_pads_load_and_sit_on_the_recorded_board(self):
        pads = geo.load_pads(self.path)
        self.assertGreater(len(pads), 30)
        geo.validate_pads(pads, geo.resolve(self.survey))

    def test_every_pad_is_traced_never_passed_off_as_measured(self):
        for p in geo.load_pads(self.path):
            self.assertEqual(p['state'], 'traced', p['id'])
            self.assertGreater(p['uncertainty_mm'], 0, p['id'])

    def test_low_confidence_pads_carry_an_explanation(self):
        with self.path.open(newline='', encoding='utf-8') as handle:
            for row in csv.DictReader(handle):
                if row['label_confidence'] == 'low':
                    self.assertTrue(row['notes'].strip(), f"{row['id']} is low confidence but has no note")

    def test_the_board_record_points_at_this_file(self):
        self.assertEqual(self.survey.get('pads_file'), 'measurements/boards/gamepad-gh-wii-u002-pads.csv')


if __name__ == '__main__':
    unittest.main()
