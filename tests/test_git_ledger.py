"""Network-blocked ledger contract fixtures, no live services or credentials."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from dispatcher.git_ledger import GitLedger, Operation, reduce_files, canonical
from dispatcher.git_transport import MemoryGitTransport
from dispatcher.model import AgentJob, ProtocolError, Status


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'control.json'
        self.t = MemoryGitTransport(); self.l = GitLedger(self.path, self.t)
        self.token = self.l.acquire('root-fixture')
        self.op = Operation('AJ-0015', 1, 'stable-op-0015', 0, None, None,
                            AgentJob('AJ-0015').to_cells(), 'synthetic:authority', 'synthetic:context',
                            '2026-10-04T00:00:00+00:00', 'fixture', 'local', 1, 1, 1,
                            'VA-GIT-LEDGER-0015-01')

    def state(self): return json.loads(self.path.read_text())
    def restart(self): self.l = GitLedger(self.path, self.t)
    def append(self): return self.l.append(self.token, self.op)

    def test_append_reduce_exact17(self):
        result = self.append(); self.assertEqual(result['outcome'], 'RECONCILED')
        state = reduce_files(self.t.read(result['sha']))
        self.assertEqual(state['rows']['AJ-0015'], self.op.intended_cells)
        self.assertEqual(len(state['rows']['AJ-0015']), 17)

    def test_duplicate_zero_second_commit(self):
        self.append(); self.restart(); self.append()
        self.assertEqual((self.t.calls, self.t.commits), (1, 1))

    def test_changed_payload_reject(self):
        self.append()
        with self.assertRaises(ProtocolError): self.l.append(self.token, replace(self.op, context_ref='changed'))
        self.assertEqual(self.t.commits, 1)

    def test_stale_head_no_mutation(self):
        self.append(); count = self.t.commits
        with self.assertRaises(ProtocolError): self.l.append(self.token, replace(self.op, operation_id='other'))
        self.assertEqual(self.t.commits, count)

    def test_stale_revision_no_mutation(self):
        self.append(); s = reduce_files(self.t.read(self.t.head()))
        op = replace(self.op, operation_id='other', expected_head=self.t.head(), expected_event_hash=s['last_event_hash'])
        with self.assertRaises(ProtocolError): self.l.append(self.token, op)
        self.assertEqual(self.t.commits, 1)

    def test_crash_precommit_resume(self):
        self.l.append(self.token, self.op, prepare_only=True); self.restart()
        self.assertIsNone(self.state()['pending']['intended_sha'])
        self.l.resume(self.token); self.append(); self.assertEqual(self.t.calls, 1)

    def test_precommit_abandon_no_duplicate(self):
        self.l.append(self.token, self.op, prepare_only=True); self.restart()
        self.l.abandon(self.token); self.append(); self.assertEqual(self.t.commits, 1)

    def test_local_not_pushed(self):
        self.l.append(self.token, self.op, prepare_only=True)
        sha = self.l.resume(self.token, publish=False)['sha']; self.restart()
        self.assertEqual(self.l.reconcile(self.token)['outcome'], 'LOCAL_COMMIT')
        self.assertIsNone(self.t.head()); self.assertEqual(self.t.calls, 0)
        self.assertEqual(self.l.resume(self.token)['sha'], sha)

    def test_lost_response_exact_remote_zero_replay(self):
        self.t.mode = 'lost'; self.append(); self.restart(); self.append()
        self.assertEqual(self.t.calls, 1)

    def test_unknown_unchanged_not_noop(self):
        self.t.mode = 'unknown'; self.assertEqual(self.append()['outcome'], 'UNCERTAIN')
        self.restart()
        with self.assertRaises(ProtocolError): self.l.recover(self.token, 'synthetic:new', True)
        with self.assertRaises(ProtocolError): self.l.resume(self.token)
        self.assertEqual(self.t.calls, 1)

    def test_one_shared_changed_condition_recovery(self):
        self.t.mode = 'reject'; self.assertEqual(self.append()['outcome'], 'FINAL_NOOP')
        with self.assertRaises(ProtocolError): self.l.recover(self.token, 'synthetic:new', False)
        self.l.recover(self.token, 'synthetic:new', True); self.restart()
        with self.assertRaises(ProtocolError): self.l.recover(self.token, 'synthetic:newer', True)
        self.assertEqual(self.t.calls, 2)

    def test_changed_condition_success(self):
        self.t.mode = 'reject'; self.append(); self.t.mode = 'success'
        self.assertEqual(self.l.recover(self.token, 'synthetic:resolved', True)['outcome'], 'RECONCILED')
        self.assertEqual((self.t.calls, self.t.commits), (2, 1))

    def test_remote_advanced_conflict(self):
        self.t.mode = 'unknown'; self.append()
        other = MemoryGitTransport()
        other_l = GitLedger(Path(self.tmp.name) / 'other.json', other)
        other_token = other_l.acquire('other')
        other_l.append(other_token, replace(self.op, operation_id='other', context_ref='other'))
        self.t.objects.update(other.objects); self.t.remote = other.remote
        self.assertEqual(self.l.reconcile(self.token)['outcome'], 'CONFLICT')
        with self.assertRaises(ProtocolError): self.l.resume(self.token)
        self.assertEqual(self.t.calls, 1)

    def test_writer_retirement_handoff(self):
        with self.assertRaises(ProtocolError): self.l.acquire('other')
        self.l.retire(self.token); token = self.l.acquire('other')
        with self.assertRaises(ProtocolError): self.append()
        with self.assertRaises(ProtocolError): self.l.acquire('root-fixture')
        self.l.append(token, self.op)

    def test_permission_cancellation_blocks(self):
        self.t.mode = 'permission'; self.append(); self.restart()
        with self.assertRaises(ProtocolError): self.l.recover(self.token, 'synthetic:new', True)
        with self.assertRaises(ProtocolError): self.l.resume(self.token)
        self.assertTrue(self.state()['permission_cancelled'])

    def test_generic_cancel_freezes(self):
        def cancelled(*args): raise RuntimeError('user cancelled MCP tool call')
        self.t.publish = cancelled; self.append(); self.restart()
        self.assertEqual(self.state()['circuit'], 'UNKNOWN')
        with self.assertRaises(ProtocolError): self.l.recover(self.token, 'new-condition', True)

    def test_fingerprint_persist_abandoned(self):
        self.l.append(self.token, self.op, prepare_only=True); self.l.abandon(self.token); self.restart()
        with self.assertRaises(ProtocolError): self.l.append(self.token, replace(self.op, worker='changed'))

    def test_replay_determinism(self):
        self.append(); files = self.t.read(self.t.head()); state = reduce_files(files)
        cells = self.op.intended_cells.copy(); cells[4] = 'Ready'
        next_op = replace(self.op, operation_id='second', record_revision=2, expected_revision=1,
                          expected_head=self.t.head(), expected_event_hash=state['last_event_hash'], intended_cells=cells)
        self.l.append(self.token, next_op)
        files = self.t.read(self.t.head()); self.assertEqual(reduce_files(files), reduce_files(dict(reversed(list(files.items())))))
        self.assertTrue(all(self.t.read(self.t.objects[self.t.head()][0])[p] == files[p] for p in state['events']))

    def test_corrupt_missing_broken_chain(self):
        self.append(); files = self.t.read(self.t.head()); event = reduce_files(files)['events'][0]
        for mutation in ('missing', 'corrupt', 'chain'):
            bad = files.copy()
            if mutation == 'missing': del bad[event]
            elif mutation == 'corrupt': bad[event] = b'{}'
            else:
                data = json.loads(bad[event]); data['payload']['expected_event_hash'] = 'broken'; bad[event] = canonical(data)
            with self.subTest(mutation=mutation), self.assertRaises(ProtocolError): reduce_files(bad)

    def test_projection_all_seven_statuses(self):
        self.assertEqual(len(Status), 7)
        for status in Status:
            with self.subTest(status=status):
                cells = self.op.intended_cells.copy(); cells[4] = status.value
                AgentJob.from_cells(cells)
        self.append(); result = self.l.projection({})
        self.assertEqual(result['projection_state'], 'SYNC_PENDING')
        self.assertEqual(len(result['snapshot']['AJ-0015']), 17)
        self.assertEqual(self.l.projection(result['snapshot'])['projection_state'], 'VERIFIED')
        self.assertEqual(self.t.calls, 1)
