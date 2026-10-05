import copy
import json
from pathlib import Path
import tempfile
import unittest
from dispatcher.cutover_readiness import compare_snapshots, read_compare
from dispatcher.isolation import cell
from dispatcher.model import AGENT_JOB_COLUMNS, Status


def fixture():
    rows = []
    for index, status in enumerate(Status):
        row = [cell('string', '') for _ in range(17)]
        row[0] = cell('string', f'AJ-900{index}')
        row[4] = cell('string', status.value)
        rows.append(row)
    return dict(version=2, source=dict(workbook='synthetic', title='Agent Jobs', gid=0, range='A1:Q8'),
                capture=dict(reference='synthetic://capture', captured_at='2026-10-05T00:00:00Z',
                             complete=True, timezone='Etc/UTC'),
                columns=list(AGENT_JOB_COLUMNS), statuses=[s.value for s in Status], rows=rows,
                header_cells=[cell('string', x) for x in AGENT_JOB_COLUMNS],
                grid_metadata=dict(locale='en_US', timezone='Etc/UTC', frozen_rows=1, frozen_columns=1,
                                   row_count=8, column_count=17, date_policy='serials opaque; interpretation gated',
                                   provenance='synthetic://grid'),
                cell_provenance=[[dict(note=None, native_format=None, data_validation=None,
                                       provenance='synthetic://cell') for _ in range(17)] for _ in range(8)])


class ReadinessTests(unittest.TestCase):
    def test_exact_all_statuses(self):
        self.assertEqual(compare_snapshots(fixture(), fixture())['result'], 'PASS')

    def test_every_cell_and_metadata_mutation(self):
        source = fixture()
        for col in range(17):
            changed = copy.deepcopy(source)
            changed['rows'][0][col] = cell('string', 'changed')
            self.assertEqual(compare_snapshots(source, changed)['result'], 'HOLD')
        for section, key, value in [('source', 'gid', 1), ('capture', 'reference', 'other'),
                                    ('capture', 'complete', False), ('capture', 'timezone', 'UTC')]:
            changed = copy.deepcopy(source); changed[section][key] = value
            self.assertEqual(compare_snapshots(source, changed)['result'], 'HOLD')

    def test_typed_semantics_exact(self):
        for typed in [cell('number', 1), cell('number', 1.0), cell('blank'), cell('absent'),
                      cell('formula', '=1+1'), cell('date_serial', 45000, format='yyyy-mm-dd', timezone='Etc/UTC'),
                      cell('datetime', '2026-10-05T00:00:00+00:00', timezone='Etc/UTC'), cell('string', ' é\n ')]:
            left = fixture(); left['rows'][0][6] = typed
            self.assertEqual(compare_snapshots(left, copy.deepcopy(left))['result'], 'PASS')
            right = copy.deepcopy(left); right['rows'][0][6] = cell('string', str(typed['value']) + 'changed')
            self.assertEqual(compare_snapshots(left, right)['result'], 'HOLD')
        left = fixture(); right = fixture()
        left['rows'][0][6] = cell('number', 1); right['rows'][0][6] = cell('number', 1.0)
        self.assertEqual(compare_snapshots(left, right)['result'], 'HOLD')

    def test_shape_order_duplicates_invalid(self):
        for mutation in [lambda x: x['rows'].reverse(), lambda x: x['rows'].append(x['rows'][0]),
                         lambda x: x['rows'][0].pop(), lambda x: x.update(extra=True),
                         lambda x: x['columns'].reverse(), lambda x: x['rows'][0].__setitem__(6, cell('number', 1))]:
            left = fixture(); right = copy.deepcopy(left); mutation(right)
            self.assertEqual(compare_snapshots(left, right)['result'], 'HOLD')

    def test_native_grid_notes_validation_long_unicode(self):
        left = fixture()
        left['rows'][0][10] = cell('string', ('e\u0301😀 ' * 13000) + 'tail')
        left['cell_provenance'][1][6].update(note='Invented UTC provenance; opaque serial',
            native_format={'numberFormat': {'type': 'DATE_TIME', 'pattern': 'M/d/yyyy H:mm:ss'}},
            data_validation={'strict': True, 'condition': {'type': 'ONE_OF_LIST', 'values': [s.value for s in Status]}})
        self.assertEqual(compare_snapshots(left, copy.deepcopy(left))['result'], 'PASS')
        for key, value in [('note', 'changed'), ('native_format', {}), ('data_validation', None)]:
            right = copy.deepcopy(left); right['cell_provenance'][1][6][key] = value
            self.assertEqual(compare_snapshots(left, right)['result'], 'HOLD')
        right = copy.deepcopy(left); right['rows'][0][10]['value'] = right['rows'][0][10]['value'][:-1]
        self.assertEqual(compare_snapshots(left, right)['result'], 'HOLD')
        right = copy.deepcopy(left); right['grid_metadata']['date_policy'] = 'assume Lagos wall time'
        self.assertEqual(compare_snapshots(left, right)['result'], 'HOLD')

    def test_full_201_by_17_absence(self):
        left = fixture()
        left['rows'] += [[cell('absent') for _ in range(17)] for _ in range(193)]
        left['cell_provenance'] += [[dict(note=None, native_format=None, data_validation=None,
                                         provenance='synthetic://template') for _ in range(17)] for _ in range(193)]
        left['source']['range'] = 'A1:Q201'; left['grid_metadata']['row_count'] = 201
        self.assertEqual(compare_snapshots(left, copy.deepcopy(left))['result'], 'PASS')
        right = copy.deepcopy(left); right['rows'][-1][16] = cell('string', '')
        self.assertEqual(compare_snapshots(left, right)['result'], 'HOLD')
        right = copy.deepcopy(left); right['cell_provenance'][-1][6]['native_format'] = {'numberFormat': {'type': 'DATE_TIME'}}
        self.assertEqual(compare_snapshots(left, right)['result'], 'HOLD')

    def test_malformed_capture_extent(self):
        for section, key, value in [('source', 'range', 'not a range'),
                                    ('source', 'range', 'A1:Q9'),
                                    ('capture', 'captured_at', 'not a timestamp'),
                                    ('capture', 'captured_at', '2026-10-05T00:00:00')]:
            value_snapshot = fixture(); value_snapshot[section][key] = value
            self.assertEqual(compare_snapshots(value_snapshot, value_snapshot)['result'], 'HOLD')

    def test_read_only_no_body_disclosure(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fixture.json'; path.write_text(json.dumps(fixture()))
            before = path.read_bytes()
            self.assertEqual(read_compare(path, path)['result'], 'PASS')
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(read_compare(path, Path(d) / 'missing')['result'], 'HOLD')
            path.write_text('{"version":1,"version":1}')
            self.assertEqual(read_compare(path, path)['result'], 'HOLD')
            self.assertNotIn('AJ-900', json.dumps(read_compare(path, path)))
