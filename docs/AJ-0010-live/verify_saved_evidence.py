"""Read-only checks of retained actual MCP evidence; makes no connector calls."""
import json
import sqlite3
from pathlib import Path

from dispatcher.google_sheets import GoogleSheetsAdapter, private_owner_only


def main():
    p = Path(__file__).resolve().parent
    read = lambda name: json.loads((p / name).read_text())
    fixture = json.loads((p.parent / 'AJ-0010-fixture-plan.json').read_text())
    before, after = read('execute-before.json'), read('execute-after.json')
    restarted_before, restarted_after = read('reconcile-before.json'), read('reconcile-after.json')
    config = read('config.json')
    with sqlite3.connect(f'file:{p}/receipts.sqlite?mode=ro', uri=True) as db:
        receipts = {key: json.loads(body) for key, body in db.execute('select attempt,body from receipts')}
    assert set(receipts) == {'AJ-0010/sandbox/create-v1/0', 'AJ-0010/sandbox/update-v1/0'}
    create = receipts['AJ-0010/sandbox/create-v1/0']
    update = receipts['AJ-0010/sandbox/update-v1/0']
    values = lambda capture: [c.get('userEnteredValue', {}).get('stringValue', '') for c in capture['cells'][1][:17]]
    assert values(before) == [''] * 17
    assert before == create['baseline']
    assert values(update['baseline']) == fixture['create']['cells']
    assert values(after) == fixture['update']['cells']
    assert after == restarted_before == restarted_after
    assert GoogleSheetsAdapter.unchanged_structure(before, update['baseline'], 2)
    assert GoogleSheetsAdapter.unchanged_structure(update['baseline'], after, 2)
    for capture in (before, update['baseline'], after, restarted_before, restarted_after):
        private_owner_only(capture['file'], config['owner_email'], file_id=config['spreadsheet_id'])
        private_owner_only(capture['root'], config['owner_email'], file_id=config['root_folder_id'])
    for kind, receipt in (('create', create), ('update', update)):
        assert receipt['submission']['cells'] == fixture[kind]['cells']
        assert receipt['response'] == read(kind + '-supervisor-original-response.json')
        response = receipt['response']
        assert receipt['exception_type'] is None and response['isError'] is False
        assert response['structuredContent'] == {
            'spreadsheetId': config['spreadsheet_id'], 'replies': [{}], 'updatedSpreadsheet': None}
        request = receipt['request']['requests']
        assert len(request) == 1
        cell_update = request[0]['updateCells']
        assert cell_update['fields'] == 'userEnteredValue'
        assert cell_update['range'] == {'sheetId': config['sheet_id'], 'startRowIndex': 1,
            'endRowIndex': 2, 'startColumnIndex': 0, 'endColumnIndex': 17}
        assert cell_update['rows'] == [{'values': [
            {'userEnteredValue': {'stringValue': value}} for value in fixture[kind]['cells']]}]
    counts = {}
    sessions = []
    for mode in ('execute', 'reconcile'):
        requests = [json.loads(path.read_text()) for path in sorted(p.glob(mode + '-tool-*-request.json'))]
        sessions.append({request['bridge_session'] for request in requests})
        mutations = [request for request in requests if request['tool'].endswith('batch_update_spreadsheet')]
        counts[mode] = {'requests': len(requests), 'mutations': len(mutations)}
        assert len(mutations) == (2 if mode == 'execute' else 0)
        assert read(mode + '-process.json')['exit_code'] == 0
        result = read(mode + '-result.json')
        assert result['submissions'] == 2 and result['recovery_used'] == 0
        state = read(mode + '-writer-state.json')
        assert len(state['operations']) == 2
        for operation in state['operations'].values():
            assert operation['outcome'] == 'SUCCESS' and len(operation['submissions']) == 1
            assert operation['recovery_used'] == 0 and not operation['circuit_open']
    assert len(sessions[0]) == len(sessions[1]) == 1 and not sessions[0] & sessions[1]
    assert read('execute-process.json')['tool_session_id'] != read('reconcile-process.json')['tool_session_id']
    print(json.dumps({'result': 'PASS', 'scope': 'retained actual live evidence; no new API calls',
        'counts': counts, 'logical_create': 1, 'logical_update': 1, 'replay_writes': 0,
        'workbook_creates': 1, 'setup_batches': 1,
        'exact17cells_create_and_update': True, 'entire_exposed_structure_preserved': True,
        'private_owner_only_before_after': True, 'separate_process_restart': True}, indent=2))


if __name__ == '__main__':
    main()
