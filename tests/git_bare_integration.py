"""Explicit local bare fixtures only; offline suite blocks executable launches.
Run: python3 -B -m tests.git_bare_integration
"""
from dataclasses import replace
from pathlib import Path
import subprocess
import tempfile
from dispatcher.git_ledger import GitLedger, Operation, reduce_files
from dispatcher.model import AgentJob, ProtocolError
from tests.git_bare_fixture import LocalBareGitTransport


def main():
    with tempfile.TemporaryDirectory(prefix='aj0015-local-bare-') as directory:
        root = Path(directory); bare = root / 'remote.git'
        subprocess.run(['git', 'init', '--bare', str(bare)], check=True, capture_output=True)
        transport = LocalBareGitTransport(bare)
        ledger = GitLedger(root / 'control.json', transport); token = ledger.acquire('fixture')
        op = Operation('AJ-0015', 1, 'fixture-op', 0, None, None,
                       AgentJob('AJ-0015').to_cells(), 'synthetic:authority', 'synthetic:context',
                       '2026-10-04T00:00:00+00:00', 'fixture', 'local-bare', 1, 1, 1,
                       'VA-GIT-LEDGER-0015-01')
        ledger.append(token, op, prepare_only=True)
        sha = ledger.resume(token, publish=False)['sha']
        assert len(sha) == 40 and transport.head() is None
        assert reduce_files(transport.read(sha))['rows']['AJ-0015'] == op.intended_cells
        class LostResponse(LocalBareGitTransport):
            def publish(self, expected, intended):
                assert super().publish(expected, intended) == 'SUCCESS'
                raise RuntimeError('synthetic response lost')
        ledger = GitLedger(root / 'control.json', LostResponse(bare))
        assert ledger.resume(token)['sha'] == sha
        assert ledger.append(token, op)['sha'] == sha
        assert transport.head() == sha
        state = reduce_files(transport.read(sha))
        cells = op.intended_cells.copy(); cells[4] = 'Ready'
        second = replace(op, operation_id='second', record_revision=2, expected_revision=1,
                         expected_head=sha, expected_event_hash=state['last_event_hash'], intended_cells=cells)
        ledger = GitLedger(root / 'control.json', transport)
        sha2 = ledger.append(token, second)['sha']
        assert transport.parent(sha2) == sha
        assert transport.publish(sha, sha) == 'CONFLICT'
        assert transport.head() == sha2
        try:
            ledger.append(token, replace(second, operation_id='stale'))
        except ProtocolError:
            pass
        else:
            raise AssertionError('stale head accepted')
        ledger.retire(token); successor = ledger.acquire('successor')
        try: ledger.append(token, op)
        except ProtocolError: pass
        else: raise AssertionError('retired writer accepted')
        assert ledger.append(successor, second)['sha'] == sha2
        print('PASS: actual Git SHA prepared before ref update; exact blobs; lost-response reconciliation; append parent chain; CAS conflict; retired fence; no network')


if __name__ == '__main__': main()
