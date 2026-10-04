"""Mock root responses only; no external tool invocation."""
import os
import tempfile
import unittest
from dispatcher.model import ProtocolError
from dispatcher.slack import SlackBoundary, SlackJournal
from dispatcher.slack_controlled import bind_synthetic, WORKSPACE, SENDER
from dispatcher.slack_handoff import RootHandoff, ROOT_ROUTE
from tests.support import Harness


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = self.temp.name + '/journal.sqlite'
        self.j = SlackJournal(self.path)
        self.addCleanup(lambda: self.j.close())
        self.keys = bind_synthetic(self.j)
        self.allowed = True
        self.h = self.open_handoff()
        self.h.authorize(approval='mock owner approval', identity_evidence='mock root bot proof',
                         zero_send_evidence='mock exclusive zero sends', workspace=WORKSPACE,
                         sender=SENDER, route=ROOT_ROUTE)

    def open_handoff(self):
        return RootHandoff(SlackBoundary(Harness().engine, self.j, lambda *a: False),
                           lambda: self.allowed)

    def evidence(self, req):
        accepted = dict(workspace=WORKSPACE, sender=SENDER, destination=req['destination'], reference='mock:'+req['operation_id'])
        observed = dict(accepted, thread=req['thread'], text=req['content'])
        return dict(raw_response={'fixture':'original-send'}, acceptance=accepted,
                    raw_readback={'fixture':'original-read'}, observation=observed)

    def test_first_request_is_original_and_durable(self):
        before = self.j.snapshot()['controlled_slack']['binding']
        req = self.h.prepare_next()
        self.assertEqual(req['operation_id'], self.keys[0])
        self.assertEqual(req['content'], before[self.keys[0]]['text'])
        state = self.j.snapshot()
        self.assertEqual(state['messages'][self.keys[0]]['state'], 'sending')
        self.assertEqual(state['messages'][self.keys[0]]['attempts'], 1)
        self.assertEqual(state['root_handoff']['requests'][self.keys[0]]['state'], 'reserved')
        self.assertEqual(state['root_handoff']['evidence'], [])
        self.assertEqual(state['controlled_slack']['binding'], before)

    def test_no_reissue_pending_after_restart(self):
        self.h.prepare_next()
        self.j.close()
        self.j = SlackJournal(self.path)
        self.h = self.open_handoff()
        with self.assertRaises(ProtocolError):
            self.h.prepare_next()
        self.assertEqual(len(self.h.status()['requests']), 1)

    def test_acceptance_not_verification(self):
        req = self.h.prepare_next()
        e = self.evidence(req)
        e.update(raw_readback=None, observation=None)
        self.assertEqual(self.h.reconcile(req['request_sha256'], **e), 'accepted')
        with self.assertRaises(ProtocolError):
            self.h.prepare_next()
        self.assertEqual(self.h.reconcile(req['request_sha256'], **self.evidence(req)), 'verified')
        self.assertEqual(self.h.prepare_next()['operation_id'], self.keys[1])

    def test_mismatch_freezes_all_dimensions(self):
        req = self.h.prepare_next()
        for field, value in [('workspace','wrong'),('sender','wrong'),('destination','wrong'),
                             ('reference','wrong'),('thread','parent'),('text','changed')]:
            e = self.evidence(req)
            e['observation'][field] = value
            self.assertNotEqual(self.h.reconcile(req['request_sha256'], **e), 'verified')
        with self.assertRaises(ProtocolError):
            self.h.prepare_next()

    def test_no_receipts_no_claim(self):
        req = self.h.prepare_next()
        e = self.evidence(req)
        e.update(raw_response=None, raw_readback=None)
        self.assertEqual(self.h.reconcile(req['request_sha256'], **e), 'unknown')
        with self.assertRaises(ProtocolError):
            self.h.prepare_next()

    def test_unknown_request_rejected(self):
        self.h.prepare_next()
        with self.assertRaises(ProtocolError):
            self.h.reconcile('foreign')

    def test_withdrawal_stops_next_but_allows_readback(self):
        req = self.h.prepare_next()
        self.allowed = False
        self.assertEqual(self.h.reconcile(req['request_sha256'], **self.evidence(req)), 'verified')
        with self.assertRaises(ProtocolError):
            self.h.prepare_next()

    def test_lost_response_exact_readback_can_settle(self):
        req = self.h.prepare_next()
        e = self.evidence(req)
        e.update(raw_response=None, acceptance=None)
        self.assertEqual(self.h.reconcile(req['request_sha256'], **e), 'verified')

    def test_binding_tamper_blocks(self):
        with self.j.transaction() as state:
            state['messages'][self.keys[0]]['text'] = 'changed'
        with self.assertRaises(ProtocolError):
            self.h.prepare_next()

    def test_three_sequential_mock_receipts_restart_zero_new_requests(self):
        for key in self.keys:
            req = self.h.prepare_next()
            self.assertEqual(req['operation_id'], key)
            self.assertEqual(self.h.reconcile(req['request_sha256'], **self.evidence(req)), 'verified')
        before = self.j.snapshot()
        self.j.close()
        pid = os.fork()
        if pid == 0:
            try:
                self.j = SlackJournal(self.path)
                assert self.open_handoff().prepare_next() is None
                assert self.j.snapshot() == before
                self.j.close()
                os._exit(0)
            except BaseException:
                os._exit(1)
        _, status = os.waitpid(pid,0)
        self.j = SlackJournal(self.path)
        self.assertEqual(os.waitstatus_to_exitcode(status),0)
        self.assertEqual(sum(m['attempts'] for m in self.j.snapshot()['messages'].values()),3)
        self.assertTrue(all(m['human_read']=='unknown' for m in self.j.snapshot()['messages'].values()))
