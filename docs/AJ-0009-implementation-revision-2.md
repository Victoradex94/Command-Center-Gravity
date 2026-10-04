# AJ-0009 — ImplementationRevision 2 correction record

Job AJ-0009 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
Nonce VA-SHEETS-0009-01. **ImplementationRevision 2**, separately recorded, does
not change execution lineage or create another job. Bounded ordinary correction
authority: coordinator-supplied Victor Slack `1791108457.730869`.

Repository: `Victoradex94/Command-Center-Gravity`; branch
`aj-0009-sheets-writer-v1`; base/current committed HEAD
`1057b5575f7cecb0da67295b6d0ea9308dc76c9c`. This is an uncommitted candidate.
Root acceptance and explicit continuation remain required before commit/push.
No live API, credentials, permissions, installation, deployment or ledger change.

## Preserved revision-1 history — not accepted

The initial candidate's 109 tests passed, but fresh reviewer
`/root/aj0009_independent_review` found F1, a high-severity permission-persistence
defect through two preflight windows. Acceptance was withheld. The independent
four-test probe suite returned **2 pass, 2 fail, exit 1**. The coordinator accepted
that defect report, not the candidate. Lineage and structure gaps were added as
explicit acceptance corrections in the subsequent instruction.

Preserved artifacts:

* [Complete 12-file IR1 candidate archive](history/AJ-0009-ir1-candidate.tar.gz),
  SHA-256 `b68b76bbd8173e7b49fdcfa0275c1ff2240789ab55de8bf91e71679aa6660c26`.
* [Original per-file content manifest](history/AJ-0009-ir1-manifest.json), SHA-256
  `33800a0a73d5af2568490f49c8c90757bcf5cdaa9bddcd4e6f2db6340205f781`.
* [Independent review summary](history/AJ-0009-ir1-review/review-summary.json),
  [component results](history/AJ-0009-ir1-review/components.json),
  [failing output](history/AJ-0009-ir1-review/review-probes.stderr),
  [exact four probes](history/AJ-0009-ir1-review/test_review_probes.py),
  [exploratory observations](history/AJ-0009-ir1-review/probes.json), and independent
  before/after manifests. The exploratory unknown-cancellation result was **not**
  accepted as a definite defect; Protocol v1.1 distinguishes generic tool labels
  from genuine human withdrawal.
* `AJ-0009-results.json` and `AJ-0009-verification.md` remain unchanged as historical
  IR1 evidence. They must not be read as acceptance of the corrected candidate.

The archive was built only after each source byte hash matched the submitted
manifest. It retains the old interface documentation as well as code/tests; current
interface changes do not rewrite what the first reviewer saw. AJ-0007 stored
acceptance/history and all base core files remain unchanged.

## Bounded corrections

**F1: persistent permission stops.** Every authenticated human denial/revocation
at an authority check or authoritative provider observation is recorded durably,
including the original preflight and recovery's final preflight. The registry
fences both the original reference and overlapping logical job/source identities.
Fresh operation IDs, contexts, callbacks, restarts and handoffs cannot erase it.
Zero-submission permission rejections are persisted as resolved local failures
before returning, so a crash after the stop is saved cannot lose the fence.

An explicit `AuthorityRenewal` interface binds a distinct new authenticated
instruction to the exact target and stop IDs and records root review. Old stops
are retained. Reconciliation, revision/lineage checks, the same incident and
shared one-recovery budget remain mandatory. Renewals cannot reset an open circuit
or clear unknown effects. This is a local interface, not a live permission grant.

**Writer-boundary lineage.** Raw requests now supply explicit expected/intended
`Lineage`. Q must match intended Job ID/SpecRevision/RunEpoch/Attempt exactly, and
the current row must match both expected RecordRevision and expected lineage.
Missing, duplicated, malformed and stale counters are rejected. Actual changes
require authenticated `LineageChange` evidence for the existing clarify/revise/
reopen/retry counter transformations. The repository has an explicit callback for
the lifecycle decision reference; it does not invent or automatically approve a
change. An integration test runs all four existing dispatcher lifecycle actions.

**Mock structural preservation.** The persistent fixture models validation,
formats, row metadata, table/filter/grid bounds and neighbouring values. The
`Submission` contract exposes no structural write fields and `_apply` is limited
to 17 values in an existing A:Q data row. Metadata and neighbours are compared
before/after normal writes, late application, response loss, rejection, partial
effects, cancellation, crash and reconciliation. No real Sheets behavior is claimed.

Journal schema 2 is required for these controls. Schema-1 journal migration is
not implemented: silently retaining a journal whose permission history was not
reliably captured would recreate F1. A future migration requires explicit reviewed
reconciliation. Tests use isolated temporary files; no stored runtime is migrated.

## Permanent regression map

All correction tests are in `tests/test_writer_revision2.py`. Both independently
failing windows were reproduced before correction and incorporated permanently.

| Requirement | Tests |
| --- | --- |
| Initial authenticated denial survives new operation/context/ref/source/job alias and restart/handoff | `test_authenticated_initial_denial_cannot_be_erased_by_fresh_operation_context` |
| Final recovery preflight revocation persists | `test_authenticated_revocation_during_final_recovery_preflight_survives_restart` |
| Other recovery authority-check windows | `test_all_recovery_authority_checks_persist_genuine_stop` |
| Stop survives crash before local rejection return | `test_permission_stop_is_durable_if_process_dies_before_local_rejection_marker` |
| Separate process dies immediately after denial commit; replacement stays fenced | `test_actual_process_death_after_denial_commit_preserves_stop` (required child exit 79) |
| Narrow, explicit, auditable renewal; old ref remains stopped | `test_explicit_reviewed_renewal_is_narrow_audited_and_old_reference_stays_stopped` |
| Malformed, unbound or same-ref renewal rejected | `test_malformed_unbound_or_same_reference_renewal_cannot_clear_stop` |
| A renewed grant can subsequently be revoked | `test_new_denial_of_renewed_reference_is_not_erased_by_old_renewal` |
| Provider denial of a renewed submission fences its actual authority reference and preserves original/effective provenance | `test_provider_denial_after_renewal_fences_effective_reference_and_audits_it` |
| Renewal cannot reset incident budget/circuit or clear unknown effects | `test_human_stop_renewal_retains_same_incident_and_shared_budget`, `test_renewal_never_clears_unknown_effects` |
| Generic tool cancellation remains distinct; independent work can proceed | `test_generic_tool_cancellation_does_not_create_permission_stop`, `test_stop_does_not_block_independently_authorized_unrelated_target` |
| Each stale expected counter at current RecordRevision | `test_raw_writer_rejects_each_stale_expected_counter_at_current_revision` |
| Each regressed or mismatched intended Q counter | `test_raw_writer_rejects_each_regression_and_mismatched_intended_q` |
| Missing/malformed/duplicate counters and wrong Job ID | `test_missing_duplicate_malformed_or_wrong_job_lineage_is_rejected` |
| Exact authorized change and freshness after no-op | `test_existing_lifecycle_changes_require_exact_authenticated_decision`, `test_recovery_rechecks_lineage_and_does_not_replay_over_changed_q` |
| Legitimate clarify/revise/retry/reopen through accepted engine | `test_dispatcher_clarify_revise_retry_and_reopen_use_explicit_lineage_interface` |
| Metadata/neighbours survive create/update/reconciliation | `test_metadata_and_neighbours_preserved_across_create_update_and_reconciliation` |
| Rejection, partial effects, cancellation and crash preserve metadata | `test_metadata_unchanged_after_rejection_partial_and_crash` |
| Values-only API cannot address metadata or expand grid | `test_values_only_submission_cannot_address_metadata_or_expand_grid` |

The existing 58-test suite remains untouched. Existing writer tests are retained;
their request fixture now supplies explicit lineage, and independent human-denial
cases use distinct authority references so one case's newly persistent stop does
not preempt the other case. Original independent probes are also rerun unchanged
against the revised supported fixture/interface.

## Verification and independent recheck

Actual commands/counts/component exits are captured separately in
[IR2 results](AJ-0009-ir2-results.json). The complete suite runs under
`python3 -m tests.offline_suite`; the retained review probes also install the same
offline guard. The original 58 tests, original simulation, compilation, tracked
diff checks, staging-empty checks and whole-candidate preservation checks are run.

Author verification at the IR2 review handoff: **131/131 tests passed** under the
offline guard (58 original + 51 prior-candidate + 22 correction regressions).
The separate original suite passed 58/58, correction module 22/22, and retained
independent probes **4/4** (previously 2/4). The unchanged simulation passed all
11 groups / 58 tests. Each command, compilation, diff check and staging-empty
check exited 0. Required crash-child exits were 77 (application) and 79 (saved
denial); the concurrent claim children exited 0. These are author results to be
independently reproduced, not advance acceptance by the reviewer.

The same reviewer `/root/aj0009_independent_review` will independently recheck the
fixed candidate and reproduce the formerly failing windows and new lineage/
structure tests. Its final disposition belongs in the coordinator return, with
before/after reviewed hashes. If it reports further defects, they are returned
without another silent correction cycle. No reviewer acceptance is claimed here
in advance of that review.

Remaining exclusions: no live adapter, legacy aggregate import, distributed lock,
provider exactly-once/CAS guarantee, physical power-loss proof or production
format/validation guarantee. Mock provider settlement is stronger than Sheets may
expose. Unsupported finality stays UNCERTAIN; the [bounded live-test recommendation](AJ-0009-sheets-writer.md#next-bounded-live-test-recommendation--not-an-assignment)
remains recommendation only. No new job or live test is created.
