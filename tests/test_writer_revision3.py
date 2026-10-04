"""IR3: independent F2 reproduction and exact renewal applicability boundaries."""

from dataclasses import replace
import unittest
from unittest.mock import patch

from dispatcher.model import ProtocolError
from dispatcher.sheets_writer import AuthorityRenewal, Outcome
from tests.test_sheets_writer import AUTH, SCOPE, WriterFixture, request


class RenewalScopeCorrections(WriterFixture):
    def renewal(self, req, reference="synthetic://scoped-renewal", *, review=True):
        attestation = AuthorityRenewal(
            reference, SCOPE, "Dẹkun", req.job_id, req.source_keys,
            tuple(sorted(self.writer.state()["permission_stops"])), True,
            "LOCAL explicit renewed instruction for these exact values and original authority",
            req.original_authority_ref or req.authority_ref, req.intent_digest)
        self.authority.renewals[reference] = attestation
        if review:
            self.writer.review_renewal(reference, self.token)
        return attestation

    def denied_renewal(self, req=None, **kwargs):
        req = req or request()
        self.authority.states[req.authority_ref] = "denied"
        self.assertEqual(self.writer.write(req, self.token).outcome, Outcome.FAILED)
        return req, self.renewal(req, **kwargs)

    @staticmethod
    def renewed(req, renewal, **changes):
        return replace(req, operation_id="renewed-operation", authority_ref=renewal.reference,
                       original_authority_ref=renewal.original_authority_ref, **changes)

    def test_independent_F2_unrelated_renewal_cannot_replace_revoked_original(self):
        # Permanent exact IR2 scenario; only the fixture's new required binding
        # fields differ from the archived independent probe. No guard is mocked.
        original = request("original-job", "AJ-0010", source_key="original-source",
                           authority_ref="review://original-A")
        self.mock.plan("tool-noop")
        self.assertEqual(self.writer.write(original, self.token).outcome, Outcome.FAILED)
        unrelated = request("unrelated-job", "AJ-0020", source_key="unrelated-source",
                            authority_ref="review://unrelated-B")
        _, renewal = self.denied_renewal(unrelated, reference="review://renewal-B-only")
        self.authority.states[original.authority_ref] = "revoked"
        with self.assertRaises(ProtocolError):
            self.writer.recover(original.operation_id, self.change(original, authority_ref=renewal.reference), self.token)
        self.assertEqual(len(self.mock.calls), 1)
        self.assertEqual(self.writer.state()["operations"][original.operation_id]["recovery_used"], 0)
        # A normal recovery still checks the real original; F2 rejection did not
        # create or consume a replacement incident/budget.
        with self.assertRaises(ProtocolError):
            self.writer.recover(original.operation_id, self.change(original), self.token)
        self.assertTrue(any(stop["authority_ref"] == original.authority_ref
                            for stop in self.writer.state()["permission_stops"].values()))

    def test_unrelated_renewal_cannot_replace_still_valid_original_either(self):
        original = request("original", "AJ-0010", source_key="source-A", authority_ref="scope://A")
        self.mock.plan("tool-noop")
        self.writer.write(original, self.token)
        _, renewal = self.denied_renewal(request("other", "AJ-0020", source_key="source-B", authority_ref="scope://B"))
        with self.assertRaises(ProtocolError):
            self.writer.recover(original.operation_id, self.change(original, authority_ref=renewal.reference), self.token)
        self.assertEqual(len(self.mock.calls), 1)
        self.assertEqual(self.writer.recover(original.operation_id,
                         self.change(original, authority_ref=original.authority_ref), self.token).outcome, Outcome.SUCCESS)

    def test_write_blocks_cross_job_source_and_outcome_even_without_target_stop(self):
        req, renewal = self.denied_renewal()
        base = self.renewed(req, renewal)
        other = request("other-job", "AJ-0020", source_key="unrelated-source",
                        authority_ref=renewal.reference, original_authority_ref=req.authority_ref)
        cells = list(base.cells)
        cells[10] = "different deliverable output"
        variants = (other, replace(base, source_keys=("different-source",)),
                    replace(base, cells=tuple(cells)), replace(base, aggregate="different aggregate"),
                    replace(base, original_authority_ref="wrong-original"))
        for i, variant in enumerate(variants):
            with self.subTest(i=i):
                result = self.writer.write(replace(variant, operation_id=f"scope-violation-{i}"), self.token)
                self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_missing_original_relationship_fails_on_fresh_write(self):
        req, renewal = self.denied_renewal()
        result = self.writer.write(replace(req, operation_id="missing-original", authority_ref=renewal.reference), self.token)
        self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_review_rejects_cross_job_and_cross_source_stop_binding(self):
        req, good = self.denied_renewal(review=False)
        for bad in (replace(good, job_id="AJ-0040"), replace(good, source_keys=("other-source",)),
                    replace(good, source_keys=(*good.source_keys, "extra-source"))):
            with self.subTest(bad=bad):
                self.authority.renewals[good.reference] = bad
                with self.assertRaises(ProtocolError):
                    self.writer.review_renewal(good.reference, self.token)
        self.assertFalse(self.writer.state()["renewals"])

    def test_review_rejects_missing_or_unrelated_original_and_malformed_intent(self):
        req, good = self.denied_renewal(review=False)
        for bad in (replace(good, original_authority_ref=""), replace(good, original_authority_ref="unrelated"),
                    replace(good, original_authority_ref=good.reference), replace(good, intent_digest=""),
                    replace(good, intent_digest="caller prose"), replace(good, intent_digest=None)):
            with self.subTest(bad=bad):
                self.authority.renewals[good.reference] = bad
                with self.assertRaises(ProtocolError):
                    self.writer.review_renewal(good.reference, self.token)
        self.assertFalse(self.writer.state()["renewals"])

    def test_authenticated_but_different_intent_renewal_does_not_authorize_recovery(self):
        req = request()
        self.mock.plan("human-noop")
        self.writer.write(req, self.token)
        cells = list(req.cells)
        cells[10] = "another expressly renewed outcome"
        renewal = self.renewal(replace(req, cells=tuple(cells)))
        with self.assertRaises(ProtocolError):
            self.writer.recover(req.operation_id, self.change(req, authority_ref=renewal.reference), self.token)
        self.assertEqual(len(self.mock.calls), 1)

    def test_same_target_renewal_must_match_operations_original_authority(self):
        denied, renewal = self.denied_renewal(request(authority_ref="scope://A"))
        # The intended mutation is identical, but this request asserts another
        # original instruction. Merely matching cells cannot create that relation.
        forged = replace(self.renewed(denied, renewal), original_authority_ref="scope://B")
        self.assertEqual(self.writer.write(forged, self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_unreviewed_renewal_is_not_an_ordinary_grant_for_unrelated_write(self):
        req, renewal = self.denied_renewal(review=False)
        other = request("unreviewed", "AJ-0050", source_key="new-source", authority_ref=renewal.reference)
        self.assertEqual(self.writer.write(other, self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_unreviewed_renewal_cannot_supply_recovery_condition_authority(self):
        original = request("original", "AJ-0010", source_key="source-A", authority_ref="scope://A")
        self.mock.plan("tool-noop")
        self.writer.write(original, self.token)
        _, renewal = self.denied_renewal(request("other", "AJ-0020", source_key="source-B", authority_ref="scope://B"), review=False)
        with self.assertRaises(ProtocolError):
            self.writer.recover(original.operation_id, self.change(original, authority_ref=renewal.reference), self.token)
        self.assertEqual(len(self.mock.calls), 1)

    def test_unknown_grant_kind_and_reclassification_fail_closed(self):
        req, renewal = self.denied_renewal()
        inspect = self.authority.inspect
        for kind in ("ordinary", "unknown"):
            with self.subTest(kind=kind), patch.object(self.authority, "inspect",
                    side_effect=lambda ref, scope, actor: replace(inspect(ref, scope, actor), kind=kind)):
                result = self.writer.write(replace(self.renewed(req, renewal), operation_id=f"changed-kind-{kind}"), self.token)
                self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_ordinary_grant_cannot_invent_a_renewal_relationship(self):
        result = self.writer.write(replace(request(), original_authority_ref="invented-original"), self.token)
        self.assertEqual(result.outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_targeted_renewal_cannot_claim_or_retire_writer(self):
        req, renewal = self.denied_renewal()
        with self.assertRaises(ProtocolError):
            self.writer.retire(self.token, renewal.reference, "not an administrative grant")
        self.writer.retire(self.token, "scope://administrative", "explicit ordinary root handoff")
        with self.assertRaises(ProtocolError):
            self.writer.claim("replacement", renewal.reference)
        self.assertIsNone(self.writer.state()["owner"])

    def test_legitimate_scoped_initial_renewal_survives_restart_with_revoked_original(self):
        req, renewal = self.denied_renewal()
        self.authority.states[AUTH] = "revoked"
        self.restart()
        self.writer.retire(self.token, "scope://administrative", "settled writer retirement")
        self.token = self.writer.claim("fresh-writer", "scope://administrative")
        changed = replace(self.renewed(req, renewal), context_ref="new-context", route="verified-new-route")
        result = self.writer.write(changed, self.token)
        self.assertEqual(result.outcome, Outcome.SUCCESS)
        self.assertEqual(len(self.mock.calls), 1)
        self.assertEqual(self.mock.calls[0]["authority_ref"], renewal.reference)
        self.assertTrue(self.writer.state()["permission_stops"])

    def test_legitimate_scoped_recovery_survives_restart_with_revoked_original(self):
        req = request()
        self.mock.plan("human-noop")
        self.writer.write(req, self.token)
        renewal = self.renewal(req)
        self.authority.states[AUTH] = "revoked"
        self.restart()
        self.writer.retire(self.token, "scope://administrative", "settled writer retirement")
        self.token = self.writer.claim("fresh-writer", "scope://administrative")
        result = self.writer.recover(req.operation_id, self.change(req, authority_ref=renewal.reference), self.token)
        self.assertEqual(result.outcome, Outcome.SUCCESS)
        self.assertEqual(result.recovery_used, 1)
        self.assertEqual(len(self.mock.calls), 2)

    def test_scope_rejection_survives_fresh_context_and_restart(self):
        req, renewal = self.denied_renewal()
        self.restart()
        self.writer.retire(self.token, "scope://administrative", "explicit retirement")
        self.token = self.writer.claim("replacement", "scope://administrative")
        other = request("fresh-context", "AJ-0060", source_key="other-source", authority_ref=renewal.reference,
                        original_authority_ref=req.authority_ref, context_ref="fresh-context")
        self.assertEqual(self.writer.write(other, self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_legacy_unbound_recorded_renewal_is_not_implicitly_upgraded(self):
        req, renewal = self.denied_renewal()
        with self.journal.locked():
            state = self.journal.load()
            del state["renewals"][renewal.reference]["intent_digest"]
            del state["renewals"][renewal.reference]["original_authority_ref"]
            self.journal.save(state)
        self.restart()
        self.writer.retire(self.token, "scope://administrative", "explicit retirement")
        self.token = self.writer.claim("replacement", "scope://administrative")
        self.assertEqual(self.writer.write(self.renewed(req, renewal), self.token).outcome, Outcome.FAILED)
        self.assertFalse(self.mock.calls)

    def test_scoped_renewal_cannot_be_retargeted_by_later_attestation(self):
        req, renewal = self.denied_renewal()
        self.authority.renewals[renewal.reference] = replace(renewal, intent_digest="a" * 64)
        with self.assertRaises(ProtocolError):
            self.writer.review_renewal(renewal.reference, self.token)
        self.assertEqual(self.writer.state()["renewals"][renewal.reference]["intent_digest"], req.intent_digest)

    def test_repository_entry_cannot_turn_targeted_renewal_into_general_write_authority(self):
        from dispatcher.sheets_repository import SheetsRepository
        from tests.support import Harness
        req, renewal = self.denied_renewal(request("denied", "AJ-0090", source_key="renewal-only"))
        # A normal dispatcher aggregate created entirely in the original memory
        # repository supplies an unrelated, otherwise valid repository commit.
        h = Harness()
        record = h.record
        repository = SheetsRepository(self.writer, self.token, authority_ref=renewal.reference,
                    context_ref="LOCAL unrelated repository context", condition="verified-base-context", route="mock-route")
        with self.assertRaises(ProtocolError):
            repository.commit(record, None, record.lineage, self.token.actor)
        self.assertFalse(self.mock.calls)

    def test_renewal_reference_as_lineage_decision_is_still_scope_checked(self):
        from dispatcher.model import Lineage
        from dispatcher.sheets_writer import LineageChange
        original = request("create", "AJ-0010", source_key="source-A", authority_ref="scope://A")
        self.writer.write(original, self.token)
        _, renewal = self.denied_renewal(request("other", "AJ-0020", source_key="source-B", authority_ref="scope://B"))
        before, after = original.intended_lineage, Lineage(original.job_id, 2, 1, 1)
        update = request("clarify", original.job_id, revision=1, source_key="source-A", authority_ref=original.authority_ref,
                         expected_lineage=before, intended_lineage=after, lineage_change_ref=renewal.reference)
        cells = list(update.cells)
        cells[16] = "SpecRevision=2; RunEpoch=1; Attempt=1; RecordRevision=2"
        update = replace(update, cells=tuple(cells))
        self.authority.lineage_changes[renewal.reference] = LineageChange(
            renewal.reference, SCOPE, "Dẹkun", before, after, "clarify", True, "LOCAL lifecycle attestation")
        self.assertEqual(self.writer.write(update, self.token).outcome, Outcome.FAILED)
        self.assertEqual(len(self.mock.calls), 1)

    def test_generic_cancel_recovery_of_scoped_renewed_initial_write(self):
        req, renewal = self.denied_renewal()
        renewed = self.renewed(req, renewal)
        self.mock.plan("tool-noop")
        self.assertEqual(self.writer.write(renewed, self.token).outcome, Outcome.FAILED)
        result = self.writer.recover(renewed.operation_id,
                     self.change(renewed, authority_ref=renewal.reference), self.token)
        self.assertEqual(result.outcome, Outcome.SUCCESS)
        self.assertEqual(result.recovery_used, 1)
        self.assertEqual(len(self.mock.calls), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
