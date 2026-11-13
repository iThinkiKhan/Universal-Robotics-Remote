import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('axis_analysis',ROOT/'tools/analyze_axis.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def synthetic(mv=0,age=0,pin=5):
    return '\n'.join(f'AXIS available=1 active=1 valid=1 pin={pin} samples={i*10} raw=0 filtered=0 mv_est={mv} age_ms={age} elapsed_ms={i*100} errors=0' for i in range(1,51))

class AxisDiagnostics(unittest.TestCase):
    def test_ground_record_acceptance_and_wrong_reference(self):
        self.assertTrue(module.analyze(synthetic(),'ground')['passed'])
        self.assertFalse(module.analyze(synthetic(mv=1500),'ground')['passed'])
    def test_stale_wrong_pin_and_incomplete_records_fail(self):
        for text in [synthetic(age=500),synthetic(pin=6),'','AXIS available=1 active=1 valid=1 pin=5']:
            self.assertFalse(module.analyze(text)['passed'])
    def test_restarted_session_is_not_misreported_as_continuous(self):
        self.assertFalse(module.analyze(synthetic()+'\n'+synthetic())['passed'])
    def test_bench_model_agrees_with_canonical_pin_and_proposed_state(self):
        model=json.loads((ROOT/'hardware/bench/lx-observer.json').read_text())
        registry=json.loads((ROOT/'hardware/signals.json').read_text())
        axis=next(s for s in registry['signals'] if s['id']==model['signal_id'])
        self.assertEqual(axis['gpio'],model['gpio']);self.assertEqual(axis['state'],'proposed')
        self.assertFalse(registry['gamepad_enabled']);self.assertFalse(model['boot_sampling'])
        self.assertFalse(model['unpowered_connected_input_allowed'])
        self.assertFalse(model['shared_power_rails'])
    def test_blank_session_template_has_consistent_columns(self):
        import csv
        with (ROOT/'measurements/templates/lx-observer-session.csv').open(newline='') as f:
            rows=list(csv.reader(f))
        self.assertTrue(all(len(r)==len(rows[0]) for r in rows))
        for row in rows[1:]:self.assertEqual(row[rows[0].index('result')],'')

if __name__=='__main__':unittest.main()
