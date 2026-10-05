"""Independent adversarial AJ-0016 probes; invented data and local provider only."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dispatcher.git_ledger import GitLedger, digest
from dispatcher.git_transport import MemoryGitTransport
from dispatcher.isolation import (IsolationCoordinator, LocalAuthorityProvider, bootstrap,
                                  cell, import_snapshot, import_operation, string_row, verify_manifest, ROUTES)
from dispatcher.model import AgentJob, ProtocolError, Status


class IsolationReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.transport = MemoryGitTransport()
        self.ledger = GitLedger(Path(self.tmp.name) / 'ledger.json', self.transport)
        self.token = self.ledger.acquire('independent-synthetic-reviewer')
        rows = {f'AJ-{9000+i}': [cell('string', v) for v in AgentJob(f'AJ-{9000+i}', status=status).to_cells()]
                for i, status in enumerate(Status)}
        self.manifest = bootstrap(rows, provisional_ids=list(rows),
            privacy_policy='synthetic-only; no bodies, secrets or personal data; no normalization',
            provenance='synthetic://independent-review/snapshot')
        self.accepted = digest(self.manifest)
        self.provider = LocalAuthorityProvider(Path(self.tmp.name) / 'authority.json')
        self.coordinator = IsolationCoordinator(self.provider, self.ledger, self.manifest, self.accepted)

    def active(self):
        self.coordinator.initialize(); self.coordinator.transition('LEGACY', 'HELD')
        self.coordinator.transition('HELD', 'PREPARING')
        self.head = import_snapshot(self.ledger, self.token, self.manifest, self.accepted)
        self.coordinator.activate(self.head)
        return next(j for j, c in self.manifest['rows'].items() if c[4]['value'] == 'Ready')

    def test_dispatch_remote_changes_between_gate_and_selection(self):
        job = self.active(); original = self.ledger._remote
        calls = 0
        def changing_remote():
            nonlocal calls
            calls += 1
            result = original()
            if calls >= 2:
                return ('synthetic-advanced-head', result[1], result[2])
            return result
        with patch.object(self.ledger, '_remote', side_effect=changing_remote):
            with self.assertRaises(ProtocolError):
                self.coordinator.dispatch(job, surface='new', epoch=1, head=self.head)

    def test_dispatch_rollback_between_gate_and_selection(self):
        job = self.active(); original = self.ledger._remote
        calls = 0
        def changing_remote():
            nonlocal calls
            calls += 1
            if calls == 2:
                self.coordinator.rollback_hold()
            return original()
        with patch.object(self.ledger, '_remote', side_effect=changing_remote):
            with self.assertRaises(ProtocolError):
                self.coordinator.dispatch(job, surface='new', epoch=1, head=self.head)

    def test_remote_changes_after_selection_final_check_holds(self):
        job = self.active(); original = self.ledger._remote
        calls = 0
        def changing_remote():
            nonlocal calls
            calls += 1
            result = original()
            if calls == 2:
                self.transport.remote = 'synthetic-retired-head'
            return result
        with patch.object(self.ledger, '_remote', side_effect=changing_remote):
            with self.assertRaises(ProtocolError):
                self.coordinator.dispatch(job, surface='new', epoch=1, head=self.head)

    def test_corrupt_authority_envelope_and_missing_state_hold(self):
        job = self.active()
        self.provider.path.write_text('{"state": {}, "digest": "synthetic-bad"}')
        with self.assertRaises(ProtocolError):
            self.coordinator.dispatch(job, surface='new', epoch=1, head=self.head)
        self.provider.path.unlink()
        with self.assertRaises(ProtocolError):
            self.coordinator.dispatch(job, surface='new', epoch=1, head=self.head)

    def test_self_consistent_wrong_bootstrap_lineage_rejected(self):
        self.coordinator.initialize(); self.coordinator.transition('LEGACY', 'HELD')
        self.coordinator.transition('HELD', 'PREPARING')
        for i, job in enumerate(sorted(self.manifest['rows'])):
            head, _, state = self.ledger._remote()
            op = import_operation(self.manifest, self.accepted, job, head, state['last_event_hash'])
            if i == 0:
                op = replace(op, nonce='SYNTHETIC-WRONG-NONCE', run_epoch=2)
            self.ledger.append(self.token, op)
        head = self.transport.head(); count = self.transport.calls
        with self.assertRaises(ProtocolError): self.coordinator.activate(head)
        with self.assertRaises(ProtocolError):
            import_snapshot(self.ledger, self.token, self.manifest, self.accepted)
        self.assertEqual(self.transport.calls, count)
        self.assertEqual(self.provider.read()['phase'], 'PREPARING')

    def test_crash_after_publish_before_response_import_reconciles(self):
        job = sorted(self.manifest['rows'])[0]
        op = import_operation(self.manifest, self.accepted, job, None, None)
        self.ledger.append(self.token, op, prepare_only=True)
        sha = self.ledger.resume(self.token, publish=False)['sha']
        self.transport.publish(None, sha)
        restarted = GitLedger(self.ledger.path, self.transport)
        head = import_snapshot(restarted, self.token, self.manifest, self.accepted)
        self.assertEqual(head, self.transport.head())
        self.assertEqual((self.transport.calls, self.transport.commits), (7, 7))
        with restarted.locked() as control:
            self.assertIsNone(control['pending'])

    def test_manifest_mutations_rehashed_do_not_gain_acceptance(self):
        for field in ('repo', 'ref', 'base', 'source', 'lineage', 'identity', 'history'):
            with self.subTest(field=field):
                m = deepcopy(self.manifest); m[field] = 'synthetic-wrong-identity'
                with self.assertRaises(ProtocolError): verify_manifest(m, digest(m))

    def test_rehash_per_cell_and_operation_corruption_rejected(self):
        for field in ('reconciliation', 'operations'):
            m = deepcopy(self.manifest)
            m[field][next(iter(m['rows']))] = 'synthetic-corruption'
            with self.assertRaises(ProtocolError): verify_manifest(m, digest(m))

    def test_retired_epoch_cannot_prepare_or_reactivate(self):
        self.active(); self.coordinator.rollback_hold()
        with self.assertRaises(ProtocolError): self.coordinator.transition('HELD', 'PREPARING')
        with self.assertRaises(ProtocolError): self.coordinator.activate(self.head)
        for route in ROUTES:
            with self.assertRaises(ProtocolError): self.coordinator.gate(route, 'legacy', 0, None)
        self.assertEqual(self.provider.read()['exception']['legacy_unconditional_write'], 'UNKNOWN')

    def test_typed_semantics_rejected_by_string_export(self):
        for typed in (cell('blank'), cell('absent'), cell('number', 17),
                      cell('date_serial', 46299.5, format='yyyy-mm-dd hh:mm', timezone='Etc/UTC'),
                      cell('formula', '=1+1', format='0.00'),
                      cell('datetime', '2026-10-05T12:00:00+00:00', timezone='Etc/UTC')):
            cells = deepcopy(next(iter(self.manifest['rows'].values()))); cells[6] = typed
            with self.assertRaises(ProtocolError): string_row(cells)
        self.assertNotEqual(cell('blank'), cell('absent'))

    def test_lost_import_response_restart_same_identity_zero_replay(self):
        self.transport.mode = 'lost'
        first = import_snapshot(self.ledger, self.token, self.manifest, self.accepted)
        count = (self.transport.calls, self.transport.commits)
        restarted = GitLedger(Path(self.tmp.name) / 'ledger.json', self.transport)
        self.assertEqual(import_snapshot(restarted, self.token, self.manifest, self.accepted), first)
        self.assertEqual((self.transport.calls, self.transport.commits), count)
        self.assertEqual(count, (7, 7))
