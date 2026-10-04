"""All Slack fixtures local; no actual Slack clients or calls."""
from dataclasses import replace
import tempfile
import unittest

from dispatcher.slack import Command, Grant, Readback, SlackBoundary, SlackConfig, SlackJournal
from dispatcher.model import ProtocolError, ReturnClass, Status
from tests.support import Harness, brief, source, gates, routes, REQUIRED


class Provider:
    def __init__(self):
        self.messages = {}
        self.calls = 0
        self.mode = "ok"
        self.unknown = False

    def inspect(self, key, destination, thread):
        if self.unknown:
            return Readback("unknown")
        return self.messages.get(key, Readback("absent"))

    def send(self, key, destination, thread, text):
        self.calls += 1
        if self.mode == "reject":
            from dispatcher.adapters import RejectedDelivery
            raise RejectedDelivery("mock rejection")
        if self.mode != "missing":
            self.messages[key] = Readback("found", key, destination, thread, text, "mock:1")
        if self.mode == "crash":
            raise KeyboardInterrupt("mock process crash after send")
        if self.mode == "timeout":
            raise TimeoutError("mock response lost")
        if self.mode == "accepted":
            self.unknown = True
        return "mock:1"


class SlackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.h = Harness()
        self.path = self.temp.name + "/slack.sqlite"
        self.j = SlackJournal(self.path)
        self.addCleanup(lambda: self.j.close())
        self.trusted = set()
        self.b = SlackBoundary(self.h.engine, self.j, lambda g, c: g.fingerprint in self.trusted)
        self.p = Provider()

    def command(self, **kw):
        return replace(Command(source(channel=SlackConfig().command), "intake", "AJ-0011",
                               "VA-SLACK-0011-01", brief(outcome="Slack boundary")), **kw)

    def submit(self, c):
        self.trusted.add(c.fingerprint)
        return self.b.command(c, Grant(c.fingerprint, "mock owner authentication"))

    def restart(self):
        self.j.close()
        self.j = SlackJournal(self.path)
        self.b = SlackBoundary(self.h.engine, self.j, lambda g, c: g.fingerprint in self.trusted)

    def material(self):
        self.h.review()
        self.b.sync(self.h.job_id)
        return next(iter(self.j.snapshot()["messages"]))

    def test_normal_intake_ack_and_duplicate_restart(self):
        c = self.command()
        self.assertEqual(self.submit(c), "AJ-0011")
        key = "ack/" + c.key
        self.assertEqual(self.b.deliver(key, self.p), "verified")
        self.restart()
        self.assertEqual(self.submit(c), "AJ-0011")
        self.b.deliver(key, self.p)
        self.assertEqual(self.p.calls, 1)
        self.assertEqual(self.j.snapshot()["messages"][key]["human_read"], "unknown")

    def test_duplicate_instruction_different_source(self):
        self.submit(self.command())
        c = self.command(source=source("101.1", channel=SlackConfig().command), job_id="AJ-0012")
        self.assertEqual(self.submit(c), "AJ-0011")
        self.assertEqual(len(self.h.repo.all()), 2)

    def test_observer_receipt_no_job(self):
        c = self.command(action="observe", brief=None)
        self.assertEqual(self.submit(c), "")
        self.restart()
        self.assertEqual(self.submit(c), "")
        self.assertEqual(len(self.h.repo.all()), 1)

    def test_forged_grant_unrelated_channel_or_agent(self):
        c = self.command()
        with self.assertRaises(ProtocolError):
            self.b.command(c, Grant(c.fingerprint, "forged"))
        for change in (dict(channel="unrelated"), dict(author="agent"), dict(authenticated=False),
                       dict(workspace="foreign")):
            with self.subTest(change=change), self.assertRaises(ProtocolError):
                self.submit(replace(c, source=replace(c.source, **change)))
        self.assertFalse(self.j.snapshot()["commands"])

    def test_scope_binding_and_assignment(self):
        c = self.command()
        self.trusted.add(c.fingerprint)
        with self.assertRaises(ProtocolError):
            self.b.command(replace(c, action="cancel"), Grant(c.fingerprint, "trusted"))
        with self.assertRaises(ProtocolError):
            self.submit(replace(c, brief=brief(explicit_worker="")))

    def test_edited_instruction_requires_revision(self):
        c = self.command()
        self.submit(c)
        with self.assertRaises(ProtocolError):
            self.submit(replace(c, source=replace(c.source, version="2")))

    def test_payload_collision(self):
        c = self.command()
        self.submit(c)
        with self.assertRaises(ProtocolError):
            self.submit(replace(c, nonce="different-nonce"))

    def test_supersession_and_late_return(self):
        self.h.review()
        old = self.h.envelope()
        c = self.command(action="revise", job_id=self.h.job_id, lineage=self.h.lineage,
                         brief=brief(scope="updated bounded scope"), evidence="old run completed; effects retained")
        self.submit(c)
        self.h.engine.receive(old)
        self.assertEqual(self.h.record.row.status, Status.INTAKE)
        self.assertEqual(self.h.record.lineage.spec_revision, 2)
        self.assertIsNone(self.h.record.current_attempt)

    def test_cancel_withdrawal_and_late_return(self):
        self.h.working()
        old = self.h.envelope()
        self.submit(self.command(action="cancel", job_id=self.h.job_id, lineage=self.h.lineage,
                                 evidence="stop requested; physical termination unconfirmed"))
        self.h.engine.receive(old)
        self.assertEqual(self.h.record.row.status, Status.CANCELLED)
        self.assertTrue(self.h.record.current_attempt.fenced)

    def test_route_and_admission_not_start(self):
        self.h.ready()
        with self.assertRaises(ProtocolError):
            self.h.engine.dispatch(self.h.lineage, gates(), routes(authorized=False), REQUIRED, self.h.executor)
        self.h.dispatch()
        self.assertEqual(self.h.record.row.status, Status.READY)
        with self.assertRaises(ProtocolError):
            self.h.engine.receive(self.h.envelope())
        self.b.sync(self.h.job_id)
        self.assertFalse(self.j.snapshot()["messages"])

    def test_completion_requires_verification(self):
        self.h.review()
        with self.assertRaises(ProtocolError):
            self.h.engine.complete(self.h.lineage, self.h.verification(checker="Codex"))
        self.assertEqual(self.h.record.row.status, Status.REVIEW)
        self.h.engine.complete(self.h.lineage, self.h.verification())
        self.b.sync(self.h.job_id)
        self.assertEqual(len(self.j.snapshot()["messages"]), 4)

    def test_partial_and_blocked_no_completion(self):
        for kind in (ReturnClass.PARTIAL, ReturnClass.BLOCKED):
            with self.subTest(kind=kind):
                h = Harness()
                h.working()
                h.engine.receive(h.envelope(claimed_class=kind, remaining="work remains", blockers="dependency"))
                with self.assertRaises(ProtocolError):
                    h.engine.complete(h.lineage, h.verification())
                b = SlackBoundary(h.engine, self.j, lambda g, c: False)
                b.sync(h.job_id)
                self.assertTrue(self.j.snapshot()["messages"])
                # separate canonical journal per independent scenario
                with self.j.transaction() as state:
                    state["messages"] = {}

    def test_missing_ack_is_durable_not_execution(self):
        c = self.command()
        self.submit(c)
        self.p.mode = "missing"
        self.assertEqual(self.b.deliver("ack/" + c.key, self.p), "accepted")
        self.restart()
        self.b.deliver("ack/" + c.key, self.p)
        self.assertEqual(self.p.calls, 1)
        self.assertEqual(self.h.repo.read("AJ-0011").row.status, Status.INTAKE)

    def test_uncertain_ack_reconciles_original(self):
        c = self.command()
        self.submit(c)
        self.p.mode = "timeout"
        self.assertEqual(self.b.deliver("ack/" + c.key, self.p), "verified")
        self.assertEqual(self.p.calls, 1)

    def test_accepted_without_readback_not_surfaced(self):
        key = self.material()
        self.p.mode = "accepted"
        self.assertEqual(self.b.deliver(key, self.p), "accepted")
        self.assertIsNotNone(self.b.audit_surface(self.h.job_id))
        self.restart()
        self.b.deliver(key, self.p)
        self.assertEqual(self.p.calls, 1)
        self.p.unknown = False
        self.assertEqual(self.b.deliver(key, self.p), "verified")
        self.assertEqual(self.p.calls, 1)

    def test_crash_after_send_before_marker(self):
        key = self.material()
        self.p.mode = "crash"
        with self.assertRaises(KeyboardInterrupt):
            self.b.deliver(key, self.p)
        self.restart()
        self.assertEqual(self.b.deliver(key, self.p), "verified")
        self.assertEqual(self.p.calls, 1)

    def test_thread_only_escalation_does_not_surface(self):
        self.h.engine.escalate(self.h.lineage, "decision", facts="blocked", decision="choose scope",
                               recommendation="reduce", consequence="wait", deadline="next control")
        self.b.sync(self.h.job_id)
        messages = self.j.snapshot()["messages"]
        self.assertEqual(len(messages), 3)
        key = next(k for k in messages if k.endswith("/attention"))
        m = messages[key]
        self.p.messages[key] = Readback("found", key, m["destination"], "thread-only", m["text"], "mock:2")
        self.assertEqual(self.b.deliver(key, self.p), "unknown")
        self.assertIsNotNone(self.b.audit_surface(self.h.job_id))
        self.assertEqual(self.p.calls, 0)

    def test_shared_retry_fallback_budget_and_circuit(self):
        key = self.material()
        self.p.mode = "reject"
        self.b.deliver(key, self.p)
        self.b.recover(self.h.job_id, "mock changed condition", lambda group, evidence: True)
        self.b.deliver(key, self.p)
        self.assertEqual(self.p.calls, 2)
        self.assertTrue(self.j.snapshot()["incidents"][self.h.job_id]["circuit"])
        with self.assertRaises(ProtocolError):
            self.b.recover(self.h.job_id, "fallback", lambda group, evidence: True)
        self.b.deliver(key, self.p)
        self.assertEqual(self.p.calls, 2)

    def test_unknown_cannot_replay_even_with_recovery(self):
        key = self.material()
        self.p.mode = "accepted"
        self.b.deliver(key, self.p)
        self.b.recover(self.h.job_id, "mock change", lambda group, evidence: True)
        self.b.deliver(key, self.p)
        self.assertEqual(self.p.calls, 1)

    def test_intake_crash_reconciles_core_without_reapply(self):
        c = self.command()
        original = self.h.engine.intake
        def crash(*args, **kwargs):
            original(*args, **kwargs)
            raise KeyboardInterrupt()
        self.h.engine.intake = crash
        with self.assertRaises(KeyboardInterrupt):
            self.submit(c)
        self.restart()
        with self.assertRaises(ValueError):
            self.submit(c)
        self.assertEqual(self.b.reconcile_command(c), "AJ-0011")
        self.assertEqual(self.submit(c), "AJ-0011")

    def test_deduplicated_surface_and_no_chatter(self):
        self.h.working()
        self.b.sync(self.h.job_id)
        self.assertFalse(self.j.snapshot()["messages"])
        self.h.engine.receive(self.h.envelope())
        self.b.sync(self.h.job_id)
        self.b.sync(self.h.job_id)
        self.assertEqual(len(self.j.snapshot()["messages"]), 2)
        for key in self.j.snapshot()["messages"]:
            self.b.deliver(key, self.p)
        self.assertIsNone(self.b.audit_surface(self.h.job_id))


from tests.test_sheets_writer import WriterFixture, AUTH
from dispatcher.engine import Dispatcher
from dispatcher.sheets_repository import SheetsRepository
from tests.support import NOW


class SlackSheetsIntegration(WriterFixture):
    def test_full_durable_repository_restart_and_exclusive_writer(self):
        journal = SlackJournal(self.temp.name + "/slack.sqlite")
        self.addCleanup(journal.close)
        def boundary():
            repo = SheetsRepository(self.writer, self.token, authority_ref=AUTH,
                                    context_ref="synthetic://context", condition="verified-base-context",
                                    route="mock-route")
            core = Dispatcher(repo, clock=lambda: NOW)
            return SlackBoundary(core, journal, lambda g, c: True)
        adapter = boundary()
        c = Command(source(channel=SlackConfig().command), "intake", "AJ-0011",
                    "VA-SLACK-0011-01", brief())
        grant = Grant(c.fingerprint, "synthetic authenticated root scope")
        adapter.command(c, grant)
        self.restart()
        self.reclaim()  # explicit mock root retirement and new exclusive epoch
        adapter = boundary()
        self.assertEqual(adapter.command(c, grant), "AJ-0011")
        row = adapter.core.repository.read("AJ-0011")
        self.assertEqual(len(row.row.to_cells()), 17)
        self.assertEqual(len(self.mock.calls), 1)
        forged = Dispatcher(adapter.core.repository, writer="other-agent", clock=lambda: NOW)
        adapter = SlackBoundary(forged, journal, lambda g, c: True)
        with self.assertRaises(ProtocolError):
            adapter.command(c, grant)
