"""AJ-0009: local faults only, including separate-process crash/restart."""

from dataclasses import replace
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dispatcher.engine import Dispatcher
from dispatcher.mock_sheets import MockAuthority, MockSheets, SimulatedCrash
from dispatcher.model import (AGENT_JOB_COLUMNS, AgentJob, Conflict, ProtocolError,
                              ReconciliationRequired, Status, Lineage)
from dispatcher.record_codec import decode_record, encode_record
from dispatcher.sheets_repository import SheetsRepository
from dispatcher.sheets_writer import (CurrentRow, Effect, Outcome, RecoveryChange, SheetsWriter,
                                      WriteRequest, failure_fingerprint)
from dispatcher.writer_journal import WriterJournal
from tests.support import Harness, NOW, brief, source


SCOPE = "LOCAL-FIXTURE/Agent Jobs"
AUTH = "synthetic://owner/AJ-0009"


def request(operation="op-1", job="AJ-0009", revision=None, source_key="source-1", **changes):
    row = AgentJob(job, "", "Local writer fixture", "Codex", Status.INTAKE, "Normal",
                   NOW, NOW, "No dependency", "Synthetic source " + source_key,
                   "", "", "", "No", "Not required", NOW,
                   f"SpecRevision=1; RunEpoch=1; Attempt=1; Nonce=VA-SHEETS-0009-01; RecordRevision={(revision or 0) + 1}")
    return replace(WriteRequest(operation, job, revision, tuple(row.to_cells()), (source_key,),
                                AUTH, "synthetic://context/base", "verified-base-context", "mock-route",
                                expected_lineage=Lineage(job, 1, 1, 1) if revision is not None else None,
                                intended_lineage=Lineage(job, 1, 1, 1)), **changes)


def child_crash(journal_path, provider_path, token, req):
    writer = SheetsWriter(WriterJournal(journal_path, SCOPE), MockSheets(provider_path, SCOPE),
                          MockAuthority(), clock=lambda: NOW)
    try:
        token = writer.claim("crash-process", AUTH)
        writer.write(req, token)
    except SimulatedCrash:
        os._exit(77)
    os._exit(78)


def child_claim(journal_path, provider_path, queue):
    writer = SheetsWriter(WriterJournal(journal_path, SCOPE), MockSheets(provider_path, SCOPE),
                          MockAuthority(), clock=lambda: NOW)
    try:
        writer.claim("second-process", AUTH)
        queue.put("unexpected-claim")
    except ProtocolError:
        queue.put("blocked-existing-owner")


class WriterFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.journal_path = str(Path(self.temp.name) / "journal.sqlite")
        self.provider_path = str(Path(self.temp.name) / "mock.sqlite")
        self.authority = MockAuthority()
        self.restart()
        self.token = self.writer.claim("Dẹkun", AUTH)

    def restart(self):
        self.journal = WriterJournal(self.journal_path, SCOPE)
        self.mock = MockSheets(self.provider_path, SCOPE)
        self.writer = SheetsWriter(self.journal, self.mock, self.authority, clock=lambda: NOW)

    def reclaim(self):
        self.writer.retire(self.token, AUTH, "explicit retirement after restart and reconciliation")
        self.token = self.writer.claim("Dẹkun", AUTH)

    def change(self, req, **kwargs):
        return replace(RecoveryChange("synthetic://verified/change", req.condition,
                                      "verified-provider-condition-resolved", "mock-fallback",
                                      "LOCAL probe of scope, capability, access and route", True,
                                      AUTH, NOW, SCOPE, req.operation_id, req.digest), **kwargs)


class WriterTests(WriterFixture):
    def test_normal_create_update_round_trip(self):
        create = request()
        self.assertEqual(self.writer.write(create, self.token).outcome, Outcome.SUCCESS)
        update = request("op-2", revision=1)
        cells = list(update.cells)
        cells[4], cells[10] = "Ready", "new bounded output"
        update = replace(update, cells=tuple(cells))
        self.assertEqual(self.writer.write(update, self.token).outcome, Outcome.SUCCESS)
        self.assertEqual(self.writer.read(create.job_id).cells, update.cells)
        self.assertEqual(self.writer.read(create.job_id).revision, 2)
        self.assertEqual(len(self.mock.calls), 2)

    def test_exact_17_fields_and_seven_statuses_preserved(self):
        req = request()
        cells = list(req.cells)
        for i in (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15):
            cells[i] = f"distinct {i} ‘é’\n;=literal RAW text"
        req = replace(req, cells=tuple(cells))
        result = self.writer.write(req, self.token)
        self.assertEqual(result.cells, req.cells)
        self.assertEqual(AgentJob.from_cells(list(result.cells)).to_cells(), list(req.cells))
        self.assertEqual(len(AGENT_JOB_COLUMNS), 17)
        self.assertEqual({s.value for s in Status}, {"Intake", "Ready", "Working", "Review", "Blocked", "Done", "Cancelled"})

    def test_duplicate_job_id_create_rejected(self):
        self.writer.write(request(), self.token)
        result = self.writer.write(request("duplicate"), self.token)
        self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertEqual(len(self.mock.calls), 1)

    def test_duplicate_source_on_other_job_rejected(self):
        self.writer.write(request(), self.token)
        result = self.writer.write(request("duplicate-source", "AJ-0010"), self.token)
        self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertEqual(len(self.mock.calls), 1)

    def test_preexisting_duplicate_rows_rejected(self):
        req = request()
        self.mock.seed((CurrentRow(2, req.cells, req.source_keys), CurrentRow(8, req.cells, req.source_keys)))
        self.assertEqual(self.writer.write(request("update", revision=1), self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_stale_revision_and_lost_row_conflict(self):
        self.writer.write(request(), self.token)
        self.writer.write(request("update", revision=1), self.token)
        result = self.writer.write(request("stale", revision=1), self.token)
        self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertEqual(len(self.mock.calls), 2)
        result = self.writer.write(request("missing", "AJ-0011", 1, "new-source"), self.token)
        self.assertEqual(result.outcome, Outcome.FAILED)

    def test_validation_status_values_and_malformed_inputs(self):
        baseline = request()
        invalid_cells = []
        for index, value in ((0, "AJ-9999"), (4, "Paused"), (13, "Maybe"),
                             (10, "x" * 50001), (10, 42),
                             (16, "RecordRevision=1; RecordRevision=garbage"),
                             (16, "RecordRevision=0"), (16, "RecordRevision=2")):
            cells = list(baseline.cells)
            cells[index] = value
            invalid_cells.append(tuple(cells))
        invalid_cells += [baseline.cells[:-1], baseline.cells + ("18th field",)]
        variants = [replace(baseline, cells=c) for c in invalid_cells]
        variants += [replace(baseline, expected_revision=True), replace(baseline, source_keys=()),
                     replace(baseline, source_keys=("dup", "dup")), replace(baseline, context_ref=""),
                     replace(baseline, job_id="bad-id"), replace(baseline, operation_id="bad operation"),
                     replace(baseline, job_id=None), replace(baseline, source_keys=None),
                     replace(baseline, aggregate=42), replace(baseline, cells=None)]
        for i, req in enumerate(variants):
            with self.subTest(i=i):
                if req.operation_id != "bad operation":
                    req = replace(req, operation_id=f"invalid-{i}")
                self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)
        self.assertEqual(self.writer.write(request("valid-after-malformed"), self.token).outcome, Outcome.SUCCESS)

    def test_forbidden_status_transition_is_rejected(self):
        self.writer.write(request(), self.token)
        update = request("update", revision=1)
        cells = list(update.cells)
        cells[4] = "Done"
        self.assertEqual(self.writer.write(replace(update, cells=tuple(cells)), self.token).outcome, Outcome.FAILED)
        self.assertEqual(len(self.mock.calls), 1)

    def test_source_history_cannot_be_removed(self):
        self.writer.write(request(), self.token)
        result = self.writer.write(request("update", revision=1, source_key="different"), self.token)
        self.assertEqual(result.outcome, Outcome.FAILED)

    def test_schema_mismatch_incomplete_and_untrusted_reads_reject_before_submit(self):
        original = self.mock.snapshot(SCOPE)
        for snap in (replace(original, columns=AGENT_JOB_COLUMNS[:-1]),
                     replace(original, complete=False), replace(original, authoritative=False),
                     replace(original, scope="other-table")):
            with self.subTest(snap=snap), patch.object(self.mock, "snapshot", return_value=snap):
                req = request("bad-read-" + str(len(self.writer.state()["operations"])))
                self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_narrow_physical_target_and_unrelated_rows_unchanged(self):
        req = request()
        other = request("other", "AJ-0042", source_key="other")
        self.mock.seed((CurrentRow(10, req.cells, req.source_keys), CurrentRow(11, other.cells, other.source_keys)))
        update = request("update", revision=1)
        self.assertEqual(self.writer.write(update, self.token).outcome, Outcome.SUCCESS)
        self.assertEqual(self.mock.calls[-1]["position"], 10)
        self.assertEqual(self.writer.read("AJ-0042").cells, other.cells)

    def test_timeout_empty_target_is_uncertain_and_new_identity_frozen(self):
        req = request()
        self.mock.plan("tool-pending")
        result = self.writer.write(req, self.token)
        self.assertEqual(result.outcome, Outcome.UNCERTAIN)
        self.assertIsNone(self.writer.read(req.job_id))
        for candidate in (replace(req, operation_id="new-nonce"), request("new-job", "AJ-0010")):
            with self.assertRaises(ReconciliationRequired):
                self.writer.write(candidate, self.token)
        self.assertEqual(len(self.mock.calls), 1)

    def test_late_apply_reconciliation_adopts_without_retry(self):
        req = request()
        self.mock.plan("tool-pending")
        self.writer.write(req, self.token)
        self.mock.resolve("op-1/0", Effect.APPLIED)
        self.assertEqual(self.writer.reconcile(req.operation_id).outcome, Outcome.SUCCESS)
        self.assertEqual(self.writer.recover(req.operation_id, self.change(req), self.token).outcome, Outcome.SUCCESS)
        self.assertEqual(len(self.mock.calls), 1)

    def test_partial_and_unknown_stay_frozen(self):
        for mode in ("partial", "before-crash"):
            with self.subTest(mode=mode):
                req = request(mode, "AJ-" + ("0020" if mode == "partial" else "0021"), source_key=mode)
                self.mock.plan(mode)
                try:
                    result = self.writer.write(req, self.token)
                except SimulatedCrash:
                    result = self.writer.reconcile(req.operation_id)
                self.assertEqual(result.outcome, Outcome.UNCERTAIN)
                with self.assertRaises(ProtocolError):
                    self.writer.recover(req.operation_id, self.change(req), self.token)
        self.assertEqual(len(self.mock.calls), 2)

    def test_crash_after_apply_before_success_marker_restart(self):
        req = request()
        self.mock.plan("apply-crash")
        with self.assertRaises(SimulatedCrash):
            self.writer.write(req, self.token)
        self.assertEqual(self.writer.state()["operations"]["op-1"]["outcome"], Outcome.UNCERTAIN)
        self.restart()
        self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.SUCCESS)
        self.assertEqual(len(self.mock.calls), 1)

    def test_crash_after_intent_before_provider_admission_remains_unknown(self):
        with patch.object(self.mock, "submit", side_effect=SimulatedCrash("before admission")):
            with self.assertRaises(SimulatedCrash):
                self.writer.write(request(), self.token)
        self.restart()
        self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.UNCERTAIN)
        self.assertIsNone(self.writer.read("AJ-0009"))
        self.assertFalse(self.mock.calls)
        with self.assertRaises(ProtocolError):
            self.writer.recover("op-1", self.change(request()), self.token)

    def test_journal_failure_prevents_provider_submission(self):
        with patch.object(self.journal, "save", side_effect=OSError("disk unavailable")):
            with self.assertRaises(OSError):
                self.writer.write(request(), self.token)
        self.assertFalse(self.mock.calls)

    def test_crash_during_recovery_persists_shared_budget(self):
        req = request()
        self.mock.plan("reject", "before-crash")
        self.writer.write(req, self.token)
        with self.assertRaises(SimulatedCrash):
            self.writer.recover("op-1", self.change(req), self.token)
        self.restart()
        result = self.writer.reconcile("op-1")
        self.assertEqual(result.recovery_used, 1)
        self.assertTrue(result.circuit_open)
        self.assertEqual(result.outcome, Outcome.UNCERTAIN)
        with self.assertRaises(ProtocolError):
            self.writer.recover("op-1", self.change(req), self.token)
        self.assertEqual(len(self.mock.calls), 2)

    def test_actual_child_process_death_and_fresh_process_state(self):
        req = request()
        self.mock.plan("apply-crash")
        self.writer.retire(self.token, AUTH, "handoff to child process before fault test")
        ctx = multiprocessing.get_context("fork")
        child = ctx.Process(target=child_crash, args=(self.journal_path, self.provider_path, self.token, req))
        child.start()
        child.join(10)
        if child.is_alive():
            child.terminate()
            child.join()
            self.fail("child did not finish")
        self.assertEqual(child.exitcode, 77)
        self.restart()
        self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.SUCCESS)
        self.assertEqual(len(self.mock.calls), 1)

    def test_restart_and_same_request_never_mutate_again(self):
        req = request()
        self.mock.plan("tool-pending")
        self.writer.write(req, self.token)
        self.restart()
        with self.assertRaises(ProtocolError):
            self.writer.write(req, self.token)
        self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.UNCERTAIN)
        self.assertEqual(len(self.mock.calls), 1)

    def test_human_cancellation_and_permission_denial_block_recovery(self):
        for mode, job in (("human-noop", "AJ-0022"), ("denied-noop", "AJ-0023")):
            with self.subTest(mode=mode):
                req = request(mode, job, source_key=mode, authority_ref=AUTH + "/" + mode)
                self.mock.plan(mode)
                self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.FAILED)
                with self.assertRaises(ProtocolError):
                    self.writer.recover(req.operation_id, self.change(req), self.token)
        self.assertEqual(len(self.mock.calls), 2)

    def test_unverified_human_label_requires_provenance_reconciliation(self):
        req = request()
        self.mock.plan("tool-noop")
        self.writer.write(req, self.token)
        sub = self.writer._submission(self.writer.state()["operations"]["op-1"]["submissions"][0])
        obs = replace(self.mock.inspect(sub), cancellation="human", cancellation_authenticated=False)
        with patch.object(self.mock, "inspect", return_value=obs):
            with self.assertRaises(ProtocolError):
                self.writer.recover("op-1", self.change(req), self.token)
        self.assertFalse(self.writer.state()["operations"]["op-1"]["permission_stop"])
        self.assertEqual(self.writer.recover("op-1", self.change(req), self.token).outcome, Outcome.SUCCESS)

    def test_revoked_authority_is_persisted_and_context_cannot_erase_it(self):
        req = request()
        self.mock.plan("tool-noop")
        self.writer.write(req, self.token)
        self.authority.states[AUTH] = "revoked"
        with self.assertRaises(ProtocolError):
            self.writer.recover("op-1", self.change(req), self.token)
        self.authority.states[AUTH] = "valid"
        self.restart()
        self.reclaim()
        with self.assertRaises(ProtocolError):
            self.writer.recover("op-1", self.change(req), self.token)
        self.assertEqual(len(self.mock.calls), 1)

    def test_unknown_or_unbound_authority_blocks_submission(self):
        self.authority.states[AUTH] = "unknown"
        self.assertEqual(self.writer.write(request(), self.token).outcome, Outcome.FAILED)
        self.authority.states[AUTH] = "valid"
        grant = self.authority.inspect(AUTH, SCOPE, "Dẹkun")
        with patch.object(self.authority, "inspect", return_value=replace(grant, scope="other")):
            self.assertEqual(self.writer.write(request("unbound"), self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_generic_tool_cancellation_noop_can_use_changed_condition_recovery(self):
        req = request()
        self.mock.plan("tool-noop")
        self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.FAILED)
        result = self.writer.recover("op-1", self.change(req), self.token)
        self.assertEqual(result.outcome, Outcome.SUCCESS)
        self.assertEqual(result.recovery_used, 1)
        self.assertEqual(len(self.mock.calls), 2)

    def test_generic_cancel_pending_requires_settlement_not_empty_row(self):
        req = request()
        self.mock.plan("tool-pending")
        self.writer.write(req, self.token)
        with self.assertRaises(ProtocolError):
            self.writer.recover("op-1", self.change(req), self.token)
        self.mock.resolve("op-1/0", Effect.NOOP)
        self.assertEqual(self.writer.recover("op-1", self.change(req), self.token).outcome, Outcome.SUCCESS)

    def test_false_failure_after_original_success_does_not_retry(self):
        req = request()
        self.mock.plan("apply-timeout")
        result = self.writer.write(req, self.token)
        self.assertEqual(result.outcome, Outcome.SUCCESS)
        self.assertEqual(self.writer.recover("op-1", self.change(req), self.token).recovery_used, 0)
        self.assertEqual(len(self.mock.calls), 1)

    def test_exact_readback_mismatch_never_reports_success(self):
        req = request()
        real_snapshot = self.mock.snapshot
        def wrong_read(scope):
            snap = real_snapshot(scope)
            if not snap.rows:
                return snap
            cells = list(snap.rows[0].cells)
            cells[15] = "wrong Last Update"
            return replace(snap, rows=(replace(snap.rows[0], cells=tuple(cells)),))
        with patch.object(self.mock, "snapshot", side_effect=wrong_read):
            self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.UNCERTAIN)
        self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.SUCCESS)

    def test_forged_or_stale_provider_evidence_stays_uncertain(self):
        req = request()
        self.mock.plan("tool-pending")
        self.writer.write(req, self.token)
        sub = self.writer._submission(self.writer.state()["operations"]["op-1"]["submissions"][0])
        obs = self.mock.inspect(sub)
        for bad in (replace(obs, attempt_id="other", effect=Effect.NOOP, settled=True, effects_resolved=True),
                    replace(obs, digest="wrong"), replace(obs, authoritative=False), replace(obs, scope="other")):
            with patch.object(self.mock, "inspect", return_value=bad):
                self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.UNCERTAIN)
        self.assertEqual(len(self.mock.calls), 1)

    def test_retirement_fresh_handoff_and_stale_token_fence(self):
        with self.assertRaises(ProtocolError):
            self.writer.claim("proxy", AUTH)
        self.writer.retire(self.token, AUTH, "explicit retirement; prior writer stopped")
        new = self.writer.claim("proxy", AUTH)
        with self.assertRaises(ProtocolError):
            self.writer.write(request(), self.token)
        self.assertEqual(self.writer.write(request(), new).outcome, Outcome.SUCCESS)
        kinds = [a["kind"] for a in self.writer.state()["audit"]]
        self.assertEqual(kinds[:3], ["writer_claimed", "writer_retired", "writer_claimed"])

    def test_replacement_instance_requires_retirement_even_with_copied_token(self):
        self.writer.write(request(), self.token)
        original, token = self.writer, self.token
        self.restart()
        with self.assertRaises(ProtocolError):
            self.writer.write(request("update", revision=1), token)
        self.reclaim()
        with self.assertRaises(ProtocolError):
            original.write(request("update", revision=1), token)
        self.assertEqual(self.writer.write(request("update", revision=1), self.token).outcome, Outcome.SUCCESS)

    def test_unsettled_write_blocks_retirement_even_after_restart(self):
        self.mock.plan("tool-pending")
        self.writer.write(request(), self.token)
        self.restart()
        with self.assertRaises(ProtocolError):
            self.writer.retire(self.token, AUTH, "try fresh writer")
        with self.assertRaises(ProtocolError):
            self.writer.claim("replacement", AUTH)

    def test_same_journal_second_process_cannot_claim_active_owner(self):
        ctx = multiprocessing.get_context("fork")
        queue = ctx.Queue()
        child = ctx.Process(target=child_claim, args=(self.journal_path, self.provider_path, queue))
        child.start()
        child.join(10)
        if child.is_alive():
            child.terminate()
            child.join()
            self.fail("claim child timed out")
        self.assertEqual(child.exitcode, 0)
        self.assertEqual(queue.get(timeout=2), "blocked-existing-owner")
        queue.close()

    def test_handoff_does_not_reset_shared_budget(self):
        req = request()
        self.mock.plan("reject", "reject")
        self.writer.write(req, self.token)
        self.writer.retire(self.token, AUTH, "settled original retired")
        token = self.writer.claim("fresh-proxy", AUTH)
        result = self.writer.recover("op-1", self.change(req), token)
        self.assertEqual(result.recovery_used, 1)
        self.assertTrue(result.circuit_open)
        self.writer.retire(token, AUTH, "settled fallback retired")
        newest = self.writer.claim("third-context", AUTH)
        with self.assertRaises(ProtocolError):
            self.writer.recover("op-1", self.change(req, route="another-route"), newest)
        self.assertEqual(len(self.mock.calls), 2)

    def test_fallback_shares_budget_and_same_fingerprint_trips_circuit(self):
        req = request()
        self.mock.plan("tool-noop", "tool-noop")
        first = self.writer.write(req, self.token)
        result = self.writer.recover("op-1", self.change(req), self.token)
        self.assertEqual(first.fingerprint, result.fingerprint)
        self.assertTrue(result.circuit_open)
        self.assertEqual(result.recovery_used, 1)
        self.writer.reconcile("op-1")
        self.restart()
        self.reclaim()
        with self.assertRaises(ProtocolError):
            self.writer.recover("op-1", self.change(req, route="third-route"), self.token)
        op = self.writer.state()["operations"]["op-1"]
        self.assertEqual(op["recurrence_count"], 1)
        self.assertEqual(len(op["failure_occurrences"]), 2)
        self.assertEqual(len(self.mock.calls), 2)
        self.assertEqual(sum(e["kind"] == "circuit_open" for e in self.writer.state()["audit"]), 1)

    def test_uncertain_recovery_opens_circuit_and_late_success_closes_without_replay(self):
        req = request()
        self.mock.plan("reject", "tool-pending")
        self.writer.write(req, self.token)
        result = self.writer.recover("op-1", self.change(req), self.token)
        self.assertEqual(result.outcome, Outcome.UNCERTAIN)
        self.assertTrue(result.circuit_open)
        self.mock.resolve("op-1/1", Effect.APPLIED)
        self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.SUCCESS)
        self.assertEqual(len(self.mock.calls), 2)

    def test_stale_unverified_or_unchanged_recovery_evidence_rejected(self):
        req = request()
        self.mock.plan("reject")
        self.writer.write(req, self.token)
        for change in (self.change(req, verified=False), self.change(req, to_condition=req.condition),
                       self.change(req, checked_at="2026-10-04T05:00:00+00:00"),
                       self.change(req, checked_at="2026-10-04T07:00:00+00:00"),
                       self.change(req, scope="different"), self.change(req, digest="wrong"),
                       self.change(req, operation_id="other"), self.change(req, evidence="")):
            with self.subTest(change=change), self.assertRaises(ProtocolError):
                self.writer.recover("op-1", change, self.token)
        self.assertEqual(len(self.mock.calls), 1)
        self.assertEqual(self.writer.state()["operations"]["op-1"]["recovery_used"], 0)

    def test_failure_fingerprint_ignores_occurrence_and_preserves_safety_scope(self):
        args = (SCOPE, "verified-base-context", "state-ledger", "cancelled-call", "write-effects-unresolved")
        self.assertEqual(failure_fingerprint(*args), failure_fingerprint(*args))
        self.assertNotEqual(failure_fingerprint(*args), failure_fingerprint("other-workbook", *args[1:]))
        req = request()
        second = request("different-occurrence", "AJ-0010", source_key="second-source")
        self.mock.plan("tool-noop", "tool-noop")
        self.assertEqual(self.writer.write(req, self.token).fingerprint,
                         self.writer.write(second, self.token).fingerprint)

    def test_identity_reuse_changed_intent_is_conflict(self):
        req = request()
        self.writer.write(req, self.token)
        with self.assertRaises(Conflict):
            self.writer.write(replace(req, context_ref="different"), self.token)
        self.assertEqual(len(self.mock.calls), 1)

    def test_new_route_identity_after_exhausted_budget_stays_frozen(self):
        req = request()
        self.mock.plan("reject", "reject")
        self.writer.write(req, self.token)
        self.writer.recover("op-1", self.change(req), self.token)
        with self.assertRaises(ReconciliationRequired):
            self.writer.write(replace(req, operation_id="fresh-id", route="new-route"), self.token)
        self.assertEqual(len(self.mock.calls), 2)

    def test_audit_contains_exact_attempt_reconciliation_and_verified_outcome(self):
        req = request()
        self.writer.write(req, self.token)
        self.restart()
        audit = self.writer.state()["audit"]
        attempt = next(e for e in audit if e["kind"] == "write_attempted")
        reconciliation = next(e for e in audit if e["kind"] == "authoritative_reconciliation")
        self.assertEqual(tuple(attempt["submission"]["cells"]), req.cells)
        self.assertEqual(tuple(reconciliation["snapshot"]["rows"][0]["cells"]), req.cells)
        self.assertEqual(audit[-1]["outcome"], Outcome.SUCCESS)
        self.assertEqual(audit[-1]["kind"], "verified_outcome")

    def test_independent_job_can_proceed_while_affected_branch_frozen(self):
        self.mock.plan("tool-pending")
        self.writer.write(request(), self.token)
        independent = request("independent", "AJ-0040", source_key="independent")
        self.assertEqual(self.writer.write(independent, self.token).outcome, Outcome.SUCCESS)
        self.assertEqual([s["position"] for s in self.mock.calls], [2, 3])
        self.mock.resolve("op-1/0", Effect.APPLIED)
        self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.SUCCESS)
        self.assertEqual(self.writer.read(independent.job_id).cells, independent.cells)

    def test_noop_observation_with_changed_target_is_not_resolved_failure(self):
        req = request()
        self.mock.plan("tool-pending")
        self.writer.write(req, self.token)
        self.mock.resolve("op-1/0", Effect.NOOP)
        changed = request("alien")
        self.mock.seed((CurrentRow(2, changed.cells, changed.source_keys),))
        self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.UNCERTAIN)

    def test_read_failure_after_apply_stays_frozen_until_authoritative_read(self):
        real = self.mock.snapshot
        def fail_after_submit(scope):
            if self.mock.calls:
                raise TimeoutError("mock read unavailable")
            return real(scope)
        with patch.object(self.mock, "snapshot", side_effect=fail_after_submit):
            self.assertEqual(self.writer.write(request(), self.token).outcome, Outcome.UNCERTAIN)
        self.assertEqual(self.writer.reconcile("op-1").outcome, Outcome.SUCCESS)
        self.assertEqual(len(self.mock.calls), 1)


class RepositoryIntegrationTests(WriterFixture):
    def repository(self):
        return SheetsRepository(self.writer, self.token, authority_ref=AUTH,
                                context_ref="synthetic://context/base", condition="verified-base-context", route="mock-route")

    def harness(self):
        h = Harness()
        h.repo = self.repository()
        h.engine = Dispatcher(h.repo, clock=lambda: h.now)
        h.engine.intake(h.job_id, "VA-DISPATCHER-0007-01", source(), brief())
        return h

    def test_dispatcher_full_lifecycle_and_codec_survive_restart(self):
        h = self.harness()
        record = h.done()
        self.assertEqual(record.row.status, Status.DONE)
        self.assertEqual(decode_record(encode_record(record)), record)
        self.restart()
        self.assertEqual(self.repository().read(h.job_id), record)
        self.assertTrue(record.attempts)
        self.assertTrue(record.deliveries)
        self.assertIsNotNone(record.verification)

    def test_dispatcher_uncertain_reservation_never_calls_executor(self):
        h = self.harness()
        h.ready()
        self.mock.plan("apply-crash")
        with self.assertRaises(SimulatedCrash):
            h.dispatch()
        self.assertEqual(len(h.executor.requests), 0)
        self.restart()
        h.repo = self.repository()
        h.engine = Dispatcher(h.repo, clock=lambda: NOW)
        record = h.repo.reconcile(h.job_id, "Dẹkun")
        self.assertIsNotNone(record.current_attempt)
        self.reclaim()
        h.repo = self.repository()
        h.engine = Dispatcher(h.repo, clock=lambda: NOW)
        h.dispatch()
        self.assertEqual(len(h.executor.requests), 0)

    def test_repository_rejects_stale_lineage_and_external_aggregate_mismatch(self):
        h = self.harness()
        before = h.record
        h.ready()
        with self.assertRaises(Conflict):
            h.repo.commit(before, before.version, before.lineage, "Dẹkun")
        row = self.writer.read(h.job_id)
        cells = list(row.cells)
        cells[10] = "out-of-band edit"
        self.mock.seed((replace(row, cells=tuple(cells)),))
        with self.assertRaises(ReconciliationRequired):
            h.repo.read(h.job_id)

    def test_repository_checks_aggregate_identity_before_mutation_and_source_on_read(self):
        h = self.harness()
        record = h.record
        record.lineage = replace(record.lineage, job_id="AJ-9999")
        calls = len(self.mock.calls)
        with self.assertRaises(ProtocolError):
            h.repo.commit(record, record.version, h.lineage, "Dẹkun")
        self.assertEqual(len(self.mock.calls), calls)
        row = self.writer.read(h.job_id)
        self.mock.seed((replace(row, source_keys=("foreign-source",)),))
        with self.assertRaises(ReconciliationRequired):
            h.repo.read(h.job_id)

    def test_codec_unknown_type_rejected_without_dynamic_import(self):
        data = {"version": 1, "record": {"type": "arbitrary.module", "fields": {}}}
        with self.assertRaises(ProtocolError):
            decode_record(json.dumps(data))
