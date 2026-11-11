"""Consistency tests for the harness package: the connection list, ordering list and plan must agree with the
pad table and the harness registry, so the proposal cannot drift from the records it refers to."""
import csv
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'electronics/harness-sources-proposed.csv'
PROCURE = ROOT / 'electronics/harness-procurement-proposed.csv'
SHEET = ROOT / 'measurements/templates/harness-continuity-sheet.csv'
PLAN = (ROOT / 'docs/HARNESS_PLAN.md').read_text(encoding='utf-8')
STATUSES = {'plan-ready', 'blocked', 'hold', 'retained'}


def rows(path):
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle, restkey='_extra'))


class ConnectionList(unittest.TestCase):
    def setUp(self):
        self.rows = rows(SOURCES)
        self.pads = {r['id']: r for r in rows(ROOT / 'measurements/boards/gamepad-gh-wii-u002-pads.csv')}

    def test_well_formed_and_known_status(self):
        self.assertTrue(self.rows)
        for r in self.rows:
            self.assertNotIn('_extra', r)
            self.assertIn(r['status'], STATUSES, r['signal'])

    def test_every_referenced_pad_exists(self):
        for r in self.rows:
            for pid in filter(None, r['source_pads'].split('|')):
                self.assertIn(pid, self.pads, f"{r['harness']} {r['signal']} cites missing pad {pid}")

    def test_stated_label_position_and_confidence_match_the_pad_table(self):
        for r in self.rows:
            if not r['pad_label'] and not r['x_mm']:
                continue
            first = self.pads[r['source_pads'].split('|')[0]]
            self.assertEqual(r['pad_label'], first['label'])
            self.assertEqual((r['x_mm'], r['y_mm']), (first['x_mm'], first['y_mm']))
            self.assertEqual(r['pad_confidence'], first['label_confidence'])

    def test_plan_ready_needs_a_single_labelled_high_confidence_pad(self):
        for r in self.rows:
            if r['status'] == 'plan-ready':
                ids = r['source_pads'].split('|')
                self.assertEqual(len(ids), 1, f"{r['signal']} has several candidate pads")
                self.assertEqual(self.pads[ids[0]]['label_confidence'], 'high', r['signal'])
                self.assertTrue(self.pads[ids[0]]['label'], r['signal'])

    def test_blocked_and_held_rows_say_what_blocks_them(self):
        for r in self.rows:
            if r['status'] == 'blocked':
                self.assertTrue(r['gate'].strip(), f"{r['signal']} is blocked with no gate")
            if r['status'] in ('blocked', 'hold'):
                self.assertTrue(r['notes'].strip(), r['signal'])

    def test_j1_matches_the_harness_registry(self):
        registry = json.loads((ROOT / 'electronics/harnesses.json').read_text(encoding='utf-8'))
        j1 = {p['signal']: str(p['pin']) for p in next(h for h in registry['harnesses'] if h['id'] == 'J1')['pins']}
        ours = {r['signal']: r['pin'] for r in self.rows if r['harness'] == 'J1'}
        self.assertEqual(ours, j1)

    def test_power_and_bus_are_never_marked_ready(self):
        for r in self.rows:
            if r['harness'] in ('J3', 'NONE'):
                self.assertEqual(r['status'], 'hold', r['signal'])

    def test_no_pad_is_claimed_by_two_plan_ready_signals(self):
        used = [r['source_pads'] for r in self.rows if r['status'] == 'plan-ready']
        self.assertEqual(len(used), len(set(used)))

    def test_gates_that_name_a_decision_or_measurement_exist_in_the_plan(self):
        for r in self.rows:
            for ref in re.findall(r'\b[DM]\d\b', r['gate']):
                self.assertIn(f'**{ref}.', PLAN, f"{ref} is cited but not defined in HARNESS_PLAN.md")


class ButtonHarness(unittest.TestCase):
    """J2A and J2B: every useful button on a free test pad, and a check sheet that covers each one."""
    def setUp(self):
        self.rows = rows(SOURCES)
        self.pads = {r['id']: r for r in rows(ROOT / 'measurements/boards/gamepad-gh-wii-u002-pads.csv')}
        self.sheet = rows(ROOT / 'measurements/templates/button-check-sheet.csv')

    def test_connector_positions_are_complete_and_unique(self):
        for harness, size in (('J1', 8), ('J2A', 8), ('J2B', 10)):
            pins = [int(r['pin']) for r in self.rows if r['harness'] == harness]
            self.assertEqual(sorted(pins), list(range(1, size + 1)), harness)

    def test_no_signal_wire_lands_on_a_ribbon_power_or_bus_pad(self):
        forbidden = {'right-stick-ribbon', 'left-stick-ribbon', 'SW1', 'SW2', 'battery-footprint', 'motor'}
        for r in self.rows:
            if r['harness'] in ('J1', 'J2A', 'J2B'):
                for pid in filter(None, r['source_pads'].split('|')):
                    pad = self.pads[pid]
                    self.assertNotIn(pad['group'], forbidden, f"{r['signal']} taps {pid}")
                    if pad['group'] == 'power-bus':
                        self.assertEqual(pad['label'], 'GND', f"{r['signal']} taps {pid}")

    def test_signal_name_is_the_printed_pad_label(self):
        for r in self.rows:
            if r['harness'] in ('J2A', 'J2B') and r['status'] == 'plan-ready':
                self.assertEqual(r['signal'], self.pads[r['source_pads']]['label'])

    def test_every_button_and_click_has_a_blank_check_row_for_each_candidate_pad(self):
        wanted = {(r['signal'], pid) for r in self.rows if r['harness'] in ('J1', 'J2A', 'J2B')
                  and r['function'] and 'analog' not in r['function'] and 'reference' not in r['function']
                  for pid in r['source_pads'].split('|')}
        self.assertEqual({(r['signal'], r['expected_pad']) for r in self.sheet}, wanted)
        self.assertEqual(len(wanted), 18)
        for r in self.sheet:
            self.assertIn(r['state'], {'pending', 'owner-reported'})
            if r['state'] == 'pending':
                for column in ('pad_to_contact_continuity', 'released_v', 'pressed_v', 'instrument', 'date'):
                    self.assertEqual(r[column], '', f"{r['id']} has a reading recorded before it was taken")

    def test_prefilled_rows_only_restate_readings_in_the_electrical_ledger(self):
        ledger = rows(ROOT / 'measurements/electrical.csv')
        for r in self.sheet:
            if r['state'] != 'owner-reported':
                continue
            cited = set(re.findall(r'BTN\d+', r['notes']))
            self.assertEqual(len(cited), 2, r['id'])
            found = {e['id']: e for e in ledger if e['id'] in cited}
            self.assertEqual(set(found), cited, r['id'])
            self.assertEqual({float(e['value']) for e in found.values()}, {float(r['released_v']), float(r['pressed_v'])})
            for e in found.values():
                self.assertTrue(e['quantity'].startswith(r['signal']), f"{r['id']} cites {e['id']} ({e['quantity']})")
                self.assertEqual((e['instrument'], e['date']), (r['instrument'], r['date']))


class OrderingList(unittest.TestCase):
    def setUp(self):
        self.rows = rows(PROCURE)

    def test_status_quantity_and_reason(self):
        for r in self.rows:
            self.assertIn(r['status'], {'buy-now', 'buy-after-decision', 'hold'}, r['line'])
            self.assertTrue(r['decision_or_reason'].strip(), r['line'])
            self.assertTrue(r['qty'].strip(), r['line'])
        self.assertEqual(len({r['line'] for r in self.rows}), len(self.rows))

    def test_nothing_that_needs_a_decision_is_marked_buy_now_without_being_an_evaluation_item(self):
        for r in self.rows:
            if r['status'] == 'buy-now' and r['needed_for'] in ('D1', 'D1; D2'):
                self.assertEqual(r['category'], 'connector eval', r['line'])

    def test_after_decision_rows_name_a_decision(self):
        for r in self.rows:
            if r['status'] == 'buy-after-decision':
                self.assertRegex(r['decision_or_reason'], r'\b[DM]\d\b', r['line'])

    def test_connector_part_numbers_carry_a_verify_note(self):
        for r in self.rows:
            if r['category'] == 'connector eval':
                self.assertTrue(r['verify_before_ordering'].strip() and r['verify_before_ordering'] != 'none', r['line'])

    def test_held_items_are_never_quantified(self):
        for r in self.rows:
            if r['status'] == 'hold':
                self.assertEqual(r['qty'], '0', r['line'])

    def test_every_decision_in_the_list_is_defined_in_the_plan(self):
        for r in self.rows:
            for ref in re.findall(r'\b[DM]\d\b', r['decision_or_reason'] + ' ' + r['needed_for']):
                self.assertIn(f'**{ref}.', PLAN, f'{ref} is cited but not defined')


class ContinuitySheet(unittest.TestCase):
    def test_rows_point_at_real_plan_ready_pads_and_start_blank(self):
        pads = {r['id']: r for r in rows(ROOT / 'measurements/boards/gamepad-gh-wii-u002-pads.csv')}
        ready = {r['signal']: r['source_pads'] for r in rows(SOURCES) if r['status'] == 'plan-ready'}
        for r in rows(SHEET):
            self.assertEqual(r['state'], 'proposed')
            self.assertEqual(ready.get(r['signal']), r['from_pad'], r['wire_id'])
            self.assertIn(r['from_pad'], pads)
            for column in ('continuity_ohm', 'tester', 'date'):
                self.assertEqual(r[column], '', f"{r['wire_id']} has a result recorded before it was built")


class PlanDocument(unittest.TestCase):
    def test_decisions_and_measurements_are_defined(self):
        for ref in [f'D{i}' for i in range(1, 7)] + [f'M{i}' for i in range(1, 8)]:
            self.assertIn(f'**{ref}.', PLAN)

    def test_it_does_not_claim_to_replace_the_registry(self):
        self.assertIn('remain the authority', PLAN)


if __name__ == '__main__':
    unittest.main()
