"""Independent offline AJ-0012 adverse probes; no live route installed."""
import sys
import unittest
from dataclasses import replace
from tests.offline_suite import reject_external
from tests.test_slack_controlled import ControlledTests
from dispatcher.slack import Readback, SlackJournal, SlackBoundary
from dispatcher.slack_controlled import Observation, WORKSPACE, SENDER
from dispatcher.model import ProtocolError
from tests.support import Harness

class Probes(ControlledTests):
    def test_review_corrupt_binding_freezes(self):
        key = self.keys[0]
        with self.j.transaction() as state:
            state['controlled_slack']['binding'][key]['text'] = 'tampered'
        self.assertEqual(self.b.deliver(key, self.p), 'unknown')
        self.assertEqual(self.calls, [])

    def test_review_all_wrong_readback_dimensions_freeze(self):
        key = self.keys[0]
        item = self.j.snapshot()['messages'][key]
        exact = Readback('found', key, item['destination'], '', item['text'], 'mock:1')
        for field, value in [('key', 'foreign'), ('destination', 'foreign'),
                             ('thread', 'parent'), ('text', 'changed'), ('reference', '')]:
            bad = replace(exact, **{field: value})
            self.p.read = lambda *args: Observation(bad, WORKSPACE, SENDER, {'fixture':field})
            self.assertEqual(self.b.deliver(key, self.p), 'unknown')
        self.assertEqual(self.calls, [])

    def test_review_timeout_then_recovery_no_repeat(self):
        key = self.keys[0]
        def uncertain(*args):
            self.calls.append(key)
            raise TimeoutError('fixture response lost before any readable receipt')
        self.p.dispatch = uncertain
        self.assertEqual(self.b.deliver(key, self.p), 'unknown')
        self.b.recover('AJ-0012', 'mock changed condition', lambda *args: True)
        self.assertEqual(self.b.deliver(key, self.p), 'unknown')
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(self.j.snapshot()['incidents']['AJ-0012']['recovery_used'])
        self.assertEqual(self.j.snapshot()['controlled_slack']['operations'][key]['state'], 'reserved')

    def test_review_read_failure_before_attempt_never_sends(self):
        def broken(*args):
            raise TimeoutError('fixture read unavailable')
        self.p.read = broken
        self.assertEqual(self.b.deliver(self.keys[0], self.p), 'unknown')
        self.assertEqual(self.calls, [])

    def test_review_missing_receipt_after_restart_no_send(self):
        key = self.keys[0]
        def die(*args):
            self.calls.append(key)
            raise KeyboardInterrupt('fixture death after durable reservation')
        self.p.dispatch = die
        with self.assertRaises(KeyboardInterrupt):
            self.b.deliver(key, self.p)
        self.j.close()
        self.j = SlackJournal(self.path)
        self.b = SlackBoundary(Harness().engine, self.j, lambda *args: False)
        self.p = self.provider()
        self.assertEqual(self.b.deliver(key, self.p), 'unknown')
        self.assertEqual(len(self.calls), 1)

    def test_review_original_receipts_retained(self):
        key = self.keys[0]
        self.assertEqual(self.b.deliver(key, self.p), 'verified')
        c = self.j.snapshot()['controlled_slack']
        self.assertEqual(c['operations'][key]['raw'], {'fixture':'original-acceptance'})
        self.assertEqual(len(c['reads']), 2)
        self.assertEqual(c['reads'][1]['normalized']['text'], c['binding'][key]['text'])
        self.assertEqual(c['reads'][1]['sender'], SENDER)

if __name__ == '__main__':
    sys.addaudithook(reject_external)
    suite = unittest.TestSuite(Probes(name) for name in unittest.defaultTestLoader.getTestCaseNames(Probes)
                              if name.startswith('test_review_'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
