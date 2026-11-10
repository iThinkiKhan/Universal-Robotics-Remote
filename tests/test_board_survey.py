import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('board_survey', ROOT / 'scripts/cad/board_survey.py')
survey = importlib.util.module_from_spec(spec)
spec.loader.exec_module(survey)


class PublicBoardSurvey(unittest.TestCase):
    def test_public_project_needs_no_internal_instruction_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'README.md').write_text('# Example engineering project\n')
            photos = root / 'measurements/photos/example'
            photos.mkdir(parents=True)
            (photos / 'manifest.json').write_text(json.dumps({'photos': [{'filename': 'reference.jpg'}]}))
            output = survey.create(root, 'example', 'Example board', photos, 'reference.jpg')
            record = json.loads(output.read_text())
            self.assertEqual(record['state'], 'awaiting_measurements')
            self.assertTrue(all(reading['value_mm'] is None for reading in record['readings']))
            self.assertEqual(record['outline']['points_mm'], [])
            self.assertEqual(record['mounting_holes'], [])
            with self.assertRaises(ValueError):
                survey.create(root, 'example', 'Example board', photos, 'reference.jpg')


if __name__ == '__main__':
    unittest.main()
