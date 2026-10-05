"""Read-only exact JSON comparison; no import, conversion, transport or activation.

Inputs are already represented typed snapshots. AJ18 owns native conversion.
Reports contain no cell bodies, identifiers, hashes of private cells or exceptions.
"""
import json
import re
from datetime import datetime
from pathlib import Path
from .isolation import validate_cell
from .model import AGENT_JOB_COLUMNS, Status, require


def exact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def validate_snapshot(snapshot):
    require(type(snapshot) is dict and set(snapshot) ==
            {'version', 'source', 'capture', 'columns', 'statuses', 'rows',
             'header_cells', 'grid_metadata', 'cell_provenance'}, 'closed snapshot')
    require(type(snapshot['version']) is int and snapshot['version'] == 2, 'version')
    require(type(snapshot['source']) is dict and set(snapshot['source']) ==
            {'workbook', 'title', 'gid', 'range'}, 'source identity')
    s = snapshot['source']
    require(all(type(s[k]) is str and s[k] for k in ('workbook', 'title', 'range'))
            and type(s['gid']) is int and s['gid'] >= 0, 'source types')
    require(type(snapshot['capture']) is dict and set(snapshot['capture']) ==
            {'reference', 'captured_at', 'complete', 'timezone'}, 'capture metadata')
    c = snapshot['capture']
    require(c['complete'] is True and all(type(c[k]) is str and c[k]
            for k in ('reference', 'captured_at', 'timezone')), 'complete capture required')
    require(snapshot['columns'] == list(AGENT_JOB_COLUMNS) and
            snapshot['statuses'] == [s.value for s in Status], 'accepted contract')
    require(type(snapshot['rows']) is list, 'ordered rows required')
    g = snapshot['grid_metadata']
    require(type(g) is dict and set(g) == {'locale', 'timezone', 'frozen_rows',
            'frozen_columns', 'row_count', 'column_count', 'date_policy', 'provenance'}, 'grid metadata')
    require(all(type(g[k]) is str and g[k] for k in ('locale', 'timezone', 'date_policy', 'provenance')),
            'explicit date interpretation policy and provenance')
    require(all(type(g[k]) is int and g[k] >= 0 for k in
            ('frozen_rows', 'frozen_columns', 'row_count', 'column_count')) and
            g['column_count'] == 17 and g['row_count'] == len(snapshot['rows']) + 1 and
            g['frozen_rows'] <= g['row_count'] and g['frozen_columns'] <= 17 and
            g['timezone'] == c['timezone'], 'grid dimensions/timezone')
    require(type(snapshot['header_cells']) is list and len(snapshot['header_cells']) == 17, 'header cells')
    for label, header in zip(AGENT_JOB_COLUMNS, snapshot['header_cells']):
        validate_cell(header)
        require(header['kind'] == 'string' and header['value'] == label, 'exact header')
    provenance = snapshot['cell_provenance']
    require(type(provenance) is list and len(provenance) == g['row_count'], 'full grid provenance')
    for metadata_row in provenance:
        require(type(metadata_row) is list and len(metadata_row) == 17, '17 metadata cells')
        for metadata in metadata_row:
            require(type(metadata) is dict and set(metadata) ==
                    {'note', 'native_format', 'data_validation', 'provenance'}, 'closed cell provenance')
            require((metadata['note'] is None or type(metadata['note']) is str) and
                    (metadata['native_format'] is None or type(metadata['native_format']) is dict) and
                    (metadata['data_validation'] is None or type(metadata['data_validation']) is dict) and
                    type(metadata['provenance']) is str and bool(metadata['provenance']), 'metadata types')
    ids = set()
    for row in snapshot['rows']:
        require(type(row) is list and len(row) == 17, 'exact 17 cells')
        for cell in row:
            validate_cell(cell)
        if all(cell['kind'] == 'absent' for cell in row):
            continue  # Captured trailing template rows remain present, with metadata.
        require(row[0]['kind'] == 'string' and bool(row[0]['value']) and
                row[0]['value'] not in ids, 'unique job identity')
        ids.add(row[0]['value'])
        require(row[4]['kind'] == 'string' and row[4]['value'] in snapshot['statuses'], 'status')
    extent = re.fullmatch(r'A1:Q([1-9][0-9]*)', s['range'])
    require(extent is not None and int(extent.group(1)) == len(snapshot['rows']) + 1,
            'complete header and row extent required')
    require(datetime.fromisoformat(c['captured_at']).tzinfo is not None, 'aware capture timestamp')
    exact(snapshot)


def compare_snapshots(expected, actual):
    """Fail closed. Compare complete capture, order, type and metadata, no normalization."""
    try:
        validate_snapshot(expected)
        validate_snapshot(actual)
        equal = exact(expected) == exact(actual)
    except (ValueError, TypeError, KeyError, OverflowError):
        return {'result': 'HOLD', 'reason': 'invalid snapshot', 'activation': False}
    return {'result': 'PASS' if equal else 'HOLD',
            'reason': 'exact equality' if equal else 'snapshot differs', 'activation': False}


def read_compare(expected_path, actual_path):
    """Read local protected exports only; never persists inputs or invokes a tool."""
    def load(path):
        def pairs(items):
            value = {}
            for key, item in items:
                if key in value:
                    raise ValueError('duplicate key')
                value[key] = item
            return value
        return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs)
    try:
        return compare_snapshots(load(expected_path), load(actual_path))
    except (OSError, ValueError, TypeError):
        return {'result': 'HOLD', 'reason': 'unreadable snapshot', 'activation': False}
