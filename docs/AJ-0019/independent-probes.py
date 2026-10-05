"""Independent synthetic-only AJ-0019 review probes; no transport or import."""
import copy
import json
import jsonschema
from tests.test_cutover_readiness import fixture
from dispatcher.cutover_readiness import compare_snapshots
from dispatcher.isolation import cell

schema = json.load(open('docs/AJ-0019/bootstrap.schema.json'))
jsonschema.Draft202012Validator.check_schema(schema)
validator = jsonschema.Draft202012Validator(schema)
assert not list(validator.iter_errors(fixture()))
checks = 0
for value in ('not a range', 'A1:Q999'):
    x = fixture()
    x['source']['range'] = value
    assert compare_snapshots(x, x)['result'] == 'HOLD'
    checks += 1
x = fixture()
x['capture']['captured_at'] = 'not a timestamp'
assert compare_snapshots(x, x)['result'] == 'HOLD'
checks += 1
for col in range(17):
    x = fixture()
    x['rows'][0][col]['timezone'] = 'unexpected'
    assert compare_snapshots(fixture(), x)['result'] == 'HOLD'
    checks += 1
for kind, value in [('number', True), ('blank', ''), ('formula', 'bad')]:
    x = fixture()
    x['rows'][0][6].update(kind=kind, value=value)
    assert list(validator.iter_errors(x))
    checks += 1
x = fixture()
x['rows'][0][6]['value'] = 'e\u0301'
y = copy.deepcopy(x)
y['rows'][0][6]['value'] = 'é'
assert compare_snapshots(x, y)['result'] == 'HOLD'
checks += 1
# Continuation v2: every native matrix and grid metadata field is significant.
full = fixture()
full['rows'] += [[cell('absent') for _ in range(17)] for _ in range(193)]
full['cell_provenance'] += [[dict(note=None, native_format=None, data_validation=None,
    provenance='synthetic://independent-template') for _ in range(17)] for _ in range(193)]
full['source']['range'] = 'A1:Q201'
full['grid_metadata']['row_count'] = 201
assert compare_snapshots(full, copy.deepcopy(full))['result'] == 'PASS'
assert not list(validator.iter_errors(full))
checks += 2
for key, value in [('locale', 'en_GB'), ('timezone', 'Africa/Lagos'), ('frozen_rows', 2),
                   ('frozen_columns', 2), ('date_policy', 'synthetic changed policy'),
                   ('provenance', 'synthetic://changed')]:
    x = copy.deepcopy(full)
    x['grid_metadata'][key] = value
    assert compare_snapshots(full, x)['result'] == 'HOLD'
    checks += 1
for index in [0, 1, 200]:
    for key, value in [('note', ''), ('native_format', {'numberFormat': {'pattern': 'x'}}),
                       ('data_validation', {'strict': True}), ('provenance', 'synthetic://changed')]:
        x = copy.deepcopy(full)
        x['cell_provenance'][index][16][key] = value
        assert compare_snapshots(full, x)['result'] == 'HOLD'
        checks += 1
x = copy.deepcopy(full)
x['rows'][0][10] = cell('string', ('e\u0301😀' * 17000) + 'END')
assert compare_snapshots(x, copy.deepcopy(x))['result'] == 'PASS'
y = copy.deepcopy(x)
y['rows'][0][10]['value'] = y['rows'][0][10]['value'][:-1]
assert compare_snapshots(x, y)['result'] == 'HOLD'
checks += 2
for mutate in [lambda x: x['cell_provenance'].pop(),
               lambda x: x['header_cells'][0].update(value='wrong header'),
               lambda x: x['rows'][-1][-1].update(kind='blank')]:
    x = copy.deepcopy(full)
    mutate(x)
    assert compare_snapshots(full, x)['result'] == 'HOLD'
    checks += 1
print(f'independent probes {checks} PASS; schema Draft202012 valid')
