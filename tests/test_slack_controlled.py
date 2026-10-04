"""Offline fixtures only; no live tool callbacks are installed."""
import os
import tempfile
import unittest
from dataclasses import replace
from dispatcher.model import ProtocolError
from dispatcher.slack import SlackBoundary, SlackJournal, Readback
from dispatcher.slack_controlled import (
    Acceptance, ControlledTransport, Observation, RouteIdentity,
    ROUTE, WORKSPACE, SENDER, bind_synthetic,
)
from tests.support import Harness


class ControlledTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = self.temp.name + '/journal.sqlite'
        self.j = SlackJournal(self.path)
        self.addCleanup(lambda: self.j.close())
        self.keys = bind_synthetic(self.j)
        self.b = SlackBoundary(Harness().engine, self.j, lambda *args: False)
        self.identity = RouteIdentity(WORKSPACE, SENDER, ROUTE, 'mock-only-auth-proof')
        self.calls = []
        self.messages = {}
        self.allowed = True
        self.complete = True
        self.crash = False
        self.p = self.provider()

    def read(self, key, dest, thread):
        r = self.messages.get(key, Readback('absent'))
        return Observation(r, WORKSPACE, SENDER, {'fixture': 'destination-read'}, self.complete)

    def send(self, key, dest, thread, text):
        self.calls.append(key)
        self.messages[key] = Readback('found', key, dest, thread, text, 'mock:' + key)
        if self.crash:
            raise KeyboardInterrupt('mock process death')
        return Acceptance('mock:' + key, {'fixture': 'original-acceptance'})

    def provider(self):
        return ControlledTransport(self.j, self.identity, lambda i: True,
                                   lambda: self.allowed, self.read, self.send)

    def test_three_exact_bindings_and_idempotence(self):
        before = self.j.snapshot()
        self.assertEqual(bind_synthetic(self.j), self.keys)
        self.assertEqual(self.j.snapshot(), before)
        self.assertEqual(len(self.keys), 3)
        for item in before['messages'].values():
            self.assertEqual(item['thread'], '')
            self.assertIn('Synthetic test — no action required', item['text'])
            self.assertEqual(item['attempts'], 0)
        self.assertEqual(before['commands'], {})

    def test_three_verified_and_separate_process_restart_zero_send(self):
        for key in self.keys:
            self.assertEqual(self.b.deliver(key, self.p), 'verified')
        self.assertEqual(len(self.calls), 3)
        self.j.close()
        pid = os.fork()
        if pid == 0:
            try:
                self.j = SlackJournal(self.path)
                self.b = SlackBoundary(Harness().engine, self.j, lambda *args: False)
                p = self.provider()
                def forbidden(*args):
                    raise AssertionError('fourth send forbidden')
                p.dispatch = forbidden
                for key in self.keys:
                    assert self.b.deliver(key, p) == 'verified'
                state = self.j.snapshot()
                assert sum(x['calls'] for x in state['controlled_slack']['operations'].values()) == 3
                assert all(x['attempts'] == 1 and x['human_read'] == 'unknown'
                           for x in state['messages'].values())
                self.j.close()
                os._exit(0)
            except BaseException:
                os._exit(1)
        _, status = os.waitpid(pid, 0)
        self.j = SlackJournal(self.path)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        self.assertEqual(len(self.calls), 3)

    def test_wrong_identity_never_sends(self):
        for identity in (replace(self.identity, sender='U0C6LCCH9QR'),
                         replace(self.identity, workspace='other'),
                         replace(self.identity, route='other'), replace(self.identity, evidence='')):
            self.p.identity = identity
            self.assertEqual(self.b.deliver(self.keys[0], self.p), 'unknown')
        self.assertEqual(self.calls, [])

    def test_unverified_identity_never_sends(self):
        self.p.verify_identity = lambda i: False
        self.assertEqual(self.b.deliver(self.keys[0], self.p), 'unknown')
        self.assertEqual(self.calls, [])

    def test_withdrawal_before_send(self):
        def read(*args):
            result = self.read(*args)
            self.allowed = False
            return result
        self.p.read = read
        self.b.deliver(self.keys[0], self.p)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.j.snapshot()['controlled_slack']['operations'], {})

    def test_incomplete_absence_never_sends(self):
        self.complete = False
        self.assertEqual(self.b.deliver(self.keys[0], self.p), 'unknown')
        self.assertEqual(self.calls, [])

    def test_crash_reconcile_no_replay(self):
        self.crash = True
        key = self.keys[0]
        with self.assertRaises(KeyboardInterrupt):
            self.b.deliver(key, self.p)
        self.assertEqual(self.j.snapshot()['messages'][key]['state'], 'sending')
        self.assertEqual(self.b.deliver(key, self.p), 'verified')
        self.assertEqual(len(self.calls), 1)

    def test_post_attempt_absence_stays_unknown(self):
        key = self.keys[0]
        self.b.deliver(key, self.p)
        self.messages.clear()
        item = self.j.snapshot()['messages'][key]
        self.assertEqual(self.p.inspect(key, item['destination'], '') .state, 'unknown')
        with self.assertRaises(ProtocolError):
            self.p.send(key, item['destination'], '', item['text'])
        self.assertEqual(len(self.calls), 1)

    def test_content_destination_scope_and_thread_rejected(self):
        item = self.j.snapshot()['messages'][self.keys[0]]
        for key, dest, thread, text in (
            ('other', item['destination'], '', item['text']),
            (item['key'], 'other', '', item['text']),
            (item['key'], item['destination'], 'reply', item['text']),
            (item['key'], item['destination'], '', 'changed')):
            with self.assertRaises(ProtocolError):
                self.p.send(key, dest, thread, text)
        self.assertEqual(self.calls, [])

    def test_wrong_author_readback_not_verified(self):
        key = self.keys[0]
        item = self.j.snapshot()['messages'][key]
        self.p.read = lambda *args: Observation(
            Readback('found', key, item['destination'], '', item['text'], 'mock:1'),
            WORKSPACE, 'U0C6LCCH9QR', {'fixture': 'wrong-author'})
        self.assertEqual(self.b.deliver(key, self.p), 'unknown')
        self.assertEqual(self.calls, [])

    def test_accepted_without_presence_is_not_verified(self):
        self.p.dispatch = lambda *args: Acceptance('mock:accepted', {'fixture': 'accepted-only'})
        self.assertEqual(self.b.deliver(self.keys[0], self.p), 'accepted')
        self.assertEqual(self.b.deliver(self.keys[0], self.p), 'unknown')
        state = self.j.snapshot()
        self.assertEqual(state['messages'][self.keys[0]]['attempts'], 1)
        self.assertEqual(state['messages'][self.keys[0]]['human_read'], 'unknown')
        self.assertEqual(len(state['controlled_slack']['operations']), 1)
