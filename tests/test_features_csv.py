import csv
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / 'measurements/boards/gamepad-gh-wii-u002-features.csv'
NUMERIC = ('x_mm', 'y_mm', 'w_mm', 'l_mm', 'h_mm', 'uncertainty_mm')
STATES = {'pending', 'measured', 'owner-reported'}


class FeatureSheet(unittest.TestCase):
    def setUp(self):
        with FEATURES.open(newline='', encoding='utf-8') as handle:
            self.rows = list(csv.DictReader(handle, restkey='_extra'))

    def test_rows_are_well_formed_and_unique(self):
        self.assertTrue(self.rows)
        self.assertEqual(len({row['id'] for row in self.rows}), len(self.rows))
        for row in self.rows:
            self.assertNotIn('_extra', row, row['id'])
            self.assertTrue(all(value is not None for value in row.values()), row['id'])
            self.assertIn(row['state'], STATES, row['id'])

    def test_unmeasured_rows_carry_no_numbers(self):
        for row in self.rows:
            if row['state'] == 'pending':
                for column in NUMERIC + ('instrument', 'date'):
                    self.assertEqual(row[column], '', f"{row['id']} pending but {column} is filled")

    def test_measured_rows_have_datum_instrument_and_date(self):
        board = json.loads((ROOT / 'measurements/boards/gamepad-gh-wii-u002.json').read_text())
        for row in self.rows:
            if row['state'] != 'pending':
                self.assertTrue(row['date'] and row['instrument'], row['id'])
                self.assertTrue((board.get('origin_description') or '').strip(),
                                'Coordinates recorded but the board record names no datum')
                for column in ('x_mm', 'y_mm'):
                    float(row[column])


if __name__ == '__main__':
    unittest.main()
