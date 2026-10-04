"""Regression cases for independent review findings and follow-up edge inspection."""

from dataclasses import replace
import unittest

from dispatcher.adapters import ReservationObservation
from dispatcher.model import Check, DeliveryState, EventKind, ProtocolError, ReconciliationRequired, ReturnClass, Status
from tests.support import Harness, REQUIRED, authorization, brief, gates, routes


class IndependentReviewRegressions(unittest.TestCase):
    def test_pause_hold_survives_uncertain_commit(self):
        h = Harness()
        h.working()
        h.repo.fail_after_write = True
        with self.assertRaises(ReconciliationRequired):
            h.engine.pause(h.lineage, authorization("pause"), "stop requested; actual state unknown")
        h.repo.reconcile(h.job_id, "Dẹkun")
        self.assertEqual(h.record.hold_reason, "Paused")
        self.assertEqual(h.record.row.status, Status.BLOCKED)
        with self.assertRaises(ProtocolError):
            h.engine.start(h.lineage, h.observation(), reconciliation="active original run")

    def test_unknown_failed_unchecked_or_empty_verification_cannot_complete(self):
        for check in (Check(None, "inspect", "unknown"), Check(False, "test", "failed"),
                      Check(True, "inspect", "Unknown source"), Check(True, "test", "Not tested: unavailable"),
                      Check(True, "", "artifact"), Check(True, "inspect", "")):
            h = Harness()
            h.review()
            with self.subTest(check=check), self.assertRaises(ProtocolError):
                h.engine.complete(h.lineage, h.verification(criteria_evidence={"engine": check, "tests": check}))
            self.assertEqual(h.record.row.status, Status.REVIEW)

    def test_original_reserved_run_can_be_recovered_without_redispatch(self):
        h = Harness()
        h.ready()
        h.executor.mode = "unknown"
        h.dispatch()
        with self.assertRaises(ProtocolError):
            h.engine.start(h.lineage, h.observation(), reconciliation="cannot start with empty run ID")
        recovered = ReservationObservation(h.lineage, h.record.nonce, "Codex", "fake-codex",
                                           h.observation(worker_run="recovered-original"))
        with self.assertRaises(ProtocolError):
            h.engine.recover_admission(h.lineage, replace(recovered, nonce="wrong-nonce"))
        h.engine.recover_admission(h.lineage, recovered)
        self.assertEqual(h.record.row.status, Status.BLOCKED)
        h.engine.start(h.lineage, recovered.run, reconciliation="original reserved identity and activity verified")
        self.assertEqual(h.record.row.status, Status.WORKING)
        self.assertEqual(h.executor.calls, 1)

    def test_obsolete_unsent_progress_reports_current_cancellation(self):
        h = Harness()
        h.ready()
        old_key = next(e.key for e in h.record.events if e.kind == EventKind.TRANSITION)
        h.dispatch()
        h.engine.cancel(h.lineage, authorization("cancel"), "stop requested; outcome unresolved")
        h.engine.deliver(h.lineage, old_key, h.messenger)
        delivery = h.record.deliveries[old_key]
        self.assertIn("current status Cancelled", delivery.text)
        self.assertEqual(delivery.state, DeliveryState.VERIFIED)
        self.assertEqual(h.record.row.status, Status.CANCELLED)

    def test_cancelled_old_run_can_be_confirmed_stopped_after_reopening(self):
        h = Harness()
        h.working()
        prior = h.lineage
        stopped = ReservationObservation(prior, h.record.nonce, "Codex", "fake-codex",
                                          h.observation(state="stopped"))
        h.engine.cancel(prior, authorization("cancel"), "stop requested; unknown")
        h.engine.reopen(prior, authorization("reopen"), "fresh-epoch-002", "residual effects retained")
        with self.assertRaises(ProtocolError):
            h.ready()
        h.engine.reconcile_prior_attempt(h.lineage, prior, stopped, "confirmed no external side effects")
        h.ready()
        h.dispatch()
        self.assertEqual(h.executor.calls, 2)
        self.assertEqual(h.record.row.output, "")

    def test_inconsistent_full_claim_is_classified_partial(self):
        h = Harness()
        h.working()
        h.engine.receive(h.envelope(remaining="unfinished tests", claimed_class=ReturnClass.FULL))
        self.assertEqual(h.record.return_class, ReturnClass.PARTIAL)
        with self.assertRaises(ProtocolError):
            h.engine.complete(h.lineage, h.verification())

    def test_isolation_requires_specific_authority(self):
        h = Harness()
        h.working()
        h.engine.block(h.lineage, gate="execution", reason="uncertain execution", evidence="timeout",
                       owner="Dẹkun", next_action="inspect", execution_state="Unknown")
        with self.assertRaises(ProtocolError):
            h.engine.retry(h.lineage, authorization("retry"), "isolated-002", "separate sandbox",
                           gates(), routes(), REQUIRED, isolation=True)
        h.engine.retry(h.lineage, authorization("isolated_retry"), "isolated-002",
                       "owner specifically approved isolated filesystem; effects cannot overlap",
                       gates(), routes(), REQUIRED, isolation=True)
        self.assertEqual(h.record.attempts[0].execution_state, "Isolated")
        h.dispatch()
        self.assertEqual(h.executor.calls, 2)

    def test_prior_specification_is_retained_in_revision_audit(self):
        h = Harness()
        h.working()
        old = h.record.brief
        h.engine.clarify(h.lineage, authorization("clarify"), brief(criteria=("engine", "tests", "docs")),
                         "safe incorporation acknowledged")
        event = next(e for e in reversed(h.record.events) if e.kind == EventKind.REVISION)
        self.assertEqual(event.data["previous_brief"]["criteria"], old.criteria)

    def test_old_activity_cannot_resolve_later_execution_uncertainty(self):
        h = Harness()
        h.working()
        old = h.observation()
        h.now = "2026-10-04T06:05:00+00:00"
        h.engine.observe_run(h.lineage, h.observation(state="unknown", observed_at=h.now), "inspect original run")
        with self.assertRaises(ProtocolError):
            h.engine.start(h.lineage, old, reconciliation="old signal is insufficient")
        with self.assertRaises(ProtocolError):
            h.engine.observe_run(h.lineage, old, "stale observation")
        h.engine.start(h.lineage, h.observation(observed_at=h.now), reconciliation="renewed activity inspected")
        self.assertEqual(h.record.last_signal_at, h.now)

    def test_valid_return_during_pause_is_retained_until_explicit_resume(self):
        h = Harness()
        h.working()
        h.engine.pause(h.lineage, authorization("pause"), "pause requested")
        h.engine.receive(h.envelope())
        self.assertEqual(h.record.row.status, Status.BLOCKED)
        self.assertEqual(h.record.hold_reason, "Paused")
        with self.assertRaises(ProtocolError):
            h.engine.review_blocked(h.lineage, "cannot bypass pause")
        h.engine.resume(h.lineage, authorization("resume"), "explicit resume to review returned work")
        h.engine.review_blocked(h.lineage, "current result can now be assessed")
        h.engine.complete(h.lineage, h.verification())
        self.assertEqual(h.record.row.status, Status.DONE)

    def test_return_timestamp_before_current_execution_is_rejected(self):
        h = Harness()
        h.working()
        h.engine.receive(h.envelope(observed_at="2026-10-04T05:59:00+00:00"))
        self.assertEqual(h.record.row.status, Status.WORKING)
        self.assertEqual(h.record.events[-1].kind, EventKind.REJECTION)


if __name__ == "__main__":
    unittest.main()
