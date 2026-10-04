"""AJ-0014 synthetic-only acceptance and crash/restart probes."""
from dataclasses import asdict, replace
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from dispatcher.adapters import DispatchRequest
from dispatcher.codex_worker import (Authority, CodexWorkerAdapter, DeterministicMockProvider,
                                     asdict_json, digest)
from dispatcher.model import Gate, Lineage, ProtocolError, ReturnClass, Status
from dispatcher.writer_journal import WriterJournal
from tests.support import Harness, NOW, REQUIRED, brief, gates, routes


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.request = DispatchRequest(Lineage('AJ-0014', 1, 1, 1),
                                       'VA-CODEX-ROUTE-0014-01', 'Codex', 'fake-codex', brief())
        self.active = True
        self.gates = gates()
        self.route = routes()[0]
        self.restart()

    def authority(self, request):
        return Authority(digest(asdict(request)), request.lineage, request.nonce, self.active,
                         'synthetic root authority', self.gates, self.route, REQUIRED)

    def restart(self, checkpoint=lambda _: None):
        self.journal = WriterJournal(self.tmp.name + '/adapter.db', 'synthetic AJ-0014 worker')
        self.provider = DeterministicMockProvider(
            WriterJournal(self.tmp.name + '/provider.db', 'synthetic AJ-0014 provider'), lambda: NOW)
        self.adapter = CodexWorkerAdapter(self.journal, self.provider, self.authority, lambda: NOW, checkpoint)

    def calls(self):
        return len(self.provider.journal.load()['audit'])

    def op(self):
        return self.journal.load()['operations'][self.request.idempotency_key]

    def dispatch(self):
        return self.adapter.dispatch(self.request)

    def full_return(self):
        admission = self.dispatch()
        h = Harness('AJ-0014')
        h.working()
        envelope = h.envelope(nonce=self.request.nonce, worker_run=admission.worker_run)
        receipt = self.provider.observe(self.request, state='completed', complete=True, truncated=False)
        receipt['return'] = asdict_json(envelope)
        return receipt

    def test_duplicate_restart_one_submission(self):
        first = self.dispatch()
        self.restart()
        self.assertEqual(first, self.dispatch())
        self.assertEqual(self.calls(), 1)
        self.assertEqual(self.op()['request'], asdict_json(self.request))
        self.assertTrue(self.op()['authority']['reference'])

    def test_changed_payload_rejected(self):
        self.dispatch()
        for changes in ({'nonce': 'changed-nonce'}, {'limits': 'changed'}, {'route': 'other'},
                        {'brief': replace(self.request.brief, inputs='changed')}):
            with self.subTest(changes=changes), self.assertRaises(ProtocolError):
                self.adapter.dispatch(replace(self.request, **changes))
        self.assertEqual(self.calls(), 1)

    def test_concurrent_wrappers_one_submit(self):
        def run(_):
            adapter = CodexWorkerAdapter(WriterJournal(self.journal.path, 'synthetic AJ-0014 worker'),
                                         self.provider, self.authority, lambda: NOW)
            return adapter.dispatch(self.request)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(run, range(8)))
        self.assertEqual(len(set(results)), 1)
        self.assertEqual(self.calls(), 1)

    def test_timeout_after_acceptance_reconciles(self):
        self.provider.mode = 'timeout_after'
        with self.assertRaises(ProtocolError):
            self.dispatch()
        self.restart()
        with self.assertRaises(ProtocolError):
            self.dispatch()
        run = self.adapter.inspect_reservation(self.request).run
        self.assertTrue(run.authenticated)
        self.assertFalse(run.substantive)
        self.assertEqual(self.dispatch().worker_run, run.worker_run)
        self.assertEqual(self.calls(), 1)

    def test_timeout_missing_handle_never_replaced(self):
        self.provider.mode = 'timeout_before'
        with self.assertRaises(ProtocolError):
            self.dispatch()
        self.restart()
        self.assertEqual(self.adapter.inspect_reservation(self.request).run.state, 'unknown')
        with self.assertRaises(ProtocolError):
            self.dispatch()
        next_request = replace(self.request, lineage=Lineage('AJ-0014', 1, 1, 2))
        self.adapter.authorize_recovery(next_request, 'synthetic provider restored')
        with self.assertRaises(ProtocolError):
            self.adapter.dispatch(next_request)
        self.assertEqual(self.calls(), 1)

    def crash(self, window):
        pid = os.fork()
        if pid == 0:
            self.restart(lambda point: os._exit(42) if point == window else None)
            self.dispatch()
            os._exit(0)
        _, status = os.waitpid(pid, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 42)
        self.restart()

    def test_crash_before_submit_freezes(self):
        self.crash('before_submit')
        self.assertEqual(self.calls(), 0)
        self.assertEqual(self.adapter.inspect_reservation(self.request).run.state, 'unknown')
        with self.assertRaises(ProtocolError):
            self.dispatch()

    def test_crash_after_acceptance_recovers(self):
        self.crash('after_acceptance')
        self.assertTrue(self.adapter.inspect_reservation(self.request).run.authenticated)
        self.dispatch()
        self.assertEqual(self.calls(), 1)

    def test_crash_after_receipt_is_idempotent(self):
        self.crash('after_receipt')
        self.dispatch()
        self.assertEqual(self.calls(), 1)

    def test_substantive_start_only_with_attributed_evidence(self):
        admission = self.dispatch()
        self.assertFalse(self.adapter.inspect(admission.worker_run).substantive)
        self.provider.observe(self.request, state='running', substantive=True)
        self.assertFalse(self.adapter.inspect(admission.worker_run).substantive)
        self.provider.observe(self.request, start_evidence='synthetic code inspection')
        self.assertTrue(self.adapter.inspect(admission.worker_run).substantive)
        self.provider.observe(self.request, nonce='wrong')
        self.assertFalse(self.adapter.inspect(admission.worker_run).authenticated)

    def test_exact_handles_no_rebinding(self):
        admission = self.dispatch()
        self.provider.observe(self.request, turn='different')
        self.assertEqual(self.adapter.inspect(admission.worker_run).state, 'unknown')
        self.assertEqual(self.adapter.inspect_reservation(self.request).run.state, 'unknown')
        self.assertEqual(self.calls(), 1)

    def test_full_return_duplicate_and_conflict(self):
        receipt = self.full_return()
        first = self.adapter.normalize_return(self.request, receipt)
        self.assertIsNotNone(first)
        self.restart()
        self.assertEqual(first, self.adapter.normalize_return(self.request, receipt))
        receipt['return']['output'] = 'conflict'
        self.assertIsNone(self.adapter.normalize_return(self.request, receipt))
        self.assertEqual(len(self.op()['returns']), 1)
        self.assertFalse(next(iter(self.op()['returns'].values()))['independently_accepted'])

    def test_partial_blocked_returns_do_not_accept(self):
        receipt = self.full_return()
        for claim in ('Partial', 'Blocked'):
            receipt['return'].update(claimed_class=claim, failed_gate='synthetic dependency',
                                     blockers='synthetic missing input', remaining='synthetic incomplete')
            result = self.adapter.normalize_return(self.request, receipt)
            if claim == 'Partial':
                self.assertEqual(result.claimed_class, ReturnClass.PARTIAL)
            else:
                self.assertIsNone(result)  # cannot overwrite previous output
        self.assertFalse(next(iter(self.op()['returns'].values()))['independently_accepted'])

    def test_incomplete_conflicting_truncated_attribution(self):
        original = self.full_return()
        variants = [dict(original, truncated=True), dict(original, complete=False)]
        for field in ('nonce', 'worker', 'route', 'task', 'turn', 'lineage'):
            variants.append(dict(original, **{field: 'wrong'}))
        for field in original['return']:
            variant = asdict_json(original)
            del variant['return'][field]
            variants.append(variant)
        for receipt in variants:
            with self.subTest(receipt=receipt):
                self.assertIsNone(self.adapter.normalize_return(self.request, receipt))
        self.assertFalse(self.op()['returns'])
        self.assertEqual(len(self.op()['rejected_returns']), len(variants))

    def test_cancelled_reassigned_superseded_returns_fenced(self):
        receipt = self.full_return()
        for reason in ('cancelled', 'reassigned', 'superseded'):
            self.adapter.fence(self.request, reason)
            self.restart()
            self.assertIsNone(self.adapter.normalize_return(self.request, receipt))

    def test_revoked_authority_cannot_adopt(self):
        receipt = self.full_return()
        self.active = False
        self.assertIsNone(self.adapter.normalize_return(self.request, receipt))
        with self.assertRaises(ProtocolError):
            self.dispatch()

    def test_stop_ack_is_not_termination(self):
        admission = self.dispatch()
        self.assertIn('unconfirmed', self.adapter.request_stop(admission.worker_run, 'synthetic root stop'))
        self.assertEqual(self.op()['stop'], 'acknowledged')
        self.assertFalse(self.op()['terminal'])
        self.restart()
        self.provider.observe(self.request, state='stopped')
        self.adapter.inspect(admission.worker_run)
        self.assertEqual(self.op()['stop'], 'confirmed_stopped')

    def test_unsupported_stop_fences_return(self):
        receipt = self.full_return()
        self.provider.stop_mode = 'unsupported'
        self.adapter.request_stop(self.op()['admission']['worker_run'], 'synthetic stop')
        self.assertEqual(self.op()['stop'], 'unsupported')
        self.assertIsNone(self.adapter.normalize_return(self.request, receipt))

    def test_gates_explicit_worker_readiness_dependency(self):
        for field in ('authority', 'identity', 'capability', 'access', 'dependencies', 'readiness', 'return_contract'):
            self.gates = replace(gates(), **{field: Gate(None, 'synthetic unknown')})
            with self.subTest(field=field), self.assertRaises(ProtocolError):
                self.dispatch()
        self.gates = replace(gates(), dependencies=Gate(True, 'Done'))
        with self.assertRaises(ProtocolError):
            self.dispatch()
        self.gates = gates()
        with self.assertRaises(ProtocolError):
            self.adapter.dispatch(replace(self.request, brief=replace(brief(), explicit_worker='Gemini')))
        self.route = replace(self.route, route='different')
        with self.assertRaises(ProtocolError):
            self.dispatch()
        self.assertEqual(self.calls(), 0)

    def test_permission_stop_survives_restart(self):
        self.provider.mode = 'permission'
        with self.assertRaises(ProtocolError):
            self.dispatch()
        self.restart()
        with self.assertRaises(ProtocolError):
            self.adapter.authorize_recovery(self.request, 'synthetic fallback wrapper')
        incident = self.journal.load()['circuits']['AJ-0014']
        self.assertTrue(incident['permission_stop'])

    def test_shared_budget_and_recurrence(self):
        self.provider.mode = 'timeout_after'
        with self.assertRaises(ProtocolError):
            self.dispatch()
        fingerprint = self.journal.load()['circuits']['AJ-0014']['fingerprint']
        self.restart()
        run = self.adapter.inspect_reservation(self.request).run
        for _ in range(3):
            self.adapter.inspect(run.worker_run)
        self.assertEqual(self.journal.load()['circuits']['AJ-0014']['failures'], 1)
        self.provider.observe(self.request, state='completed')
        self.adapter.inspect(run.worker_run)
        self.adapter.fence(self.request, 'synthetic terminal reconciled')
        next_request = replace(self.request, lineage=Lineage('AJ-0014', 1, 1, 2))
        self.adapter.authorize_recovery(next_request, 'synthetic verified changed condition')
        self.restart()
        self.provider.mode = 'timeout_after'
        with self.assertRaises(ProtocolError):
            self.adapter.dispatch(next_request)
        incident = self.journal.load()['circuits']['AJ-0014']
        self.assertEqual(incident['fingerprint'], fingerprint)
        self.assertTrue(incident['circuit'])
        with self.assertRaises(ProtocolError):
            self.adapter.authorize_recovery(next_request, 'synthetic other wrapper')

    def test_production_transport_rejected(self):
        self.provider.synthetic_only = False
        with self.assertRaises(ProtocolError):
            CodexWorkerAdapter(self.journal, self.provider, self.authority, lambda: NOW)

    def test_engine_admission_start_return_independent_review(self):
        h = Harness('AJ-0014')
        self.request = DispatchRequest(h.lineage, h.record.nonce, 'Codex', 'fake-codex', h.record.brief)
        h.executor = self.adapter
        h.ready()
        self.assertEqual(h.dispatch().row.status, Status.READY)
        with self.assertRaises(ProtocolError):
            h.engine.start(h.lineage, self.adapter.inspect(h.record.current_attempt.worker_run))
        self.provider.observe(self.request, state='running', substantive=True, start_evidence='synthetic work')
        h.engine.start(h.lineage, self.adapter.inspect(h.record.current_attempt.worker_run))
        receipt = self.provider.observe(self.request, state='completed', complete=True, truncated=False)
        receipt['return'] = asdict_json(h.envelope())
        result = self.adapter.normalize_return(self.request, receipt)
        self.assertEqual(h.engine.receive(result).row.status, Status.REVIEW)
        self.assertEqual(h.engine.complete(h.lineage, h.verification()).row.status, Status.DONE)

    def test_blocked_return_is_complete_but_not_accepted(self):
        receipt = self.full_return()
        receipt['return'].update(claimed_class='Blocked', failed_gate='synthetic dependency',
                                 blockers='synthetic missing input', remaining='synthetic pending')
        result = self.adapter.normalize_return(self.request, receipt)
        self.assertEqual(result.claimed_class, ReturnClass.BLOCKED)
        self.assertFalse(next(iter(self.op()['returns'].values()))['independently_accepted'])

    def test_crash_stop_intent_and_lost_ack_fence_without_termination(self):
        admission = self.dispatch()
        for window in ('before_stop', 'after_stop'):
            # Independent fixture identity/database per subcase.
            with self.subTest(window=window):
                if window == 'after_stop':
                    self.tmp.cleanup()
                    self.tmp = tempfile.TemporaryDirectory()
                    self.addCleanup(self.tmp.cleanup)
                    self.restart()
                    admission = self.dispatch()
                pid = os.fork()
                if pid == 0:
                    self.restart(lambda point: os._exit(43) if point == window else None)
                    self.adapter.request_stop(admission.worker_run, 'synthetic stop')
                    os._exit(0)
                _, status = os.waitpid(pid, 0)
                self.assertEqual(os.waitstatus_to_exitcode(status), 43)
                self.restart()
                self.assertEqual(self.op()['stop'], 'requested')
                self.assertTrue(self.op()['fenced'])
                self.assertFalse(self.op()['terminal'])
                self.assertIn('requested', self.adapter.request_stop(admission.worker_run, 'synthetic repeat'))

    def test_stale_authority_and_route_are_rejected(self):
        self.gates = replace(gates(), checked_at='2026-10-04T05:00:00+00:00')
        with self.assertRaises(ProtocolError):
            self.dispatch()
        self.gates = gates()
        self.route = replace(routes()[0], checked_at='2026-10-04T05:00:00+00:00')
        with self.assertRaises(ProtocolError):
            self.dispatch()
        self.assertEqual(self.calls(), 0)
