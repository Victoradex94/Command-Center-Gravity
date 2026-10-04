"""Independent synthetic AJ-0014 regressions; no external transports."""
from dataclasses import replace
import unittest
from tests import test_codex_worker as fixtures
from dispatcher.model import Lineage, ProtocolError

class IndependentProbes(unittest.TestCase):
    def setUp(self):
        self.h = fixtures.WorkerTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)

    def test_terminal_cannot_regress_to_attributed_running(self):
        h = self.h
        a = h.dispatch()
        h.provider.observe(h.request, state='failed')
        self.assertEqual(h.adapter.inspect(a.worker_run).state, 'failed')
        h.provider.observe(h.request, state='running', substantive=True, start_evidence='synthetic restarted?')
        run = h.adapter.inspect(a.worker_run)
        self.assertFalse(run.authenticated and run.substantive,
                         'terminal task/turn was re-exposed as substantive running')

    def test_provider_failure_requires_changed_condition_recovery(self):
        h = self.h
        a = h.dispatch()
        h.provider.observe(h.request, state='failed')
        h.adapter.inspect(a.worker_run)
        h.adapter.fence(h.request, 'synthetic terminal reviewed')
        h.restart()
        next_request = replace(h.request, lineage=Lineage('AJ-0014', 1, 1, 2))
        with self.assertRaises(ProtocolError, msg='execution failure bypassed recovery budget'):
            h.adapter.dispatch(next_request)

    def test_false_string_envelope_authentication_rejected(self):
        h = self.h
        receipt = h.full_return()
        receipt['return']['authenticated'] = 'false'
        self.assertIsNone(h.adapter.normalize_return(h.request, receipt))

    def test_terminal_conflict_cannot_authorize_replacement(self):
        h = self.h
        a = h.dispatch()
        h.provider.observe(h.request, state='completed')
        h.adapter.inspect(a.worker_run)
        h.provider.observe(h.request, state='running', substantive=True, start_evidence='synthetic conflict')
        h.adapter.inspect(a.worker_run)
        h.adapter.fence(h.request, 'synthetic isolate conflicting observation')
        next_request = replace(h.request, lineage=Lineage('AJ-0014', 1, 1, 2))
        with self.assertRaises(ProtocolError, msg='sticky terminal allowed replacement of observed running work'):
            h.adapter.dispatch(next_request)

    def test_permission_failure_on_lookup_persists_stop(self):
        h = self.h
        a = h.dispatch()
        def deny(*args):
            raise PermissionError('synthetic access revoked')
        h.provider.inspect = deny
        self.assertEqual(h.adapter.inspect(a.worker_run).state, 'unknown')
        h.restart()
        incident = h.journal.load()['circuits'].get('AJ-0014', {})
        self.assertTrue(incident.get('permission_stop'), 'lookup permission denial not persisted as stop')

    def test_permission_lookup_fences_return_after_restart(self):
        h = self.h
        receipt = h.full_return()
        a = h.op()['admission']['worker_run']
        def deny(*args):
            raise PermissionError('synthetic access revoked')
        h.provider.inspect = deny
        for _ in range(3):
            h.adapter.inspect(a)
        h.restart()
        self.assertEqual(h.journal.load()['circuits']['AJ-0014']['failures'], 1)
        self.assertIsNone(h.adapter.normalize_return(h.request, receipt))

    def test_execution_failure_observations_idempotent_and_recurrence_opens_circuit(self):
        h = self.h
        a = h.dispatch()
        h.provider.observe(h.request, state='failed')
        for _ in range(3):
            h.adapter.inspect(a.worker_run)
        h.restart()
        self.assertEqual(h.journal.load()['circuits']['AJ-0014']['failures'], 1)
        h.adapter.fence(h.request, 'synthetic terminal reviewed')
        next_request = replace(h.request, lineage=Lineage('AJ-0014', 1, 1, 2))
        h.adapter.authorize_recovery(next_request, 'synthetic corrected tested condition')
        a = h.adapter.dispatch(next_request)
        h.provider.observe(next_request, state='failed')
        h.adapter.inspect(a.worker_run)
        h.restart()
        incident = h.journal.load()['circuits']['AJ-0014']
        self.assertEqual(incident['failures'], 2)
        self.assertTrue(incident['circuit'])

    def test_conflicting_lookup_retains_raw_evidence(self):
        h = self.h
        a = h.dispatch()
        receipt = h.provider.observe(h.request, nonce='synthetic-wrong-nonce')
        self.assertFalse(h.adapter.inspect(a.worker_run).authenticated)
        h.restart()
        rejected = h.op()['observations'][-1]
        self.assertEqual(rejected.get('rejected_receipt'), receipt)

    def test_failed_return_enters_budget_once(self):
        h = self.h
        receipt = h.full_return()
        receipt['state'] = 'failed'
        receipt['return'].update(execution_state='Failed', claimed_class='Blocked',
                                failed_gate='synthetic execution', blockers='synthetic failure')
        self.assertIsNotNone(h.adapter.normalize_return(h.request, receipt))
        self.assertIsNotNone(h.adapter.normalize_return(h.request, receipt))
        h.restart()
        self.assertEqual(h.journal.load()['circuits']['AJ-0014']['failures'], 1)
        h.adapter.fence(h.request, 'synthetic failed return reviewed')
        next_request = replace(h.request, lineage=Lineage('AJ-0014', 1, 1, 2))
        with self.assertRaises(ProtocolError):
            h.adapter.dispatch(next_request)

    def test_terminal_return_blocks_later_running_observation(self):
        h = self.h
        receipt = h.full_return()
        self.assertIsNotNone(h.adapter.normalize_return(h.request, receipt))
        h.provider.observe(h.request, state='running', substantive=True, start_evidence='synthetic conflict')
        result = h.adapter.inspect(h.op()['admission']['worker_run'])
        self.assertFalse(result.authenticated)
        self.assertTrue(h.op()['execution_conflict'])

if __name__ == '__main__':
    unittest.main()
