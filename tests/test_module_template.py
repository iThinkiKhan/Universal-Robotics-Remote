"""The module measurement template and its three sheets must agree, and must hold no numbers until they are measured."""
import csv
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'measurements/templates/module-readings.csv'
SHEETS = ROOT / 'measurements/templates/modules'
MODULES = {'s3': 'S3-', 'display': 'D-', 'mic': 'M-'}


def rows():
    with TEMPLATE.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle, restkey='_extra'))


class ModuleTemplate(unittest.TestCase):
    def test_well_formed_and_unique(self):
        data = rows()
        self.assertTrue(data)
        ids = [r['id'] for r in data]
        self.assertEqual(len(ids), len(set(ids)))
        for r in data:
            self.assertNotIn('_extra', r)
            self.assertIn(r['module'], MODULES)
            self.assertTrue(r['id'].startswith(MODULES[r['module']]), r['id'])
            self.assertIn(r['tier'], {'1', '2', '3'}, r['id'])
            self.assertTrue(r['reading'].strip(), r['id'])

    def test_nothing_is_filled_in_before_it_is_measured(self):
        for r in rows():
            self.assertEqual(r['state'], 'pending', r['id'])
            for column in ('value', 'instrument', 'date'):
                self.assertEqual(r[column], '', f"{r['id']} has {column} recorded without a measurement")

    def test_every_module_has_tier_one_readings(self):
        for module in MODULES:
            self.assertTrue([r for r in rows() if r['module'] == module and r['tier'] == '1'], module)

    def test_each_sheet_lists_every_reading_of_its_module(self):
        for module in MODULES:
            sheet = (SHEETS / f'{module}-measurement-sheet.svg').read_text(encoding='utf-8')
            self.assertIn('NOT TO SCALE', sheet)
            for r in rows():
                if r['module'] == module:
                    self.assertIn(f">{r['id']}<", sheet, f"{r['id']} is missing from the {module} sheet")


if __name__ == '__main__':
    unittest.main()
