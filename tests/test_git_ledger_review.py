"""Independent AJ-0015 adversarial probes; offline, no connectors."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest

from dispatcher.git_ledger import GitLedger, Operation, canonical, digest, reduce_files
from dispatcher.git_transport import MemoryGitTransport
from dispatcher.model import AgentJob, ProtocolError, Status


def operation(**changes):
    values = dict(job_id='AJ-0015', record_revision=1, operation_id='review-op-1',
                  expected_revision=0, expected_head=None, expected_event_hash=None,
                  intended_cells=AgentJob('AJ-0015', status=Status.READY).to_cells(),
                  authority_ref='Slack1791143425.384499', context_ref='independent synthetic review',
                  timestamp='2026-10-04T00:00:00+00:00', worker='review', route='local/mock',
                  spec_revision=1, run_epoch=1, attempt=1, nonce='VA-GIT-LEDGER-0015-01')
    values.update(changes)
    return Operation(**values)


class IndependentGitLedgerReview(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'control.json'
        self.transport = MemoryGitTransport()
        self.ledger = GitLedger(self.path, self.transport)
        self.token = self.ledger.acquire('review-writer')

    def test_restart_unknown_cancellation_freezes_and_preserves_fingerprint(self):
        self.transport.mode = 'unknown'
        self.assertEqual(self.ledger.append(self.token, operation())['outcome'], 'UNCERTAIN')
        restarted = GitLedger(self.path, self.transport)
        with self.assertRaises(ProtocolError):
            restarted.resume(self.token)
        with self.assertRaises(ProtocolError):
            restarted.recover(self.token, 'new-ref', verified=True)
        self.assertEqual(self.transport.calls, 1)
        state = json.loads(self.path.read_bytes())
        self.assertEqual(state['fingerprints']['review-op-1'], digest(operation().payload()))
        self.assertTrue(state['circuit'])

    def test_final_noop_shared_recovery_budget_persists_across_handoff(self):
        self.transport.mode = 'reject'
        self.assertEqual(self.ledger.append(self.token, operation())['outcome'], 'FINAL_NOOP')
        with self.assertRaises(ProtocolError):
            self.ledger.recover(self.token, 'condition-ref', verified=False)
        self.assertEqual(self.ledger.recover(self.token, 'condition-ref', verified=True)['outcome'], 'FINAL_NOOP')
        self.ledger.retire(self.token)
        restarted = GitLedger(self.path, self.transport)
        successor = restarted.acquire('successor')
        with self.assertRaises(ProtocolError):
            restarted.recover(successor, 'different-ref', verified=True)
        with self.assertRaises(ProtocolError):
            restarted.resume(self.token)
        self.assertEqual(self.transport.calls, 2)
        self.assertEqual(self.transport.commits, 1)

    def test_permission_cancellation_blocks_new_owner_after_restart(self):
        self.transport.mode = 'permission'
        self.assertEqual(self.ledger.append(self.token, operation())['outcome'], 'UNCERTAIN')
        self.ledger.retire(self.token)
        restarted = GitLedger(self.path, self.transport)
        successor = restarted.acquire('successor')
        with self.assertRaises(ProtocolError):
            restarted.recover(successor, 'condition-ref', verified=True)
        with self.assertRaises(ProtocolError):
            restarted.append(successor, operation(operation_id='another-op'))
        self.assertEqual(self.transport.calls, 1)

    def test_duplicate_after_crash_at_remote_publish_clears_exact_pending(self):
        self.ledger.append(self.token, operation(), prepare_only=True)
        sha = self.ledger.resume(self.token, publish=False)['sha']
        with self.ledger.locked() as state:
            state['pending']['attempted'] = True
            state['circuit'] = 'IN_FLIGHT'
        self.transport.publish(None, sha)  # Process dies before receipt persistence.
        restarted = GitLedger(self.path, self.transport)
        result = restarted.append(self.token, operation())
        self.assertEqual(result, {'outcome': 'RECONCILED', 'sha': sha})
        state = json.loads(self.path.read_bytes())
        self.assertIsNone(state['pending'])
        self.assertIsNone(state['circuit'])
        self.assertEqual(self.transport.calls, 1)
        self.assertEqual(self.transport.commits, 1)

    def test_changed_payload_after_abandon_remains_rejected(self):
        self.ledger.append(self.token, operation(), prepare_only=True)
        self.ledger.abandon(self.token)
        with self.assertRaises(ProtocolError):
            self.ledger.append(self.token, operation(outcome='CHANGED'))
        self.assertEqual(self.transport.commits, 0)

    def test_remote_exact_sha_with_wrong_blobs_is_not_finality(self):
        result = self.ledger.append(self.token, operation(), prepare_only=True)
        self.assertEqual(result['outcome'], 'PREPARED')
        local = self.ledger.resume(self.token, publish=False)['sha']
        self.transport.remote = local
        parent, blobs = self.transport.objects[local]
        blobs['snapshot.json'] = b'{}'
        self.transport.objects[local] = (parent, blobs)
        with self.assertRaises(ProtocolError):
            self.ledger.reconcile(self.token)
        self.assertIsNotNone(json.loads(self.path.read_bytes())['pending'])
        self.assertEqual(self.transport.calls, 0)

    def test_missing_event_and_rehashed_broken_chain_rejected(self):
        self.ledger.append(self.token, operation())
        files = self.transport.read(self.transport.head())
        manifest = json.loads(files['manifest.json'])
        path = manifest['events'][0]
        missing = dict(files); del missing[path]
        with self.assertRaises(ProtocolError):
            reduce_files(missing)
        event = json.loads(files[path])
        event['payload']['expected_event_hash'] = 'forged-prior-event'
        event['hash'] = digest(event['payload'])
        files[path] = canonical(event)
        manifest['files'][path] = hashlib.sha256(files[path]).hexdigest()
        files['manifest.json'] = canonical(manifest)
        with self.assertRaises(ProtocolError):
            reduce_files(files)

    def test_rehashed_valid_snapshot_with_false_git_parent_rejected(self):
        self.ledger.append(self.token, operation())
        files = self.transport.read(self.transport.head())
        manifest = json.loads(files['manifest.json'])
        original_path = manifest['events'][0]
        event = json.loads(files.pop(original_path))
        event['payload']['expected_head'] = 'invented-git-parent'
        event['hash'] = digest(event['payload'])
        new_path = f"events/AJ-0015/00000001-{event['hash']}.json"
        files[new_path] = canonical(event)
        files['index.json'] = canonical({'revisions': {'AJ-0015': 1},
                                        'operations': {'review-op-1': event['hash']},
                                        'last_event_hash': event['hash']})
        files['manifest.json'] = canonical({'version': 1, 'events': [new_path],
                    'files': {p: hashlib.sha256(b).hexdigest() for p,b in files.items() if p != 'manifest.json'}})
        # Files-only hash/reducer checks pass: actual Git ancestry must be consulted.
        reduce_files(files)
        self.transport.remote = self.transport.construct(None, files)
        with self.assertRaises(ProtocolError):
            self.ledger.projection({})

    def test_hidden_noop_commit_rejected_as_nonappend_ancestry(self):
        self.ledger.append(self.token, operation())
        prior = self.transport.head()
        self.transport.remote = self.transport.construct(prior, self.transport.read(prior))
        with self.assertRaises(ProtocolError):
            self.ledger.projection({})
        self.assertEqual(self.transport.calls, 1)

    def test_projection_diff_accounts_for_canonical_only_rows(self):
        self.ledger.append(self.token, operation())
        extra = AgentJob('AJ-0014').to_cells()
        result = self.ledger.projection({'AJ-0015': operation().intended_cells, 'AJ-0014': extra})
        self.assertEqual(result['projection_state'], 'SYNC_PENDING')
        self.assertEqual(result['diff']['AJ-0014'], {'before': extra, 'after': None})

    def test_writer_retirement_cannot_complete_during_publication(self):
        entered = threading.Event(); release = threading.Event(); retired = threading.Event(); retirement_success = threading.Event()
        original = self.transport.publish
        def paused(expected, sha):
            entered.set()
            if not release.wait(3):
                raise AssertionError('test release timeout')
            return original(expected, sha)
        self.transport.publish = paused
        errors = []
        def append():
            try: self.ledger.append(self.token, operation())
            except Exception as exc: errors.append(exc)
        def retire():
            try:
                self.ledger.retire(self.token)
                retirement_success.set()
            except ProtocolError: pass  # Explicit in-flight retirement rejection also fences.
            finally: retired.set()
        writer = threading.Thread(target=append)
        writer.start()
        self.assertTrue(entered.wait(2))
        retire_thread = threading.Thread(target=retire)
        retire_thread.start()
        completed_early = retired.wait(.15)
        release.set(); writer.join(3); retire_thread.join(3)
        self.assertFalse(completed_early and retirement_success.is_set(),
                         'retirement completed while old writer could still publish')
        self.assertFalse(errors, repr(errors))
        self.assertFalse(writer.is_alive() or retire_thread.is_alive())


if __name__ == '__main__':
    unittest.main()
