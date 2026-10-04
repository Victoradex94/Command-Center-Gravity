# AJ-0009 requirement-to-test map and candidate review

Lineage: AJ-0009 / SpecRevision=1 / RunEpoch=1 / Attempt=1 /
Nonce=VA-SHEETS-0009-01. Uncommitted candidate; Dẹkun acceptance and explicit
continuation are required before commit/push. These results do not modify the
AJ-0007 acceptance/history or establish any live-service guarantee.

## Actual local execution

Python 3.12.14; standard library only; no installs. Repository identity and
starting branch were inspected before edits. The clean initial checkout was
`work` at `dea8cddc0bb6e7ab20479d8aca25121590749a3b`; the required base was not
present. Authorized `git ls-remote` found the preserved branch at
`1057b5575f7cecb0da67295b6d0ea9308dc76c9c` and no AJ-0009 branch. `git fetch`
retrieved that branch, then `git switch -c aj-0009-sheets-writer-v1 <exact SHA>`
created the new implementation branch. Each of those component commands exited 0.
Initial `git cat-file` exited 128 because the object was absent before fetch;
it was not counted as a passing baseline. No relevant AGENTS.md/SKILL.md was found
in the checkout or available workspace `.agents` directory.

The original suite passed **58/58** before implementation. The final component
commands, exact counts, exits, output hashes and unchanged-base-file check are
recorded in [AJ-0009-results.json](AJ-0009-results.json). Run from repository root:

```sh
python3 -m tests.offline_suite
python3 -m tests.simulate
python3 -m compileall -q dispatcher tests
git diff --check
```

Final run: **109 passed, 0 failed, 0 errors** (58 original + 51 new), guarded
runner exit **0**. The separate original-suite check passed 58/58, exit 0. The
unchanged simulation passed all **11 groups / 58 tests**, exit 0. Compileall,
tracked diff check and staged-empty check each exited 0. The guarded runner took
1.378 seconds internally. All 14 base-tracked files other than the intentionally
extended README matched the approved commit byte-for-byte.

`offline_suite` runs ordinary unittest discovery with a process-wide audit hook
that blocks network/DNS/HTTP events and subprocess/exec launches. Forked crash
fixtures inherit the hook. A synthetic audit event proves the hook is active
without making a socket or connector call. Static import checks additionally
constrain dispatcher modules to local modules and listed nonnetwork stdlib
imports. This is repository-specific test evidence, not a hostile-code sandbox.

## Required automated cases

All names below are in `tests/test_sheets_writer.py` under `WriterTests` unless
qualified. Cells, sources, references, authority and provider responses are synthetic.

| Requirement | Automated test(s) |
| --- | --- |
| Normal create/update round-trip | `test_normal_create_update_round_trip` |
| Exactly 17 fields, original seven statuses | `test_exact_17_fields_and_seven_statuses_preserved`; original schema test retained |
| Duplicate logical ID/source, including corrupt preexisting duplicate rows | `test_duplicate_job_id_create_rejected`, `test_duplicate_source_on_other_job_rejected`, `test_preexisting_duplicate_rows_rejected` |
| Current row/revision and stale conflict | `test_stale_revision_and_lost_row_conflict`; integration stale lineage test |
| Allowed values/status and malformed inputs | `test_validation_status_values_and_malformed_inputs`, `test_forbidden_status_transition_is_rejected`, `test_schema_mismatch_incomplete_and_untrusted_reads_reject_before_submit`, `test_source_history_cannot_be_removed` |
| Cancellation/uncertainty freezes duplicates | `test_timeout_empty_target_is_uncertain_and_new_identity_frozen`, `test_restart_and_same_request_never_mutate_again` |
| Late applied write found by reconciliation | `test_late_apply_reconciliation_adopts_without_retry` |
| Partial/unknown remains frozen | `test_partial_and_unknown_stay_frozen`, `test_noop_observation_with_changed_target_is_not_resolved_failure` |
| Crash after application before local success | `test_crash_after_apply_before_success_marker_restart`, `test_actual_child_process_death_and_fresh_process_state` |
| Restart without duplicate mutation | Prior two tests plus `test_restart_and_same_request_never_mutate_again` and integration reservation crash test |
| Human cancellation/revocation/denial blocks recovery | `test_human_cancellation_and_permission_denial_block_recovery`, `test_revoked_authority_is_persisted_and_context_cannot_erase_it`, `test_unknown_or_unbound_authority_blocks_submission` |
| Generic tool cancellation + valid authority + settled no-op permits one verified change | `test_generic_tool_cancellation_noop_can_use_changed_condition_recovery`, `test_generic_cancel_pending_requires_settlement_not_empty_row`, `test_unverified_human_label_requires_provenance_reconciliation` |
| Writer retirement/fresh exclusive handoff | `test_retirement_fresh_handoff_and_stale_token_fence`, `test_replacement_instance_requires_retirement_even_with_copied_token`, `test_unsettled_write_blocks_retirement_even_after_restart`, `test_same_journal_second_process_cannot_claim_active_owner` |
| Fallback shares recovery budget | `test_fallback_shares_budget_and_same_fingerprint_trips_circuit`, `test_handoff_does_not_reset_shared_budget`, `test_crash_during_recovery_persists_shared_budget` |
| Same fingerprint recurrence trips circuit, callback/read dedup | `test_fallback_shares_budget_and_same_fingerprint_trips_circuit`, `test_failure_fingerprint_ignores_occurrence_and_preserves_safety_scope`, `test_new_route_identity_after_exhausted_budget_stays_frozen` |
| False-positive failure: original actually succeeded | `test_false_failure_after_original_success_does_not_retry` |
| No production/live connector called by suite | `tests.offline_suite` active audit guard; `tests/test_offline_boundary.py` import and guard tests; no production adapter exists |

## Interface, audit and failure-window additions

| Design requirement/window | Automated evidence |
| --- | --- |
| Deterministic identity cannot be rebound | `test_identity_reuse_changed_intent_is_conflict` |
| One narrow target; unrelated rows preserved | `test_narrow_physical_target_and_unrelated_rows_unchanged` |
| Pending physical create reservation prevents a later write overwriting an independent create | `test_independent_job_can_proceed_while_affected_branch_frozen` applies the original late write after the independent create and checks both |
| Fresh bound changed-condition/route evidence | `test_stale_unverified_or_unchanged_recovery_evidence_rejected` |
| Exact readback, not just row existence | `test_exact_readback_mismatch_never_reports_success` |
| Bound provider observation and authoritative read | `test_forged_or_stale_provider_evidence_stays_uncertain`, `test_read_failure_after_apply_stays_frozen_until_authoritative_read` |
| Durable attempted-write, authoritative reconciliation, verified outcome and handoff audit | `test_audit_contains_exact_attempt_reconciliation_and_verified_outcome`; retirement test checks event order |
| Crash after intent but before provider admission | `test_crash_after_intent_before_provider_admission_remains_unknown` proves empty target + absent log cannot clear the intent |
| Journal unavailable before intent | `test_journal_failure_prevents_provider_submission` proves zero provider calls |
| Recovery crash/budget window | `test_crash_during_recovery_persists_shared_budget` |
| Failed fallback becomes uncertain; later success adopted without replay | `test_uncertain_recovery_opens_circuit_and_late_success_closes_without_replay` (operation resolves; circuit history remains retained) |
| Existing dispatcher integration and durable typed aggregate | `RepositoryIntegrationTests.test_dispatcher_full_lifecycle_and_codec_survive_restart` runs through Done with fake executor; verifies attempts/events/deliveries/verification after restart |
| Dispatcher reservation application followed by crash never invokes executor twice | `RepositoryIntegrationTests.test_dispatcher_uncertain_reservation_never_calls_executor` checks **zero** executor calls, including after journal adoption and handoff; admission remains a distinct future reconciliation concern |
| Stale lineage and out-of-band edit block adoption | `RepositoryIntegrationTests.test_repository_rejects_stale_lineage_and_external_aggregate_mismatch` |
| Aggregate Job ID is checked before mutation and current source identity is checked before adoption | `RepositoryIntegrationTests.test_repository_checks_aggregate_identity_before_mutation_and_source_on_read` |
| Closed codec cannot instantiate arbitrary types | `RepositoryIntegrationTests.test_codec_unknown_type_rejected_without_dynamic_import` |

The process-death fixture deliberately exits **77** after mock application; the
parent test requires that exact component exit. The claim-collision child must
exit **0** and report rejection. Those are component outcomes, separate from the
overall test runner's exit 0. Every test asserting no replay checks mock call
counts or compares complete row state; mock submit does not silently deduplicate.

## Review findings and resolved changes

This is an implementer design/failure-window review, **not an independent human
acceptance**. No sub-agent or external reviewer was requested or used.

* Read-before-write alone could reserve the same empty physical row twice while a
  prior create was active. The journal now reserves outstanding positions across
  independent logical operations; a late-write regression covers the fix.
* A persisted actor/epoch token alone could be copied into a replacement instance.
  Mutations now also require that instance's current-process claim. Reconciliation
  remains read-only; restart replacement requires explicit retirement/fresh epoch.
* Cancellation labels needed separate provenance treatment. Authenticated human
  stop/denial is persistent; unverified attribution stays unresolved; generic tool
  cancellation plus settled no-op remains eligible under valid authority/change.
* Authentic observed revocation could otherwise disappear with a fresh resolver
  context. The operation retains a permission stop across restart/handoff.
* Repeated reads could overcount recurrence/re-emit circuit notifications. Failure
  occurrences deduplicate by provider attempt; a circuit-open event is emitted once.
* Loose revision extraction could overlook a second malformed token. Q validation
  now rejects duplicate/malformed/zero/out-of-range revision tokens and requires
  the exact successor revision.
* Invalid request records must not poison later valid writes. Rejected operations
  with no submissions are excluded from affected-operation freeze/aggregate lookup.
* All external effect calls follow a durable intent. A crash even before admission
  leaves a recoverable, frozen operation; missing target/provider log is not proof.

## Remaining limits and acceptance boundary

The mock's SQLite transaction supplies authoritative operation finality and atomic
row apply that a future Sheets route may not expose. Same-host advisory locking
does not exclude another host/path or a noncooperating editor. Power-loss/storage
corruption, legacy-ledger import, live authorization, real validation/formatting
preservation, remote provider finality and unattended operations remain untested.
See the [interface document](AJ-0009-sheets-writer.md) for exact adapter obligations,
restart steps, unimplemented reset/resume behavior and the bounded next live-test
recommendation. No live test or follow-on job was created.
