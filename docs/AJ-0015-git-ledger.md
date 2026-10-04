# AJ-0015 — Git-backed append-only machine ledger v1 candidate

Identity: **PROVISIONAL PENDING_CANONICAL_RECONCILIATION**. No Agent Jobs write,
ID allocation, AJ-0012/AJ-0014 row mutation, production migration or cutover.
Job AJ-0015 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
Nonce VA-GIT-LEDGER-0015-01. Authority supplied by root: explicit Victor instruction
Slack1791143425.384499. Accepted base
`d9cec7635bba5a214b990a479ff5ad4f68667126` from `codex-worker-route-v1`;
unused new local branch `aj-0015-git-ledger-v1`. Root owns coordination and
acceptance. Return before staging, committing or pushing. No PR, main merge,
deployment, live Sheets write, credentials, permissions or automatic successor.

## Authority and architecture

Agent Jobs remains the CURRENT canonical operational/human surface. Git is the
FUTURE machine authority, only after separately authorized verification/cutover.
The default dispatcher and accepted repository interfaces are unchanged.

`dispatcher/git_ledger.py` defines the closed Operation payload schema, canonical
UTF-8 sorted JSON/SHA-256 identity, pure reducer, durable local control state,
exclusive POSIX flock writer lease, retirement fencing, pending preparation,
exact-commit finality/reconciliation, bounded recovery and read-only projection.
`dispatcher/git_transport.py` defines the transport protocol and deterministic
memory fixture. The actual Git implementation lives in
`tests/git_bare_fixture.py`; it operates only on an existing synthetic local bare
repository. It constructs exact Git objects with fixed synthetic commit metadata
before CAS `update-ref`, reads actual ref SHA, exact blobs and commit ancestry.
There is deliberately no production hosted Git push adapter in this candidate.
A future adapter must independently enforce this same exact-ref/parent/blob
contract and supply trustworthy final/noop evidence; no live integration is claimed.

Each event contains JobID, RecordRevision, stable operation ID, expected prior
revision/Git head/event hash, exact intended 17-cell row, authority/context refs,
time, worker, route, SpecRevision/RunEpoch/Attempt/nonce, task/turn refs and
outcome/evidence refs. The transaction stores `events/<JobID>/<sequence>-<hash>.json`,
`snapshot.json`, `index.json` and `manifest.json`. One event is appended per commit;
previous event blobs remain byte-identical. The reader verifies complete files,
manifest hashes, event paths/hashes, chain, revision, operation uniqueness,
snapshot/index replay, actual commit parents and full append-only ancestry.
Merge commits, unindexed/missing/corrupt files and forks fail closed.

The local JSON control file stores only lease/retired identities, durable payload
fingerprints, pending intended files/commit SHA/local and remote heads, finality
receipt, circuit and the one shared recovery budget. It is not an operational
job database. Atomic replace, file and directory fsync preserve crash state.
All cooperating writers must share the same control path on one POSIX filesystem;
this is not a distributed lease/security boundary against malicious local code.
The permanent lock inode must not be deleted/replaced. Corrupt control data fails
closed. Retired writer identities cannot reacquire. Retirement while publication
is IN_FLIGHT is rejected; exact finality reconciliation is required first.

Precommit intents can resume or abandon without publication; fingerprints remain
reserved after abandonment. Local-only commits are recognized separately. The
attempt marker and intended SHA persist before publishing. Any generic exception
(including generic cancellation) freezes uncertainty; unchanged remote head alone
never establishes noop. Exact actual remote SHA plus independently read exact
blobs/manifest/history reconciles with zero replay. Changed ref yields conflict;
there is no force push or merge. Only an authoritative FINAL_NOOP receipt and a
verified changed-condition evidence reference allow one shared recovery attempt,
persisted across restart/handoff. Human permission cancellation blocks all later
publication/recovery including a successor. There is no automatic permission
renewal. `verified=True` and finality receipts are trusted coordinator/transport
attestations, not independently authenticated provider evidence.

Projection returns intended full snapshot and cell-row diff including canonical-only
rows, with SYNC_PENDING/VERIFIED metadata. It never calls Sheets. The exact existing
17 columns and seven statuses are reused from AgentJob/Status; metadata is never
an eighth job status. VERIFIED means the caller-supplied snapshot equals the
journal snapshot; it does not claim a live Sheets readback.

Data minimization: caller must supply sanitized intended cells and minimum
nonsecret evidence references. No Slack/Drive message body ingestion, credentials
or secret discovery is implemented. Exact 17-cell snapshots necessarily retain
the supplied row content; this trusted local API cannot identify arbitrary secrets
inside strings. Do not feed unsanitized message bodies/secrets into this API.

## AJ-0014 limitation and cutover plan ONLY

The exact AJ-0014 Sheets limitation is generic **`user cancelled MCP tool call`**,
with no handle/provider status. Repeated row/Drive history shows it did not visibly
land, but that is not finality. Do NOT try a Sheets write. No migration or authority
activation is performed by AJ-0015.

A. Resolve/fence the uncertain AJ-0014 write.
B. Obtain one accepted reconciled bootstrap snapshot.
C. Create genesis from that accepted snapshot.
D. Independently verify reducer output equals canonical exact 17-column data.
E. Explicitly authorize the machine authority switch, Git first.
F. Project to Sheets and verify exact live readback under separately authorized access.
G. Restart after a lost Git response and establish zero duplicate publication.
H. Only then declare Git authoritative.

Genesis bootstrap/import, provider finality evidence and production remote adapter
remain future cutover work. Recommendation: accept this offline candidate only as
an opt-in tested journal component; defer activation until A–H are verified.

## Verification and criterion map

Run `python3 -B -m tests.offline_suite`: all 250 accepted tests unchanged, plus
new ledger/reviewer probes; socket and executable audit events blocked. The
separate command `python3 -B -m tests.git_bare_integration` uses only temporary
local bare fixtures, no network/connector calls. `python3 -B -m tests.simulate`
and `python3 -B -m compileall -q dispatcher tests` also run.

| Criterion | Evidence |
| --- | --- |
| Exact append/reduce 17 columns and seven statuses | test_append_reduce_exact17, test_projection_all_seven_statuses |
| Semantic duplicate zero second commit; changed payload rejection | test_duplicate_zero_second_commit, test_changed_payload_reject, test_fingerprint_persist_abandoned |
| Stale head/revision zero mutation | test_stale_head_no_mutation, test_stale_revision_no_mutation |
| Crash precommit resume/abandon, local commit not published | test_crash_precommit_resume, test_precommit_abandon_no_duplicate, test_local_not_pushed |
| Lost response exact remote SHA zero replay | test_lost_response_exact_remote_zero_replay, actual Git bare integration |
| Unchanged head not noop, one changed-condition shared recovery | test_unknown_unchanged_not_noop, test_one_shared_changed_condition_recovery, test_changed_condition_success |
| Advanced remote/fork, no force update | test_remote_advanced_conflict, bare fixture CAS stale update |
| Exclusive retirement/handoff and stale fence | test_writer_retirement_handoff, independent concurrent publication probe |
| Human permission blocks; generic unknown cancellation freezes | test_permission_cancellation_blocks, test_generic_cancel_freezes, independent successor probe |
| Persistent fingerprint/circuit/budget | restart tests above, independent handoff budget probe |
| Deterministic reducer, append-only events, corruption detection | test_replay_determinism, test_corrupt_missing_broken_chain, independent probes |
| No live APIs/messages/credentials; accepted tests remain | unchanged offline boundary tests and full audit-blocked suite |

Historical initial offline failure and independently failed retirement/projection
probes are retained under `docs/history/AJ-0015/`. Corrections moved executable Git
fixture out of dispatcher imports, fenced IN_FLIGHT retirement and included
canonical-only projection diff entries. Final independent findings/results are in
`AJ-0015-review.md`; final actual validation summary in `AJ-0015-results.json`.
