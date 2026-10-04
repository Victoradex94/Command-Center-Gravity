"""Independent review probes; execute with PYTHONPATH=. python docs/AJ-0011-review/probes.py."""
import sys
import unittest
from tests.offline_suite import reject_external
sys.addaudithook(reject_external)
from dispatcher.adapters import RejectedDelivery
from dispatcher.model import ProtocolError
from dispatcher.slack import SlackBoundary, SlackJournal, Command, Grant, SlackConfig, Readback
from tests.support import Harness, source

class Crash(BaseException):
    pass

class ReviewProbes(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.journal = SlackJournal(':memory:')
        self.addCleanup(self.journal.close)
        self.boundary = SlackBoundary(self.h.engine, self.journal, lambda g,c: True)

    def test_escalation_has_actual_decision(self):
        self.h.engine.escalate(self.h.lineage, 'scope', facts='Scope changed',
            decision='CHOOSE_SCOPE_A_OR_B', recommendation='PREFER_SCOPE_A',
            consequence='DELAY_IF_UNDECIDED', deadline='DECISION_BY_FRIDAY')
        self.boundary.sync(self.h.job_id)
        attention = [m for m in self.journal.snapshot()['messages'].values()
                     if m['destination'] == SlackConfig().attention]
        self.assertEqual(len(attention), 1)
        for value in ('CHOOSE_SCOPE_A_OR_B','PREFER_SCOPE_A','DELAY_IF_UNDECIDED','DECISION_BY_FRIDAY'):
            self.assertIn(value, attention[0]['text'])

    def _outbox(self):
        self.h.engine.escalate(self.h.lineage, 'review', facts='facts', decision='decision',
            recommendation='recommendation', consequence='consequence', deadline='deadline')
        self.boundary.sync(self.h.job_id)
        key = next(iter(self.journal.snapshot()['messages']))
        return key, self.journal.snapshot()['messages'][key]

    def test_wrong_destination_evidence_does_not_verify(self):
        key, message = self._outbox()
        class Provider:
            def inspect(self, *args):
                return Readback('found', key, 'WRONG_DESTINATION', '', message['text'], 'ts')
            def send(self, *args):
                raise AssertionError('unexpected send')
        self.assertEqual(self.boundary.deliver(key, Provider()), 'unknown')

    def test_unknown_lookup_never_sends(self):
        key, _ = self._outbox()
        class Provider:
            def inspect(self, *args):
                raise TimeoutError('unknown')
            def send(self, *args):
                raise AssertionError('unexpected send')
        self.assertEqual(self.boundary.deliver(key, Provider()), 'unknown')
        self.assertEqual(self.journal.snapshot()['messages'][key]['attempts'], 0)

    def test_crash_after_send_reconciles_original_without_replay(self):
        key, message = self._outbox()
        class Provider:
            sent = False
            calls = 0
            def inspect(self, *args):
                return (Readback('found', key, message['destination'], '', message['text'], 'original-ts')
                        if self.sent else Readback('absent'))
            def send(self, *args):
                self.calls += 1
                self.sent = True
                raise Crash()
        provider = Provider()
        with self.assertRaises(Crash):
            self.boundary.deliver(key, provider)
        self.assertEqual(self.journal.snapshot()['messages'][key]['state'], 'sending')
        restarted = SlackBoundary(self.h.engine, self.journal, lambda g,c: True)
        self.assertEqual(restarted.deliver(key, provider), 'verified')
        self.assertEqual(provider.calls, 1)
        self.assertEqual(self.journal.snapshot()['messages'][key]['human_read'], 'unknown')

    def _crash_reconcile(self, action, already_blocked=False):
        if action == 'pause':
            self.h.ready()
            if already_blocked:
                self.h.engine.block(self.h.lineage, gate='review', reason='blocked', evidence='probe',
                    owner='root', next_action='review')
        command = Command(source('review-' + action, channel=SlackConfig().command), action,
            self.h.job_id, 'VA-REVIEW-0011-01', lineage=self.h.lineage,
            evidence='Stop requested; no external effects')
        original = getattr(self.h.engine, action)
        def applied_then_crash(*args):
            original(*args)
            raise Crash()
        setattr(self.h.engine, action, applied_then_crash)
        with self.assertRaises(Crash):
            self.boundary.command(command, Grant(command.fingerprint, 'trusted-local-grant'))
        self.assertEqual(self.boundary.reconcile_command(command), self.h.job_id)

    def test_cancel_crash_reconciliation(self):
        self._crash_reconcile('cancel')

    def test_pause_crash_reconciliation(self):
        self._crash_reconcile('pause')

    def test_already_blocked_pause_crash_reconciliation(self):
        self._crash_reconcile('pause', already_blocked=True)

    def test_crashed_correction_with_confirmed_absence_trips_circuit(self):
        key, _ = self._outbox()
        class Provider:
            calls = 0
            def inspect(self, *args):
                return Readback('absent')
            def send(self, *args):
                self.calls += 1
                if self.calls == 1:
                    raise RejectedDelivery('rejected')
                raise Crash()
        provider = Provider()
        self.boundary.deliver(key, provider)
        self.boundary.recover(self.h.job_id, 'changed condition', lambda g,e: True)
        with self.assertRaises(Crash):
            self.boundary.deliver(key, provider)
        self.boundary.deliver(key, provider)
        self.assertEqual(provider.calls, 2)
        self.assertTrue(self.journal.snapshot()['incidents'][self.h.job_id]['circuit'])
        with self.assertRaises(ProtocolError):
            self.boundary.recover(self.h.job_id, 'fallback', lambda g,e: True)

if __name__ == '__main__':
    unittest.main(verbosity=2)
