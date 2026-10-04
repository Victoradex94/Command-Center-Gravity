"""Independent root-handoff probes. Local fixtures only."""
import sys,unittest
from tests.offline_suite import reject_external
from tests.test_slack_handoff import HandoffTests
from dispatcher.model import ProtocolError

class BridgeProbes(HandoffTests):
    def test_review_returned_request_cannot_mutate_journal(self):
        req=self.h.prepare_next(); original=self.h.status()
        req['content']='changed'; req['destination']='foreign'
        self.assertEqual(self.h.status(),original)

    def test_review_permission_withdrawn_between_inspect_and_reserve(self):
        inspect=self.h.inspect
        def revoke(*args):
            value=inspect(*args);self.allowed=False;return value
        self.h.inspect=revoke
        with self.assertRaises(ValueError):self.h.prepare_next()
        self.assertEqual(self.h.status()['requests'],{})
        self.assertEqual(self.j.snapshot()['controlled_slack']['operations'],{})

    def test_review_adapter_only_crash_window_never_reissues(self):
        key=self.keys[0]
        with self.j.transaction() as s:s['messages'][key].update(state='sending',attempts=1)
        with self.assertRaises(ProtocolError):self.h.prepare_next()
        self.assertEqual(self.h.status()['requests'],{})

    def test_review_contradictory_acceptance_cannot_certify_good_readback(self):
        req=self.h.prepare_next();e=self.evidence(req)
        e['acceptance']['sender']='Victor'
        self.assertEqual(self.h.reconcile(req['request_sha256'],**e),'unknown')
        with self.assertRaises(ProtocolError):self.h.prepare_next()

    def test_review_receipt_reference_conflict_freezes(self):
        req=self.h.prepare_next();e=self.evidence(req)
        self.assertEqual(self.h.reconcile(req['request_sha256'],raw_response=e['raw_response'],acceptance=e['acceptance']),'accepted')
        e['acceptance']['reference']='different';e['observation']['reference']='different'
        self.assertEqual(self.h.reconcile(req['request_sha256'],**e),'unknown')
        with self.assertRaises(ProtocolError):self.h.prepare_next()

    def test_review_corrupt_request_freezes_reconciliation(self):
        req=self.h.prepare_next()
        with self.j.transaction() as s:s['root_handoff']['requests'][req['operation_id']]['request']['content']='changed'
        with self.assertRaises(ProtocolError):self.h.reconcile(req['request_sha256'],**self.evidence(req))

    def test_review_exact_evidence_idempotent_and_retained(self):
        req=self.h.prepare_next();e=self.evidence(req)
        self.assertEqual(self.h.reconcile(req['request_sha256'],**e),'verified')
        before=self.j.snapshot()
        self.assertEqual(self.h.reconcile(req['request_sha256'],**e),'verified')
        self.assertEqual(self.j.snapshot(),before)
        self.assertEqual(self.h.status()['evidence'][0]['raw_response'],e['raw_response'])
        self.assertEqual(self.h.status()['evidence'][0]['raw_readback'],e['raw_readback'])

if __name__=='__main__':
    sys.addaudithook(reject_external)
    suite=unittest.TestSuite(BridgeProbes(n) for n in unittest.defaultTestLoader.getTestCaseNames(BridgeProbes) if n.startswith('test_review_'))
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not r.wasSuccessful())
