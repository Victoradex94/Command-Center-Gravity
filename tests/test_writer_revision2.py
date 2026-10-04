"""ImplementationRevision 2: permanent independent-review regressions and bounds."""

from dataclasses import fields, replace
import multiprocessing
import os
import unittest
from unittest.mock import patch

from dispatcher.mock_sheets import MockAuthority, MockSheets, SimulatedCrash
from dispatcher.model import Lineage, ProtocolError
from dispatcher.sheets_writer import (AuthorityRenewal, CurrentRow, Effect, LineageChange,
                                      Outcome, SheetsWriter, Submission)
from dispatcher.sheets_writer import WriterToken
from dispatcher.writer_journal import WriterJournal
from tests.support import authorization, brief, gates, routes, REQUIRED
import tests.test_sheets_writer as writer_tests
from tests.test_sheets_writer import AUTH, NOW, SCOPE, WriterFixture, request


def with_lineage(req, lineage):
    cells = list(req.cells)
    cells[16] = (f"SpecRevision={lineage.spec_revision}; RunEpoch={lineage.run_epoch}; "
                 f"Attempt={lineage.attempt}; RecordRevision={(req.expected_revision or 0) + 1}")
    return replace(req, cells=tuple(cells), intended_lineage=lineage)


def denial_crash_child(journal_path, provider_path):
    journal = WriterJournal(journal_path, SCOPE)
    authority = MockAuthority()
    writer = SheetsWriter(journal, MockSheets(provider_path, SCOPE), authority, clock=lambda: NOW)
    token = writer.claim("denial-child", AUTH)
    authority.states[AUTH] = "denied"
    save = journal.save
    def exit_after_stop(state):
        save(state)
        if state["permission_stops"]:
            os._exit(79)
    journal.save = exit_after_stop
    writer.write(request(), token)
    os._exit(80)


class PermissionCorrections(WriterFixture):
    def renewal(self, req, reference="synthetic://explicit-renewal"):
        stop_ids = tuple(sorted(self.writer.state()["permission_stops"]))
        renewal = AuthorityRenewal(reference, SCOPE, "Dẹkun", req.job_id, req.source_keys,
                                   stop_ids, True, "LOCAL explicit root review and renewed instruction",
                                   req.original_authority_ref or req.authority_ref, req.intent_digest)
        self.authority.renewals[reference] = renewal
        return renewal

    def test_authenticated_initial_denial_cannot_be_erased_by_fresh_operation_context(self):
        # Exact failing independent-review window, now a permanent regression.
        req = request()
        self.authority.states[AUTH] = "denied"
        self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.FAILED)
        self.authority.states[AUTH] = "valid"  # no new instruction
        self.restart()
        self.reclaim()  # administrative ownership does not renew mutation authority
        for i, variant in enumerate((replace(req, context_ref="new-context"),
                                     replace(req, authority_ref="new-unreviewed-reference"),
                                     replace(req, source_keys=("new-source",)),
                                     request(job="AJ-0010"))):
            with self.subTest(i=i):
                result = self.writer.write(replace(variant, operation_id=f"new-{i}"), self.token)
                self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertEqual(len(self.mock.calls), 0)
        self.assertTrue(self.writer.state()["permission_stops"])

    def test_authenticated_revocation_during_final_recovery_preflight_survives_restart(self):
        # Exact failing independent-review sequence: valid, valid, revoked.
        req = request()
        self.mock.plan("tool-noop")
        self.writer.write(req, self.token)
        inspect, seen = self.authority.inspect, []
        def flipping(reference, scope, actor):
            grant = replace(inspect(reference, scope, actor), state="revoked" if len(seen) == 2 else "valid")
            seen.append(grant.state)
            return grant
        with patch.object(self.authority, "inspect", side_effect=flipping):
            with self.assertRaises(ProtocolError):
                self.writer.recover(req.operation_id, self.change(req), self.token)
        self.assertEqual(seen, ["valid", "valid", "revoked"])
        self.restart()
        self.reclaim()
        with self.assertRaises(ProtocolError):
            self.writer.recover(req.operation_id, self.change(req), self.token)
        self.assertEqual(len(self.mock.calls), 1)
        state = self.writer.state()
        self.assertTrue(state["operations"][req.operation_id]["permission_stop"])
        self.assertTrue(any(s["evidence"].get("grant", {}).get("state") == "revoked"
                            for s in state["permission_stops"].values()))

    def test_all_recovery_authority_checks_persist_genuine_stop(self):
        for window in (0, 1):
            req = request(f"window-{window}", f"AJ-00{20 + window}", source_key=f"source-{window}",
                          authority_ref=f"{AUTH}/{window}")
            self.mock.plan("tool-noop")
            self.writer.write(req, self.token)
            inspect, seen = self.authority.inspect, []
            def flipping(reference, scope, actor):
                grant = replace(inspect(reference, scope, actor), state="human-cancelled" if len(seen) == window else "valid")
                seen.append(grant.state)
                return grant
            change = self.change(req, authority_ref=req.authority_ref)
            with patch.object(self.authority, "inspect", side_effect=flipping):
                with self.assertRaises(ProtocolError):
                    self.writer.recover(req.operation_id, change, self.token)
            with self.assertRaises(ProtocolError):
                self.writer.recover(req.operation_id, change, self.token)
        self.assertEqual(len(self.mock.calls), 2)

    def test_stop_does_not_block_independently_authorized_unrelated_target(self):
        self.authority.states[AUTH] = "denied"
        self.writer.write(request(), self.token)
        unrelated = request("unrelated", "AJ-0030", source_key="independent-source",
                            authority_ref="synthetic://separate-authority")
        self.assertEqual(self.writer.write(unrelated, self.token).outcome, Outcome.SUCCESS)
        same_grant = request("same-grant", "AJ-0031", source_key="other-source")
        self.authority.states[AUTH] = "valid"
        self.assertEqual(self.writer.write(same_grant, self.token).outcome, Outcome.FAILED)

    def test_explicit_reviewed_renewal_is_narrow_audited_and_old_reference_stays_stopped(self):
        req = request()
        self.authority.states[AUTH] = "denied"
        self.writer.write(req, self.token)
        self.authority.states[AUTH] = "valid"
        renewal = self.renewal(req)
        fresh = replace(req, operation_id="renewed-create", authority_ref=renewal.reference,
                        original_authority_ref=req.authority_ref)
        self.assertEqual(self.writer.write(fresh, self.token).outcome, Outcome.FAILED)
        self.writer.review_renewal(renewal.reference, self.token)
        self.restart()
        self.reclaim()
        fresh = replace(fresh, operation_id="after-reviewed-renewal")
        self.assertEqual(self.writer.write(fresh, self.token).outcome, Outcome.SUCCESS)
        self.assertEqual(self.writer.write(replace(req, operation_id="old-reference"), self.token).outcome, Outcome.FAILED)
        audit = self.writer.state()["audit"]
        self.assertTrue(any(e["kind"] == "permission_stop" for e in audit))
        self.assertEqual(sum(e["kind"] == "authority_renewed" for e in audit), 1)
        self.assertEqual(len(self.mock.calls), 1)

    def test_malformed_unbound_or_same_reference_renewal_cannot_clear_stop(self):
        req = request()
        self.authority.states[AUTH] = "denied"
        self.writer.write(req, self.token)
        self.authority.states[AUTH] = "valid"
        good = self.renewal(req)
        for invalid in (replace(good, authenticated=False), replace(good, scope="wrong"),
                        replace(good, actor="worker"), replace(good, job_id="AJ-0099", source_keys=("other",)),
                        replace(good, stop_ids=("unknown-stop",)), replace(good, reference=AUTH),
                        replace(good, evidence="")):
            with self.subTest(invalid=invalid):
                self.authority.renewals[invalid.reference] = invalid
                with self.assertRaises(ProtocolError):
                    self.writer.review_renewal(invalid.reference, self.token)
        self.assertFalse(self.writer.state()["renewals"])
        self.assertFalse(self.mock.calls)

    def test_new_denial_of_renewed_reference_is_not_erased_by_old_renewal(self):
        req = request()
        self.authority.states[AUTH] = "denied"
        self.writer.write(req, self.token)
        renewal = self.renewal(req)
        self.writer.review_renewal(renewal.reference, self.token)
        self.authority.states[renewal.reference] = "revoked"
        renewed = replace(req, operation_id="new-denial", authority_ref=renewal.reference,
                          original_authority_ref=req.authority_ref)
        self.assertEqual(self.writer.write(renewed, self.token).outcome, Outcome.FAILED)
        self.authority.states[renewal.reference] = "valid"
        self.assertEqual(self.writer.write(replace(renewed, operation_id="try-again"), self.token).outcome, Outcome.FAILED)
        with self.assertRaises(ProtocolError):
            self.writer.review_renewal(renewal.reference, self.token)
        self.assertFalse(self.mock.calls)

    def test_human_stop_renewal_retains_same_incident_and_shared_budget(self):
        req = request()
        self.mock.plan("human-noop", "reject")
        self.writer.write(req, self.token)
        renewal = self.renewal(req)
        self.writer.review_renewal(renewal.reference, self.token)
        result = self.writer.recover(req.operation_id, self.change(req, authority_ref=renewal.reference), self.token)
        self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertEqual(result.recovery_used, 1)
        self.assertTrue(result.circuit_open)
        with self.assertRaises(ProtocolError):
            self.writer.recover(req.operation_id, self.change(req, authority_ref=renewal.reference), self.token)
        self.assertEqual(len(self.mock.calls), 2)

    def test_provider_denial_after_renewal_fences_effective_reference_and_audits_it(self):
        req = request()
        self.mock.plan("human-noop", "human-noop")
        self.writer.write(req, self.token)
        renewal = self.renewal(req)
        self.writer.review_renewal(renewal.reference, self.token)
        self.writer.recover(req.operation_id, self.change(req, authority_ref=renewal.reference), self.token)
        self.assertEqual(self.mock.calls[-1]["authority_ref"], renewal.reference)
        state = self.writer.state()
        attempt = [e for e in state["audit"] if e["kind"] == "write_attempted"][-1]
        self.assertEqual(attempt["authority"], renewal.reference)
        self.assertEqual(attempt["original_authority"], AUTH)
        self.assertTrue(any(s["authority_ref"] == renewal.reference for s in state["permission_stops"].values()))
        unrelated = request("reuse-stopped-renewal", "AJ-0088", source_key="unrelated",
                            authority_ref=renewal.reference)
        self.assertEqual(self.writer.write(unrelated, self.token).outcome, Outcome.FAILED)
        self.assertEqual(len(self.mock.calls), 2)

    def test_renewal_never_clears_unknown_effects(self):
        req = request()
        self.mock.plan("tool-pending")
        self.writer.write(req, self.token)
        sub = self.writer._submission(self.writer.state()["operations"][req.operation_id]["submissions"][0])
        observation = replace(self.mock.inspect(sub), cancellation="human", cancellation_authenticated=True)
        with patch.object(self.mock, "inspect", return_value=observation):
            self.assertEqual(self.writer.reconcile(req.operation_id).outcome, Outcome.UNCERTAIN)
            renewal = self.renewal(req)
            self.writer.review_renewal(renewal.reference, self.token)
            with self.assertRaises(ProtocolError):
                self.writer.recover(req.operation_id, self.change(req, authority_ref=renewal.reference), self.token)
        self.assertEqual(len(self.mock.calls), 1)

    def test_permission_stop_is_durable_if_process_dies_before_local_rejection_marker(self):
        self.authority.states[AUTH] = "denied"
        save = self.journal.save
        def crash_after_stop(state):
            save(state)
            if state["permission_stops"]:
                raise SimulatedCrash("after durable denial before return")
        with patch.object(self.journal, "save", side_effect=crash_after_stop):
            with self.assertRaises(SimulatedCrash):
                self.writer.write(request(), self.token)
        self.authority.states[AUTH] = "valid"
        self.restart()
        self.reclaim()
        self.assertEqual(self.writer.write(request("fresh-after-crash"), self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_actual_process_death_after_denial_commit_preserves_stop(self):
        self.writer.retire(self.token, AUTH, "explicit handoff to denial crash fixture")
        child = multiprocessing.get_context("fork").Process(target=denial_crash_child,
                    args=(self.journal_path, self.provider_path))
        child.start()
        child.join(10)
        if child.is_alive():
            child.terminate()
            child.join()
            self.fail("denial crash fixture timed out")
        self.assertEqual(child.exitcode, 79)
        self.restart()
        self.token = WriterToken(**self.writer.state()["owner"])
        self.reclaim()
        self.assertEqual(self.writer.write(request("after-real-crash"), self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_generic_tool_cancellation_does_not_create_permission_stop(self):
        req = request()
        self.mock.plan("tool-noop")
        self.writer.write(req, self.token)
        self.assertFalse(self.writer.state()["permission_stops"])
        self.assertEqual(self.writer.recover(req.operation_id, self.change(req), self.token).outcome, Outcome.SUCCESS)


class LineageCorrections(WriterFixture):
    def test_raw_writer_rejects_each_stale_expected_counter_at_current_revision(self):
        self.writer.write(request(), self.token)
        for field in ("spec_revision", "run_epoch", "attempt"):
            req = request(field, revision=1, expected_lineage=replace(Lineage("AJ-0009", 1, 1, 1), **{field: 2}))
            self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.FAILED)
        self.assertEqual(len(self.mock.calls), 1)

    def test_raw_writer_rejects_each_regression_and_mismatched_intended_q(self):
        before = Lineage("AJ-0009", 3, 4, 5)
        self.writer.write(with_lineage(request(), before), self.token)
        for index, field in enumerate(("spec_revision", "run_epoch", "attempt")):
            after = replace(before, **{field: getattr(before, field) - 1})
            req = with_lineage(request(f"regression-{index}", revision=1, expected_lineage=before), after)
            self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.FAILED)
            mismatched = replace(req, operation_id=f"mismatched-{index}", intended_lineage=before)
            self.assertEqual(self.writer.write(mismatched, self.token).outcome, Outcome.FAILED)
        self.assertEqual(len(self.mock.calls), 1)

    def test_missing_duplicate_malformed_or_wrong_job_lineage_is_rejected(self):
        for i, name in enumerate(("SpecRevision", "RunEpoch", "Attempt")):
            for j, text in enumerate(("", f"{name}=0", f"{name}=1; {name}=1", f"{name}=garbage")):
                req = request(f"bad-{i}-{j}")
                cells = list(req.cells)
                cells[16] = cells[16].replace(f"{name}=1", text)
                self.assertEqual(self.writer.write(replace(req, cells=tuple(cells)), self.token).outcome, Outcome.FAILED)
        for req in (request("missing-intent", intended_lineage=None),
                    request("wrong-job", intended_lineage=Lineage("AJ-9999", 1, 1, 1)),
                    request("missing-expected", revision=1, expected_lineage=None)):
            self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_existing_lifecycle_changes_require_exact_authenticated_decision(self):
        before = Lineage("AJ-0009", 1, 1, 1)
        self.writer.write(request(), self.token)
        after = replace(before, spec_revision=2)
        req = with_lineage(request("clarify", revision=1, lineage_change_ref="synthetic://clarify"), after)
        change = LineageChange(req.lineage_change_ref, SCOPE, "Dẹkun", before, after, "clarify", True, "LOCAL exact clarify decision")
        for i, invalid in enumerate((replace(change, authenticated=False), replace(change, scope="wrong"),
                                     replace(change, before=replace(before, attempt=2)), replace(change, action="retry"))):
            self.authority.lineage_changes[change.reference] = invalid
            self.assertEqual(self.writer.write(replace(req, operation_id=f"bad-decision-{i}"), self.token).outcome, Outcome.FAILED)
        self.authority.lineage_changes[change.reference] = change
        self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.SUCCESS)
        self.assertEqual(self.writer.read(req.job_id).lineage, after)
        self.assertEqual(len(self.mock.calls), 2)

    def test_recovery_rechecks_lineage_and_does_not_replay_over_changed_q(self):
        self.writer.write(request(), self.token)
        req = request("update", revision=1)
        self.mock.plan("tool-noop")
        self.writer.write(req, self.token)
        current = self.writer.read(req.job_id)
        cells = list(current.cells)
        cells[16] = cells[16].replace("RunEpoch=1", "RunEpoch=2")
        self.mock.seed((replace(current, cells=tuple(cells)),))
        with self.assertRaises(ProtocolError):
            self.writer.recover(req.operation_id, self.change(req), self.token)
        self.assertEqual(len(self.mock.calls), 2)


class StructureCorrections(WriterFixture):
    def test_metadata_and_neighbours_preserved_across_create_update_and_reconciliation(self):
        neighbour = request("neighbour", "AJ-0040", source_key="neighbour")
        self.mock.seed((CurrentRow(5, neighbour.cells, neighbour.source_keys),))
        before = self.mock.structure()
        req = request()
        self.mock.plan("tool-pending")
        self.writer.write(req, self.token)
        self.assertEqual(self.mock.structure(), before)
        self.mock.resolve("op-1/0", Effect.APPLIED)
        self.restart()
        self.assertEqual(self.writer.reconcile(req.operation_id).outcome, Outcome.SUCCESS)
        self.reclaim()
        self.mock.plan("apply-timeout")
        self.assertEqual(self.writer.write(request("update", revision=1), self.token).outcome, Outcome.SUCCESS)
        self.assertEqual(self.mock.structure(), before)
        self.assertEqual(self.writer.read(neighbour.job_id).cells, neighbour.cells)
        self.assertEqual([c["position"] for c in self.mock.calls], [6, 6])
        self.assertEqual(len(before["validation"]["E2:E1000"]["values"]), 7)

    def test_metadata_unchanged_after_rejection_partial_and_crash(self):
        before = self.mock.structure()
        for i, mode in enumerate(("reject", "partial", "apply-crash", "human-noop")):
            req = request(f"struct-{i}", f"AJ-00{50+i}", source_key=f"struct-{i}")
            self.mock.plan(mode)
            try:
                self.writer.write(req, self.token)
            except SimulatedCrash:
                self.writer.reconcile(req.operation_id)
            self.assertEqual(self.mock.structure(), before)
        self.assertEqual(len(self.mock.calls), 4)

    def test_values_only_submission_cannot_address_metadata_or_expand_grid(self):
        self.assertFalse({"format", "validation", "structure", "insert_rows"} & {f.name for f in fields(Submission)})
        neighbour = request("last-row", "AJ-0099", source_key="last")
        self.mock.seed((CurrentRow(1000, neighbour.cells, neighbour.source_keys),))
        before = self.mock.structure()
        result = self.writer.write(request(), self.token)
        self.assertEqual(result.outcome, Outcome.UNCERTAIN)
        self.assertEqual(self.mock.structure(), before)
        self.assertEqual(self.writer.read(neighbour.job_id).cells, neighbour.cells)


class LifecycleIntegration(WriterFixture):
    repository = writer_tests.RepositoryIntegrationTests.repository
    harness = writer_tests.RepositoryIntegrationTests.harness

    def test_dispatcher_clarify_revise_retry_and_reopen_use_explicit_lineage_interface(self):
        h = self.harness()
        def approve(before, after):
            action = ("revise" if after.spec_revision > before.spec_revision and after.run_epoch > before.run_epoch
                      else "clarify" if after.spec_revision > before.spec_revision
                      else "reopen" if after.run_epoch > before.run_epoch else "retry")
            ref = f"synthetic://lifecycle/{action}/{after.key}"
            self.authority.lineage_changes[ref] = LineageChange(ref, SCOPE, "Dẹkun", before, after, action, True,
                                                               "LOCAL explicit existing Dispatcher authorization")
            return ref
        h.repo.lineage_change_reference = approve
        h.engine.clarify(h.lineage, authorization("clarify"), brief(inputs="clarified inputs"), "not started")
        h.engine.revise(h.lineage, authorization("revise"), brief(outcome="Revised bounded core"),
                        "VA-IR2-REVISE-01", "no previous run")
        h.review()
        h.engine.retry(h.lineage, authorization("retry"), "VA-IR2-RETRY-01", "previous run completed",
                       gates(), routes(), REQUIRED)
        h.dispatch()
        h.start()
        h.engine.receive(h.envelope(return_id="corrected-result"))
        h.engine.complete(h.lineage, h.verification())
        h.engine.reopen(h.lineage, authorization("reopen"), "VA-IR2-REOPEN-01", "previous effects reconciled")
        self.assertEqual(h.lineage, Lineage(h.job_id, 3, 3, 1))
        changes = [e["change"]["action"] for e in self.writer.state()["audit"] if e["kind"] == "lineage_change_verified"]
        self.assertEqual(changes, ["clarify", "revise", "retry", "reopen"])


if __name__ == "__main__":
    unittest.main()
