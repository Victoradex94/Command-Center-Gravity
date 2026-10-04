# AJ-0009 — ImplementationRevision 3 correction record

Job AJ-0009 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
Nonce VA-SHEETS-0009-01. **ImplementationRevision 3** is a code-review correction,
not a new execution attempt or a recovery submission. Coordinator authority:
one ordinary F2 correction under Victor's existing Slack `1791108457.730869`.
The writer's one-recovery incident budget and circuit limits are unchanged.

Repository `Victoradex94/Command-Center-Gravity`, branch
`aj-0009-sheets-writer-v1`, base/current committed HEAD
`1057b5575f7cecb0da67295b6d0ea9308dc76c9c`. Candidate remains uncommitted and
unstaged, pending the same independent reviewer and root acceptance. Commit/push
needs explicit continuation. No live API, credentials, permissions, main changes,
installation, deployment, ledger/Slack writes or follow-on job are included.

## Preserved failed history

IR1 passed its author suite but failed two independent F1 permission-persistence
probes. IR2 corrected F1 and passed 131 tests and all four unchanged IR1 probes,
but **failed independent review** on High F2: an AJ-0020-only renewal could replace
revoked original AJ-0010 authority during recovery because the scope gate returned
early without a matching local stop. The independent F2 probe observed SUCCESS
and two provider submissions instead of one; its assertion failed, exit 1.
Neither candidate was accepted.

The complete [24-file IR2 archive](history/AJ-0009-ir2-candidate.tar.gz) was made
only after all bytes matched its [submitted manifest](history/AJ-0009-ir2-manifest.json),
SHA-256 `7989f4379efad0acc34c470f5b48ce5d4e61a59d9de4cbe3682523167d5969b6`.
The archive includes the already preserved IR1 archive and review history.
The exact [IR2 independent summary](history/AJ-0009-ir2-review/review-summary.json),
[components](history/AJ-0009-ir2-review/components.json), before/after manifests,
[original F2 probe](history/AJ-0009-ir2-review/test_renewal_scope.py) and failing
stdout/stderr are retained unchanged. IR1/IR2 result and correction documents
remain historical evidence, not statements of current acceptance.

## Correction and trust boundary

Every mutation-related authority check now validates renewal applicability even
if there is no matching local stop. A reviewed immutable `AuthorityRenewal` binds
the configured scope/root, exact logical job and source set, original stopped
authority reference and a deterministic digest of the exact intended mutation.
The intent digest includes all 17 cells, expected revision, source tuple, aggregate
snapshot, expected/intended lineage and lineage-decision reference. It excludes
occurrence, route, context and authority labels; changing those does not widen the
granted outcome. The full operation identity/digest stays distinct and immutable.

The authority reader explicitly classifies grants as ordinary or renewal.
Unreviewed renewals, unknown kinds and reclassification of stored renewals fail
closed. Review verifies the original-authority relationship against the enumerated
stops, and requires both job and exact sources to match targeted stops. Recovery
checks applicability before selecting a replacement authority, then uses the
same scoped gates for its authority checks and final preflight. Fresh initial
requests using a renewal also name the bound original authority. Targeted renewal
grants cannot authorize claim/retirement administration. Repository commits and
lineage-decision references pass through the same mutation checks.

This is a **trusted adapter attestation boundary**, not cryptographic permission
verification. A future adapter must authenticate actual instructions, classify
renewals correctly, bind the approved values/authority relationship, and report
current revocation. A caller string, digest or boolean is not independent proof.
The local MockAuthority deliberately supplies synthetic grants; its default-valid
fixture behavior is not suitable for live authentication. An incorrect trusted
adapter remains outside this local guarantee. No live adapter is added.

Legitimate exact-scope renewal can still permit the intended mutation after genuine
revocation, including restart and fresh exclusive handoff. Generic tool cancellation
with still-valid ordinary authority retains its existing reconciliation and one
changed-condition recovery path. Scope rejection does not consume or reset the
provider recovery budget. Renewal never clears unknown effects, open circuits or
previously consumed recovery. F1 persistence, lineage checks and structural mocks
are preserved. Older stored renewal records lacking the new bindings fail closed;
no implicit upgrade or journal migration is provided.

## Requirement-to-test map

Existing baseline requirements remain mapped in
[original verification](AJ-0009-verification.md) and
[IR2 correction verification](AJ-0009-implementation-revision-2.md).
The new permanent tests are in `tests/test_writer_revision3.py`, class
`RenewalScopeCorrections`:

| Correction requirement / boundary | Exact test suffix after `test_` |
| --- | --- |
| Independent F2, revoked original, no target stop | `independent_F2_unrelated_renewal_cannot_replace_revoked_original` |
| Invalid renewal cannot replace valid original either; valid recovery still works | `unrelated_renewal_cannot_replace_still_valid_original_either` |
| Create/write: cross-job/source/outcome/aggregate mismatch | `write_blocks_cross_job_source_and_outcome_even_without_target_stop` |
| Fresh request must name original relationship | `missing_original_relationship_fails_on_fresh_write` |
| Review cannot broaden by matching only job or source | `review_rejects_cross_job_and_cross_source_stop_binding` |
| Missing/mismatched original reference and malformed intent | `review_rejects_missing_or_unrelated_original_and_malformed_intent` |
| Recovery cannot consume another expressly approved outcome | `authenticated_but_different_intent_renewal_does_not_authorize_recovery` |
| Exact values alone cannot fabricate original authority | `same_target_renewal_must_match_operations_original_authority` |
| Unreviewed grant cannot become ordinary write permission | `unreviewed_renewal_is_not_an_ordinary_grant_for_unrelated_write` |
| Unreviewed recovery-condition authority | `unreviewed_renewal_cannot_supply_recovery_condition_authority` |
| Unknown kind / downgrade and invented relationship | `unknown_grant_kind_and_reclassification_fail_closed`; `ordinary_grant_cannot_invent_a_renewal_relationship` |
| Claim and retirement cannot use targeted grant | `targeted_renewal_cannot_claim_or_retire_writer` |
| Legitimate scoped new request after revoke/restart/handoff | `legitimate_scoped_initial_renewal_survives_restart_with_revoked_original` |
| Legitimate scoped recovery after revoke/restart/handoff | `legitimate_scoped_recovery_survives_restart_with_revoked_original` |
| Scope still enforced across replacement instances | `scope_rejection_survives_fresh_context_and_restart` |
| No implicit legacy renewal upgrade | `legacy_unbound_recorded_renewal_is_not_implicitly_upgraded` |
| Reviewed renewal immutable | `scoped_renewal_cannot_be_retargeted_by_later_attestation` |
| Dispatcher repository boundary | `repository_entry_cannot_turn_targeted_renewal_into_general_write_authority` |
| Lineage-decision authority boundary | `renewal_reference_as_lineage_decision_is_still_scope_checked` |
| Generic cancellation on an already-renewed initial request | `generic_cancel_recovery_of_scoped_renewed_initial_write` |

`tests/probe_writer_f2.py` also preserves the independent scenario and exact
provider-call assertion as a standalone offline probe. Only portable import-path
setup and the fixture's now-required original-authority/intent fields were added;
the old probe bytes and failed observations remain archived. It reports blocked
with one provider call. The permanent regression additionally checks unchanged
budget and verifies that subsequent ordinary recovery observes original revocation.

## Author verification and review disposition

Actual machine-readable command results are in
[AJ-0009-ir3-results.json](AJ-0009-ir3-results.json), with separate exit codes and
stdout/stderr hashes. Final commands and expected successful counts:

| Command | Author result |
| --- | --- |
| `python3 -m tests.offline_suite` | 152 passed / 0 failures / 0 errors, exit 0 |
| `python3 -m unittest tests.test_protocol tests.test_review_regressions -q` | Original 58 passed, exit 0 |
| `python3 -m unittest tests.test_writer_revision2 -q` | Prior 22 corrections passed, exit 0 |
| `python3 -m unittest tests.test_writer_revision3 -q` | New 21 corrections passed, exit 0 |
| `python3 docs/history/AJ-0009-ir1-review/test_review_probes.py` | Unchanged four F1/ownership/lineage probes passed, exit 0 |
| `python3 tests/probe_writer_f2.py` | F2 adapted fixture: one passed, exit 0 |
| `python3 -m tests.simulate` | 11 groups / 58 tests passed, exit 0 |
| `python3 -m compileall -q dispatcher tests` | Exit 0 |
| `git diff --check` | Exit 0; untracked text separately checked |
| `git diff --cached --exit-code` | Exit 0; empty staging |

Counts overlap. The full suite contains original 58 + prior candidate 51 + IR2
22 + IR3 21. The actual crash-child exits remain 77 (provider apply) and 79 (denial
commit); the ownership process and both simultaneous claim children exit 0.
These expected component exits are asserted by the tests, not hidden by outer
success. The test guard blocks network and external executable launches and is
inherited by forked children. The tests use only local SQLite fixtures.

The same independent reviewer `/root/aj0009_independent_review` must recheck the
frozen manifest and adversarial scope cases. This document records author evidence
before review and does not assert reviewer acceptance. Any additional blocker must
be returned without another correction loop. The final handoff carries the reviewed
manifest and disposition; no post-review source changes are intended.

## Remaining limits and bounded recommendation

The exact 17-column/seven-status contract and original core remain unchanged.
No production connector was called. Same-host advisory exclusion is not a
distributed provider lock, and mock settlement is stronger than Sheets may expose.
There is no provider exactly-once/CAS, physical power-loss guarantee, legacy
aggregate import or live formatting/validation proof. Unknown settlement stays
UNCERTAIN and freezes mutation.

The [bounded future live-test recommendation](AJ-0009-sheets-writer.md#next-bounded-live-test-recommendation--not-an-assignment)
remains separately gated on acceptance, preservation and adapter implementation:
one synthetic create and one update in an explicitly approved non-production range,
exact value/metadata/neighbour readback, then restart reconciliation with zero
additional mutation. It is not an assignment or authorization to make a live call.
