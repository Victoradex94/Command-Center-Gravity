# AJ-0016 offline isolation candidate

AJ-0016 / SpecRevision 1 / RunEpoch 1 / Attempt 1 / Nonce VA-ISOLATION-0016-01.
**PENDING_CANONICAL_RECONCILIATION**. Dẹkun owns dispatch and canonical reconciliation.
Repository Victoradex94/Command-Center-Gravity; accepted AJ15 feature base
`ce956abbe6b8217c1101edea1cbed6f8c9addeb3`; unused local branch
`aj-0016-isolation-prototype-v1` created from that exact commit. No commit/push,
production writes, credentials, permissions, real-data import, activation, migration,
messages, spend, merge/deploy or successor job. Remote read-only ref verification
and feature fetch were the only network operations. Relevant checkout instructions
were sought: no AGENTS.md/SKILL.md exists in this checkout or workspace instruction
directories; the provided skills catalog contains no applicable checkout skill.
AJ15 design and review were read; there is no standalone cutover-plan.md.

## Contract and architecture

This is an opt-in module; existing engine/adapter imports and behavior are unchanged.
It proves a separate synthetic authority domain, not production isolation.
A rename, revision or new Git ref alone is never a fence. LEGACY is a descriptive
starting phase, already nondispatchable because the original unconditional legacy
write has UNKNOWN effects. LEGACY -> HELD -> PREPARING -> NEW_ACTIVE are explicit.
Only `activate` performs the durable atomic authority selection CAS. One activation
epoch (1) is available; rollback consumes it permanently and selects no authority.
Missing, corrupt, contradictory or stale state holds. There is no old-Sheet fallback.
The immutable synthetic new snapshot has no operational mutation API in this prototype.

`LocalAuthorityProvider` persists one versioned hash-checked JSON envelope with
atomic replace, file/directory fsync and a permanent flock inode. Independent local
coordinators must share that provider path. The decision binds accepted manifest
digest, selected head, epoch, route inventory and UNKNOWN audit exception. This is
local cooperating POSIX process behavior, not distributed consensus, authentication,
anti-rollback storage or protection against malicious local filesystem edits.
The same mock Git provider may be shared by independent coordinator objects; actual
process contention is tested against the durable authority provider. Memory Git
is not a thread-safe hosted Git implementation. A fixed head must still be verified
at every gate. A changed/forked head holds rather than automatically advancing authority.

AJ15's closed file schema and exactly-one-event-per-commit rule are unchanged.
The control/manifest extension is **separate** from the AJ15 Git tree: no bootstrap
blob or control file is silently admitted to its reducer. Seven deterministic
snapshot imports create seven AJ15 commits, one event per imported row. Operations
have stable IDs derived from exact source identity, snapshot digest, job and cells;
the accepted manifest is bound in each full validated payload. Existing exact-ref,
parent, event hash, ancestry, corruption and fingerprint checks remain in effect.
Lost responses reconcile the same identity with zero publication replay, including
process death after publication but before response persistence. No past transition
history is invented from a status. Imports explicitly say prior history unknown.
The separate manifest must be durably preserved/accepted by its digest alongside
the separately verified Git head in any future implementation; it is not Git genesis
metadata in AJ15's tree. Offline tests simulate acceptance; they do not grant it.

## Legacy surface inventory and gating

All roles in the prototype require `surface=new`, exact epoch=1, exact selected head,
NEW_ACTIVE and verified complete AJ15 ancestry. Unknown roles deny. Calls with cached
Ready rows, queued commands or retired epochs cannot supply an alternate row to selection.

| Role | Legacy checkout surfaces to exclude in a future integration | Offline gate |
| --- | --- | --- |
| reader | SheetsRepository.read, SheetsWriter.read, GoogleSheetsAdapter observations | reader |
| allocator | Dispatcher intake/identity allocation, repository next-ID state | allocator |
| dispatcher | Dispatcher.ready/dispatch, Slack command/worker queues | dispatcher |
| writer | SheetsWriter.write, SheetsRepository mutations, tool bridge submissions | writer |
| cache | InMemoryRepository records, WriterJournal, SlackJournal, queued Ready snapshots | cache |
| reverse sync | SlackBoundary.sync, GitLedger.projection consumers, any future Sheet-to-Git importer | reverse_sync |

These are concrete integration obligations; production methods are not rerouted here.
No automatic projection-to-authority path exists. Import accepts only the exact
explicit bootstrap manifest, never projection output. `dispatch` returns a synthetic
selection receipt and rechecks head and authority around selection. It launches no
worker. Actual future worker effects require an epoch/authority fence at execution;
local receipt checks cannot guarantee atomic remote execution after a later rollback.
Uncertain old writes may still land on the invented old snapshot during bootstrap or
after activation; they cannot enter the separate new Git snapshot/decision.

## Conversion and privacy

Exact 17 column names/order and seven statuses come from the accepted model. The
manifest includes a complete source snapshot digest, per-cell hashes checked against
each cell, exact rows, provenance, explicit provisional inclusion, stable operations,
route inventory and the unreconciled UNKNOWN exception. `docs/AJ-0016-bootstrap-manifest.json`
is a review candidate with invented AJ-8000–AJ-8006 records and invented coordinates.
It is not canonically reconciled or approved for operational dispatch.

Typed cell envelopes preserve numeric values/date serials with format/timezone,
timezone-aware datetime representation, formulas and format strings, literal strings,
and distinct blank/absent tags without normalization. Number conversion never coerces
through display text. AJ15 requires strings; its export therefore rejects **all**
nonliteral/semantic cells, including numeric dates, blanks, absent cells and formulas,
rather than claim exactness. No timezone/date calculation, formula evaluation, live
format discovery or support for every native Sheets value is claimed. Datetime
objects must be explicitly represented with offset and timezone; arbitrary unsupported
objects fail. Roundtrip tests preserve typed representations and prove lossy exports
are rejected. The exact string importer preserves whitespace and empty-string literals.
Privacy minimization is an explicit synthetic-input policy: no personal data, secrets
or message bodies. No hidden trimming/redaction; caller attestation is not DLP.

## Acceptance evidence map

Full commands/results and exact file SHA256s are in AJ-0016-results.json and
AJ-0016-file-manifest.json. The final audit-blocked log and independent review are
working files. Inherited AJ15 tests continue to supply transport integrity evidence.

| Acceptance case | Evidence |
| --- | --- |
| Deterministic 17 fields, all seven statuses, per-cell digest, provisional inclusion | IsolationTests.test_exact_bootstrap_all17_all7_one_event_per_commit; test_deterministic_manifest_reconciliation_provisional_unknown |
| Wrong repo/ref/base/source/lineage and full import identity | test_wrong_repo_ref_source_columns_provenance_digest_rejected; reviewer rehashed identity/nonce/run_epoch probes |
| Delayed old writes during bootstrap and after activation; UNKNOWN retained | test_delayed_old_write_during_bootstrap_and_after_activation |
| All legacy roles excluded; stale cached Ready/queued command/retired epoch | test_all_legacy_routes_and_uninventoried_routes_denied; test_stale_ready_cached_queued_retired_epoch |
| Missing/contradictory epoch holds, crash before/after switch | test_missing_and_contradictory_epoch_holds; test_crash_before_after_switch_one_selected_authority; test_process_death_before_and_after_atomic_switch |
| Independent coordinators cannot both activate | test_independent_coordinators_shared_provider_only_one_wins; test_two_process_coordinators_shared_provider_only_one_wins |
| Lost response/restart same identity zero replay, publication-before-response crash | test_lost_response_same_identity_no_replay; independent reviewer crash/lost-response probes; isolation_bare_integration |
| Corruption/fork/stale head/hidden ancestry/extra file holds | test_corruption_fork_stale_heads_holds plus unchanged GitLedgerTests and GitLedgerReviewTests ancestry/corruption tests |
| Native date/number/formula/format/blank/absent semantics; loss rejection | test_native_typed_cells_preserve_and_reject_lossy_string_export; reviewer typed-semantics probe |
| No projection promotion, rollback holds forever | test_projection_never_promotes_authority; test_rollback_holds_no_old_reactivation; reviewer retired epoch probe |
| Selection races reject head change or rollback | reviewer dispatch_remote_changes_between_gate_and_selection and dispatch_rollback_between_gate_and_selection |
| Privacy explicit; no external I/O in suite; accepted regression suite | test_privacy_minimization_explicit_not_normalization; unchanged OfflineBoundaryTests; full offline suite |

## Subsequent verification recommendation only

After Dẹkun accepts this exact candidate manifest, the smallest separately authorized
hosted test is a disposable synthetic repository/ref: prove exact-ref CAS with two
independent clients, independently read exact parent/blobs/closed tree, inject a lost
response and reconcile the same operation without replay. No production Sheet or old
destination is needed. That would verify transport only, not production isolation;
provider decision CAS, all real route exclusions and worker execution fences would
still need separately authorized verification before any production activation.
