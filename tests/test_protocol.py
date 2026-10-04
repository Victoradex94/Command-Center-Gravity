"""Nine explicit protocol scenario families plus AJ-0006 failure/recovery simulation."""

from dataclasses import fields, replace
import json
import unittest

from dispatcher.adapters import FakeMessenger
from dispatcher.engine import ALLOWED_TRANSITIONS, Dispatcher
from dispatcher.model import (AGENT_JOB_COLUMNS, AgentJob, Conflict, DeliveryState, EventKind,
                              Gate, Lineage, ProtocolError, ReconciliationRequired, ReturnClass,
                              Status, choose_route, timestamp)
from tests.support import (Harness, NOW, REQUIRED, authorization, brief, gates, routes, source)


class Family01IntakeAndDuplicates(unittest.TestCase):
    def test_exact_schema_and_seven_statuses(self):
        self.assertEqual(len(fields(AgentJob)), 17)
        self.assertEqual(len(AGENT_JOB_COLUMNS), 17)
        self.assertEqual([s.value for s in Status],
                         ["Intake", "Ready", "Working", "Review", "Blocked", "Done", "Cancelled"])
        row = Harness().record.row
        self.assertEqual(AgentJob.from_cells(row.to_cells()), row)
        for cells in ([""] * 16, [""] * 18, row.to_cells()[:4] + ["Paused"] + row.to_cells()[5:]):
            with self.assertRaises(ProtocolError):
                AgentJob.from_cells(cells)

    def test_acknowledgement_precedes_gates_and_no_fyi_row(self):
        h = Harness()
        self.assertEqual(h.record.events[0].kind, EventKind.ACKNOWLEDGEMENT)
        self.assertEqual(h.record.row.status, Status.INTAKE)
        self.assertIsNone(h.engine.intake("AJ-0099", "nonce-0099", source("fyi"), brief(), actionable=False))
        self.assertEqual(len(h.repo.all()), 1)
        ack = h.engine.deliver_acknowledgement(source(), h.messenger)
        self.assertEqual(ack.thread, source().thread)
        self.assertEqual(ack.state, DeliveryState.VERIFIED)

    def test_forged_or_quoted_authority_rejected(self):
        h = Harness()
        for forged in (source(author="another-user"), source(workspace="other-workspace"),
                       source(authenticated=False), source(permalink="")):
            with self.assertRaises(ProtocolError):
                h.engine.intake("AJ-0099", "nonce-0099", forged, brief())
        self.assertEqual(len(h.repo.all()), 1)

    def test_exact_and_semantic_duplicates_never_create_or_dispatch(self):
        h = Harness()
        h.working()
        for event, duplicate_brief in ((source(), brief()),
                                       (source("new-message"), brief(outcome=" BUILD  BOUNDED CORE "))):
            existing = h.engine.intake("AJ-0099", "nonce-0099", event, duplicate_brief)
            self.assertEqual(existing.lineage, h.lineage)
            self.assertEqual(existing.row.job_id, "AJ-0007")
        self.assertEqual(len(h.repo.all()), 1)
        self.assertEqual(h.executor.calls, 1)
        self.assertEqual(len(h.record.sources), 2)

    def test_completed_duplicate_returns_existing_output(self):
        h = Harness()
        h.done()
        result = h.engine.intake("AJ-0099", "nonce-0099", source("later"), brief())
        self.assertEqual(result.row.status, Status.DONE)
        self.assertEqual(result.row.output, h.record.row.output)
        self.assertEqual(result.lineage.attempt, 1)

    def test_nonce_lineage_and_timestamp_validation(self):
        for revision in (0, -1, True):
            with self.assertRaises(ProtocolError):
                Lineage("AJ-0007", revision, 1, 1)
        with self.assertRaises(ProtocolError):
            timestamp("2026-10-04T06:00:00")
        h = Harness()
        with self.assertRaises(ProtocolError):
            h.engine.intake("AJ-0010", "bad", source("different"), brief(scope="different"))


class Family02RoutingAndOverride(unittest.TestCase):
    def test_named_unavailable_worker_is_preserved(self):
        decision = choose_route(routes(), REQUIRED, "Gemini", NOW)
        self.assertFalse(decision.eligible)
        self.assertEqual(decision.worker, "Gemini")
        h = Harness(custom_brief=brief(explicit_worker="Gemini"))
        with self.assertRaisesRegex(ProtocolError, "explicit assignment unavailable"):
            h.ready()
        self.assertEqual(h.record.row.assigned_worker, "Gemini")

    def test_automatic_route_and_override_ignore_cheaper_preference(self):
        candidates = routes() + routes(worker="Other", route="fake-other", preference=100)
        self.assertEqual(choose_route(candidates, REQUIRED, "", NOW).worker, "Other")
        self.assertEqual(choose_route(candidates, REQUIRED, "Codex", NOW).worker, "Codex")

    def test_subscription_or_documentation_is_not_route_proof(self):
        for change in ({"route_verified": False}, {"environment_verified": False},
                       {"result_retrieval_verified": False}, {"authorized": False},
                       {"access": Gate(None, "unknown")}, {"readiness": Gate(False, "offline")},
                       {"capabilities": frozenset({"text"})}, {"evidence": ""},
                       {"checked_at": "2026-10-04T05:00:00Z"}):
            with self.subTest(change=change):
                self.assertFalse(choose_route(routes(**change), REQUIRED, "Codex", NOW).eligible)


class Family03GatesAndSingleWriter(unittest.TestCase):
    def test_blocked_dependency_requires_usable_evidence_and_all_readiness_gates(self):
        h = Harness()
        original_lineage = h.lineage
        prerequisite = AgentJob("AJ-0900", status=Status.BLOCKED)
        failed = Gate(False, "synthetic AJ-0900 required artifact missing; owner Dẹkun")
        with self.assertRaisesRegex(ProtocolError, "dependencies"):
            h.engine.ready(h.lineage, gates(dependencies=failed), routes(), REQUIRED)
        # The coordinator records the concrete failed prerequisite through the public API.
        h.engine.block(h.lineage, gate="dependencies", reason="AJ-0900 artifact unavailable",
                       evidence=failed.evidence, owner="Dẹkun", next_action="retrieve and verify prerequisite artifact",
                       execution_state="Stopped")
        self.assertEqual(h.record.row.status, Status.BLOCKED)
        self.assertEqual(h.record.blocker["gate"], "dependencies")
        self.assertEqual(h.record.blocker["evidence"], failed.evidence)
        with self.assertRaises(ProtocolError):
            h.engine.dispatch(h.lineage, gates(dependencies=failed), routes(), REQUIRED, h.executor)
        self.assertEqual(h.executor.calls, 0)
        self.assertIsNone(h.record.current_attempt)

        # A status edit supplies neither an artifact nor verification of its usability.
        prerequisite.status = Status.DONE
        self.assertEqual((prerequisite.output, prerequisite.verification), ("", ""))
        for insufficient in (Gate(True, ""), Gate(True, prerequisite.status.value), Gate(True, " done ")):
            with self.subTest(insufficient=insufficient), self.assertRaises(ProtocolError):
                h.engine.ready(h.lineage, gates(dependencies=insufficient), routes(), REQUIRED)
            self.assertEqual(h.record.row.status, Status.BLOCKED)
            self.assertEqual(h.executor.calls, 0)

        h.now = "2026-10-04T06:00:30+00:00"
        prerequisite.output = "synthetic://prerequisite/artifact-v1"
        prerequisite.verification = "synthetic readback confirms required input format and content usable"
        resolution = Gate(True, json.dumps({"dependency_id": prerequisite.job_id,
                                            "artifact": prerequisite.output,
                                            "method_and_result": prerequisite.verification,
                                            "checker": "Dẹkun", "checked_at": h.now}, sort_keys=True))
        h.engine.block(h.lineage, gate="readiness", reason="prerequisite resolved; other gates need recheck",
                       evidence=resolution.evidence, owner="Dẹkun", next_action="recheck every start gate",
                       execution_state="Stopped")
        self.assertEqual(h.record.blocker["evidence"], resolution.evidence)
        with self.assertRaises(ProtocolError):
            h.engine.dispatch(h.lineage, gates(dependencies=resolution, checked_at=h.now),
                              routes(checked_at=h.now), REQUIRED, h.executor)
        self.assertEqual(h.executor.calls, 0)

        for name in ("authority", "identity", "capability", "access", "readiness", "return_contract"):
            rechecked = gates(dependencies=resolution, checked_at=h.now,
                              **{name: Gate(False, f"synthetic {name} gate still failed")})
            with self.subTest(gate=name), self.assertRaisesRegex(ProtocolError, name):
                h.engine.ready(h.lineage, rechecked, routes(checked_at=h.now), REQUIRED)
            self.assertEqual(h.record.row.status, Status.BLOCKED)
            self.assertEqual(h.executor.calls, 0)
        with self.assertRaises(ProtocolError):
            h.engine.ready(h.lineage, gates(dependencies=resolution, checked_at=h.now),
                           routes(checked_at=h.now, environment_verified=False), REQUIRED)
        self.assertEqual(h.record.row.status, Status.BLOCKED)

        ready = h.engine.ready(h.lineage, gates(dependencies=resolution, checked_at=h.now),
                               routes(checked_at=h.now), REQUIRED)
        self.assertEqual(ready.row.status, Status.READY)
        self.assertEqual(ready.blocker, {})
        self.assertEqual(json.loads(ready.row.dependency), {"passed": True, "evidence": resolution.evidence})
        recorded_checks = next(e for e in reversed(ready.events) if "gates" in e.data)
        self.assertEqual(recorded_checks.data["gates"]["dependencies"]["evidence"], resolution.evidence)
        self.assertEqual(recorded_checks.data["gates"]["checked_at"], h.now)
        self.assertEqual(h.lineage, original_lineage)
        self.assertEqual(h.executor.calls, 0)
        self.assertIsNone(h.record.current_attempt)

    def test_each_missing_or_unknown_gate_prevents_ready(self):
        for name in ("authority", "identity", "capability", "access", "dependencies", "readiness", "return_contract"):
            for invalid in (Gate(None, "unknown"), Gate(False, "denied"), Gate(True, "")):
                h = Harness()
                with self.subTest(gate=name, invalid=invalid), self.assertRaises(ProtocolError):
                    h.engine.ready(h.lineage, gates(**{name: invalid}), routes(), REQUIRED)
                self.assertEqual(h.record.row.status, Status.INTAKE)

    def test_dispatch_fast_path_requires_no_return_output_or_verification(self):
        h = Harness()
        h.ready()
        h.dispatch()
        self.assertEqual(h.record.row.status, Status.READY)
        self.assertEqual(h.record.row.output, "")
        self.assertEqual(h.record.row.verification, "")
        self.assertEqual(h.record.current_attempt.started_at, "")
        summary = json.loads(h.record.row.return_summary)
        self.assertEqual(summary["ReturnClass"], "")

    def test_incomplete_brief_and_changed_volatile_gate_prevent_dispatch(self):
        h = Harness(custom_brief=brief(parent_evidence_or_reason=""))
        with self.assertRaises(ProtocolError):
            h.ready()
        h = Harness()
        h.ready()
        with self.assertRaises(ProtocolError):
            h.engine.dispatch(h.lineage, gates(access=Gate(False, "revoked")), routes(), REQUIRED, h.executor)
        self.assertEqual(h.executor.calls, 0)
        h.now = "2026-10-04T06:02:00Z"
        with self.assertRaises(ProtocolError):
            h.dispatch()

    def test_workers_cannot_write_and_proxy_is_exclusive(self):
        h = Harness()
        worker = Dispatcher(h.repo, writer="Codex", clock=lambda: NOW)
        with self.assertRaises(ProtocolError):
            worker.ready(h.lineage, gates(), routes(), REQUIRED)
        h.repo.delegate("Dẹkun", "proxy", "record exact coordinator-approved changes only")
        with self.assertRaises(ProtocolError):
            h.ready()
        proxy = Dispatcher(h.repo, writer="proxy", clock=lambda: NOW)
        self.assertEqual(proxy.ready(h.lineage, gates(), routes(), REQUIRED).row.status, Status.READY)

    def test_compare_and_readback_rejects_stale_write(self):
        h = Harness()
        stale = h.record
        h.ready()
        with self.assertRaises(Conflict):
            h.repo.commit(stale, stale.version, stale.lineage, "Dẹkun")
        detached = h.record
        detached.row.status = Status.DONE
        self.assertEqual(h.record.row.status, Status.READY)

    def test_uncertain_append_must_be_reconciled_before_retry(self):
        h = Harness()
        h.repo.fail_after_write = True
        with self.assertRaises(ReconciliationRequired):
            h.engine.intake("AJ-0010", "nonce-0010", source("new"), brief(scope="new bounded scope"))
        with self.assertRaises(ReconciliationRequired):
            h.ready()
        h.repo.reconcile("AJ-0010", "Dẹkun")
        same = h.engine.intake("AJ-0011", "nonce-0011", source("new"), brief(scope="new bounded scope"))
        self.assertEqual(same.row.job_id, "AJ-0010")
        self.assertEqual(len(h.repo.all()), 2)

    def test_uncertain_reservation_never_invokes_executor(self):
        h = Harness()
        h.ready()
        h.repo.fail_after_write = True
        with self.assertRaises(ReconciliationRequired):
            h.dispatch()
        self.assertEqual(h.executor.calls, 0)
        h.repo.reconcile(h.job_id, "Dẹkun")
        h.dispatch()
        self.assertEqual(h.executor.calls, 0)
        self.assertEqual(h.record.current_attempt.execution_state, "Reserved")


class Family04ActualStartAndStaleRuns(unittest.TestCase):
    def test_admission_and_task_id_cannot_establish_working(self):
        h = Harness()
        h.ready()
        h.dispatch()
        with self.assertRaises(ProtocolError):
            h.engine.start(h.lineage, h.observation(substantive=False))
        with self.assertRaises(ProtocolError):
            h.engine.receive(h.envelope())
        self.assertEqual(h.record.row.status, Status.READY)
        h.start()
        self.assertEqual(h.record.row.status, Status.WORKING)
        self.assertEqual(h.record.current_attempt.started_at, NOW)

    def test_duplicate_dispatch_no_second_adapter_call(self):
        h = Harness()
        h.ready()
        h.dispatch()
        h.dispatch()
        self.assertEqual(h.executor.calls, 1)

    def test_uncertain_admission_never_relaunches(self):
        h = Harness()
        h.ready()
        h.executor.mode = "unknown"
        h.dispatch()
        self.assertEqual(h.record.row.status, Status.BLOCKED)
        self.assertEqual(h.record.current_attempt.execution_state, "Unknown")
        with self.assertRaises(ProtocolError):
            h.ready()
        with self.assertRaises(ProtocolError):
            h.engine.retry(h.lineage, authorization("retry"), "corrected-02", "timeout is not stop proof",
                           gates(), routes(), REQUIRED)
        self.assertEqual(h.executor.calls, 1)

    def test_stale_signal_triggers_inspection_and_renewed_evidence_not_redispatch(self):
        h = Harness()
        h.working()
        h.engine.observe_run(h.lineage, h.observation(state="unknown", substantive=False), "inspect now")
        self.assertEqual(h.record.row.status, Status.BLOCKED)
        with self.assertRaises(ProtocolError):
            h.engine.start(h.lineage, h.observation())
        h.engine.start(h.lineage, h.observation(), reconciliation="original run confirmed active; no hold")
        self.assertEqual(h.record.row.status, Status.WORKING)
        self.assertEqual(h.executor.calls, 1)

    def test_all_negative_transition_pairs_and_documented_edges(self):
        record = Harness().record
        engine = Harness().engine
        for before in Status:
            for after in Status:
                record.row.status = before
                with self.subTest(before=before, after=after):
                    if after in ALLOWED_TRANSITIONS[before]:
                        engine._move(record, after, "synthetic matrix check", "synthetic evidence")
                        self.assertEqual(record.row.status, after)
                    else:
                        with self.assertRaises(ProtocolError):
                            engine._move(record, after, "synthetic matrix check", "synthetic evidence")
        record.row.status = Status.INTAKE
        with self.assertRaises(ProtocolError):
            engine._move(record, Status.READY, "", "")


class Family05FullReturnAndVerification(unittest.TestCase):
    def test_full_return_is_review_until_independently_verified(self):
        h = Harness()
        h.review()
        self.assertEqual(h.record.row.status, Status.REVIEW)
        self.assertEqual(h.record.return_class, ReturnClass.FULL)
        h.engine.complete(h.lineage, h.verification())
        self.assertEqual(h.record.row.status, Status.DONE)
        self.assertTrue(h.record.verification.synthetic)
        self.assertTrue(any(d.state == DeliveryState.PENDING for d in h.record.deliveries.values()))

    def test_no_direct_working_to_done_or_worker_self_verification(self):
        h = Harness()
        h.working()
        with self.assertRaises(ProtocolError):
            h.engine.complete(h.lineage, h.verification())
        h.engine.receive(h.envelope())
        with self.assertRaises(ProtocolError):
            h.engine.complete(h.lineage, h.verification(checker="Codex"))

    def test_missing_or_stale_acceptance_evidence_blocks_done(self):
        for change in ({"criteria_evidence": {"engine": "checked"}}, {"artifact_evidence": ""},
                       {"destination_evidence": ""}, {"tests_or_readbacks": ""},
                       {"dependencies_evidence": ""}, {"scope_and_permissions_evidence": ""},
                       {"side_effects_evidence": ""}, {"provenance_evidence": ""},
                       {"parent_reconciliation": ""}, {"limitations": ""},
                       {"lineage": Lineage("AJ-0007", 2, 1, 1)},
                       {"checked_at": "2026-10-04T05:00:00Z"}):
            h = Harness()
            h.review()
            with self.subTest(change=change), self.assertRaises(ProtocolError):
                h.engine.complete(h.lineage, h.verification(**change))
            self.assertEqual(h.record.row.status, Status.REVIEW)

    def test_malformed_return_retained_as_rejected_audit(self):
        for field in ("attempted", "output", "evidence", "remaining", "blockers", "side_effects", "recommendation"):
            h = Harness()
            h.working()
            h.engine.receive(h.envelope(**{field: ""}))
            self.assertEqual(h.record.row.status, Status.WORKING)
            self.assertEqual(h.record.events[-1].kind, EventKind.REJECTION)
            self.assertEqual(h.record.row.output, "")

    def test_identical_return_is_noop_conflicting_return_is_audited(self):
        h = Harness()
        h.working()
        result = h.envelope()
        h.engine.receive(result)
        version = h.record.version
        h.engine.receive(result)
        self.assertEqual(h.record.version, version)
        h.engine.complete(h.lineage, h.verification())
        h.engine.receive(replace(result, output="contradictory output"))
        self.assertEqual(h.record.row.output, result.output)
        self.assertEqual(h.record.row.status, Status.REVIEW)
        self.assertIsNone(h.record.verification)

    def test_done_correction_authorizes_review_only(self):
        h = Harness()
        h.done()
        h.engine.correct_completion(h.lineage, "new failing criterion evidence", "coordinator correction report")
        self.assertEqual(h.record.row.status, Status.REVIEW)
        with self.assertRaises(ProtocolError):
            h.dispatch()


class Family06PartialBlockedAndCorrection(unittest.TestCase):
    def test_partial_output_preserved_and_cannot_complete(self):
        h = Harness()
        h.working()
        h.engine.receive(h.envelope(claimed_class=ReturnClass.PARTIAL, remaining="tests missing"))
        self.assertEqual(h.record.row.status, Status.REVIEW)
        with self.assertRaises(ProtocolError):
            h.engine.complete(h.lineage, h.verification())
        h.engine.block(h.lineage, gate="verification", reason="test artifact missing", evidence="inspected return",
                       owner="Dẹkun", next_action="retrieve evidence", execution_state="Completed")
        self.assertEqual(h.record.row.status, Status.BLOCKED)
        self.assertIn("artifact", h.record.row.output)
        h.engine.review_blocked(h.lineage, "test artifact now available")
        self.assertEqual(h.record.row.status, Status.REVIEW)

    def test_blocked_return_explicit_no_output_and_running_uncertainty(self):
        h = Harness()
        h.working()
        h.engine.receive(h.envelope(claimed_class=ReturnClass.BLOCKED, output="No output yet: access denied",
                                    evidence="Not tested: access denied", remaining="all implementation",
                                    blockers="access gate denied"))
        self.assertEqual(h.record.row.status, Status.BLOCKED)
        self.assertTrue(h.record.blocker["may_still_run"])
        with self.assertRaises(ProtocolError):
            h.engine.retry(h.lineage, authorization("retry"), "retry-0002", "no stop evidence",
                           gates(), routes(), REQUIRED)

    def test_authorized_corrective_attempt_fences_prior_attempt(self):
        h = Harness()
        h.working()
        previous = h.envelope(claimed_class=ReturnClass.PARTIAL, remaining="test fixes")
        h.engine.receive(previous)
        h.engine.retry(h.lineage, authorization("retry"), "retry-0002", "previous run completed; no external effects",
                       gates(), routes(), REQUIRED)
        self.assertEqual(h.lineage.attempt, 2)
        self.assertTrue(h.record.attempts[0].fenced)
        h.dispatch()
        h.start()
        h.engine.receive(previous)
        self.assertEqual(h.record.row.status, Status.WORKING)
        h.engine.receive(h.envelope())
        h.engine.complete(h.lineage, h.verification())
        self.assertEqual(h.record.row.status, Status.DONE)


class Family07CancellationPauseAndSupersession(unittest.TestCase):
    def test_cancelled_late_result_never_reopens_or_overwrites(self):
        h = Harness()
        h.working()
        late = h.envelope()
        h.engine.cancel(h.lineage, authorization("cancel"), "stop requested only; residual effects unknown")
        h.engine.receive(late)
        self.assertEqual(h.record.row.status, Status.CANCELLED)
        self.assertEqual(h.record.row.output, "")
        self.assertEqual(h.record.events[-1].kind, EventKind.REJECTION)
        old = h.engine.intake("AJ-0099", "nonce-0099", source(), brief())
        self.assertEqual(old.row.status, Status.CANCELLED)

    def test_explicit_reopen_advances_epoch_but_unresolved_old_run_cannot_dispatch(self):
        h = Harness()
        h.working()
        h.engine.cancel(h.lineage, authorization("cancel"), "stop requested; still running")
        with self.assertRaises(ProtocolError):
            h.engine.reopen(h.lineage, authorization("retry"), "reopen-002", "old effects unresolved")
        h.engine.reopen(h.lineage, authorization("reopen"), "reopen-002", "old effects unresolved")
        self.assertEqual(h.lineage.run_epoch, 2)
        with self.assertRaises(ProtocolError):
            h.ready()
        with self.assertRaises(ProtocolError):
            h.dispatch()

    def test_done_reopen_preserves_prior_output_and_new_epoch(self):
        h = Harness()
        h.done()
        old_output = h.record.row.output
        h.engine.reopen(h.lineage, authorization("reopen"), "reopen-002", "completed prior run; no effects")
        self.assertEqual(h.record.row.status, Status.INTAKE)
        self.assertEqual(h.record.row.output, old_output)
        h.ready()
        h.dispatch()
        self.assertEqual(h.lineage.run_epoch, 2)

    def test_pause_requires_explicit_resume_and_reconciliation(self):
        h = Harness()
        h.working()
        h.engine.pause(h.lineage, authorization("pause"), "pause requested; physical state unknown")
        with self.assertRaises(ProtocolError):
            h.engine.start(h.lineage, h.observation(), reconciliation="active")
        with self.assertRaises(ProtocolError):
            h.engine.retry(h.lineage, authorization("retry"), "retry-002", "timeout", gates(), routes(), REQUIRED)
        h.engine.resume(h.lineage, authorization("resume"), "explicit resume applies")
        h.engine.start(h.lineage, h.observation(), reconciliation="same run active and safe")
        self.assertEqual(h.executor.calls, 1)

    def test_reassignment_fences_old_worker_and_requires_safe_previous_state(self):
        h = Harness()
        h.working()
        old = h.envelope()
        h.engine.block(h.lineage, gate="assignment", reason="worker change requested", evidence="scope update",
                       owner="Dẹkun", next_action="confirm stop", execution_state="Unknown")
        with self.assertRaises(ProtocolError):
            h.engine.revise(h.lineage, authorization("revise"), brief(explicit_worker="Gemini"),
                            "revision-002", "stop unconfirmed")
        h.engine.observe_run(h.lineage, h.observation(state="stopped"), "review now")
        h.engine.revise(h.lineage, authorization("revise"), brief(explicit_worker="Gemini"),
                        "revision-002", "stop and no side effects verified")
        self.assertEqual((h.lineage.spec_revision, h.lineage.run_epoch), (2, 2))
        self.assertEqual(h.record.row.assigned_worker, "Gemini")
        h.engine.receive(old)
        self.assertEqual(h.record.row.status, Status.INTAKE)
        self.assertEqual(h.record.row.output, "")

    def test_clarification_requires_ack_and_old_revision_return_is_historical(self):
        h = Harness()
        h.working()
        old = h.envelope()
        new_brief = brief(criteria=("engine", "tests", "documentation"))
        with self.assertRaises(ProtocolError):
            h.engine.clarify(h.lineage, authorization("clarify"), new_brief, "")
        h.engine.clarify(h.lineage, authorization("clarify"), new_brief,
                         "current worker acknowledged safe incorporation of revision 2")
        self.assertEqual((h.lineage.spec_revision, h.lineage.run_epoch, h.lineage.attempt), (2, 1, 1))
        h.engine.receive(old)
        self.assertEqual(h.record.row.status, Status.WORKING)
        h.engine.receive(h.envelope())
        self.assertEqual(h.record.row.status, Status.REVIEW)

    def test_wrong_nonce_run_worker_or_attempt_is_rejected_with_evidence(self):
        for change in ({"nonce": "wrong-nonce"}, {"worker": "Gemini"}, {"worker_run": "other-run"},
                       {"lineage": Lineage("AJ-0007", 1, 1, 2)}, {"authenticated": False}):
            h = Harness()
            h.working()
            h.engine.receive(h.envelope(**change))
            self.assertEqual(h.record.row.status, Status.WORKING)
            self.assertEqual(h.record.events[-1].kind, EventKind.REJECTION)


class Family08DeliveryRecovery(unittest.TestCase):
    def test_unknown_send_observed_existing_message_is_not_resent(self):
        h = Harness()
        h.done()
        key = list(h.record.deliveries)[-1]
        h.messenger.mode = "unknown_accepted"
        h.engine.deliver(h.lineage, key, h.messenger)
        self.assertEqual(h.record.deliveries[key].state, DeliveryState.UNKNOWN)
        h.engine.deliver(h.lineage, key, h.messenger)
        self.assertEqual(h.record.deliveries[key].state, DeliveryState.VERIFIED)
        self.assertEqual(h.messenger.calls, 1)
        self.assertEqual(h.record.row.status, Status.DONE)

    def test_uncertain_absence_never_blindly_retries(self):
        h = Harness()
        key = next(iter(h.record.deliveries))
        h.messenger.lookup_unknown = True
        for _ in range(2):
            h.engine.deliver(h.lineage, key, h.messenger)
        self.assertEqual(h.messenger.calls, 0)
        self.assertEqual(h.record.deliveries[key].state, DeliveryState.UNKNOWN)

    def test_definitive_failed_notification_retry_only_after_absence_check(self):
        h = Harness()
        h.done()
        key = list(h.record.deliveries)[-1]
        h.messenger.mode = "failed"
        h.engine.deliver(h.lineage, key, h.messenger)
        self.assertEqual(h.record.deliveries[key].state, DeliveryState.FAILED)
        h.messenger.mode = "ok"
        h.engine.deliver(h.lineage, key, h.messenger)
        self.assertEqual(h.record.deliveries[key].state, DeliveryState.VERIFIED)
        self.assertEqual(h.executor.calls, 1)

    def test_missing_markers_recovered_after_synthetic_crash(self):
        h = Harness()
        h.ready()
        record = h.record
        missing = [e.key for e in record.events if e.kind == EventKind.TRANSITION][0]
        del record.deliveries[missing]
        h.repo.commit(record, record.version, record.lineage, "Dẹkun")
        h.engine.reconcile_delivery_markers(h.lineage)
        self.assertIn(missing, h.record.deliveries)
        h.engine.deliver(h.lineage, missing, h.messenger)
        self.assertEqual(h.record.deliveries[missing].state, DeliveryState.VERIFIED)

    def test_lost_command_ack_does_not_create_execution(self):
        h = Harness()
        h.messenger.mode = "unknown_accepted"
        h.engine.deliver_acknowledgement(source(), h.messenger)
        h.engine.deliver_acknowledgement(source(), h.messenger)
        self.assertEqual(h.messenger.calls, 1)
        self.assertEqual(h.executor.calls, 0)
        self.assertEqual(len(h.repo.all()), 1)


class Family09EscalationParentAndPermissions(unittest.TestCase):
    def test_escalation_deduplicates_and_requires_actual_owner_response(self):
        h = Harness()
        h.review()
        args = dict(facts="override route unavailable", decision="approve bounded route change",
                    recommendation="reconnect original worker", consequence="delivery blocked", deadline="No hard deadline")
        h.engine.escalate(h.lineage, "route", **args)
        version = h.record.version
        h.engine.escalate(h.lineage, "route", **args)
        self.assertEqual(h.record.version, version)
        self.assertEqual(h.record.row.needs_victor, "Yes")
        with self.assertRaises(ProtocolError):
            h.engine.complete(h.lineage, h.verification())
        with self.assertRaises(ProtocolError):
            h.engine.resolve_escalation(h.lineage, "route", authorization("retry"))
        h.engine.resolve_escalation(h.lineage, "route", authorization("resolve"))
        self.assertEqual(h.record.row.needs_victor, "No")

    def test_routine_recommendation_is_not_attention_or_new_job(self):
        h = Harness()
        h.done()
        with self.assertRaises(ProtocolError):
            h.engine.escalate(h.lineage, "optional", facts="recommendation only", decision="none",
                              recommendation="future adapter", consequence="none", deadline="none",
                              action_required=False, material_risk=False)
        self.assertEqual(len(h.repo.all()), 1)
        self.assertEqual(h.record.row.needs_victor, "No")

    def test_parent_reason_required_and_child_done_never_changes_parent(self):
        h = Harness(custom_brief=brief(parent_id="WP-42", parent_evidence_or_reason="verified ID and ownership evidence"))
        h.done()
        self.assertEqual(h.record.row.parent_workplan_id, "WP-42")
        self.assertEqual(len(h.repo.all()), 1)
        self.assertIn("No parent update", h.record.row.verification)


class AJ0006WrongPathAndApprovedCorrection(unittest.TestCase):
    def test_wrong_path_failure_and_explicitly_approved_corrected_attempt(self):
        # Fixture only: does not read or write AJ-0006's actual prior evidence.
        h = Harness(job_id="AJ-0006")
        h.working()
        original = h.envelope(claimed_class=ReturnClass.BLOCKED,
                              attempted="git operation in /workspace", output="No output yet: wrong repository path",
                              evidence="synthetic fatal: not a git repository", remaining="all code work",
                              blockers="environment/root gate failed", side_effects="No repository changes",
                              recommendation="discover actual root; request corrected attempt approval")
        h.engine.receive(original)
        h.engine.observe_run(h.lineage, h.observation(state="failed"), "corrected attempt review")
        with self.assertRaises(ProtocolError):
            h.engine.retry(h.lineage, authorization("retry", "AJ-0007"), "aj0006-corrected-02",
                           "correct path discovered", gates(), routes(), REQUIRED)
        h.engine.retry(h.lineage, authorization("retry", "AJ-0006"), "aj0006-corrected-02",
                       "explicit approval; failed process confirmed; /workspace/Command-Center-Gravity verified",
                       gates(), routes(), REQUIRED)
        self.assertEqual(h.lineage.attempt, 2)
        self.assertEqual(h.record.attempts[0].return_envelope, original)
        h.dispatch()
        h.start()
        h.engine.receive(h.envelope(attempted="work only in verified repository root"))
        h.engine.complete(h.lineage, h.verification())
        self.assertEqual(h.record.row.status, Status.DONE)
        self.assertEqual(h.executor.calls, 2)


if __name__ == "__main__":
    unittest.main()
