# AJ-0015 independent review

Review lineage: AJ-0015 / SpecRevision 1 / RunEpoch 1 / Attempt 1 / nonce VA-GIT-LEDGER-0015-01. Identity is PROVISIONAL PENDING_CANONICAL_RECONCILIATION. Reviewed feature `aj-0015-git-ledger-v1`, HEAD/base `d9cec7635bba5a214b990a479ff5ad4f68667126`. Reviewer independently inspected implementation, wrote adversarial probes, and ran tests; reviewer did not edit implementation, stage, commit, push, call external APIs, or mutate canonical rows.

## Findings and corrected history

1. Initial retirement race: `resume` persisted IN_FLIGHT, released lock, and published; concurrent retirement completed before publish, allowing retired writer publication. Independent initial concurrency probe failed. Implementation now rejects retirement while IN_FLIGHT; final probe confirms either serialization or explicit rejection prevents successful retirement during publication. An interrupted writer must first reconcile finality before handoff.
2. Initial projection diff omitted canonical-only rows although snapshot comparison reported SYNC_PENDING. Independent probe raised KeyError for AJ-0014. Corrected diff includes `before` canonical cells and `after: null`, making intended removal explicit; this only emits a projection and does not perform deletion/write.
3. Initial files-only reducer lacked actual Git-parent evidence for expected_head. Root added transport.parent and full ancestry verification. Independent adversarial probe rebuilds a self-consistent hash-chain/snapshot/manifest with a false expected Git parent: files-only reducer passes, authoritative remote ancestry validation rejects it. An additional probe rejects a hidden zero-event commit.
4. Root corrected duplicate reconciliation after a crash immediately after publication: exact pending SHA and blobs now clear pending/circuit. Independent restart probe verifies 1 constructed commit, 1 publication total, exact reconciliation, and cleared state.
5. Root reported its initial full-suite AST boundary failure from subprocess in dispatcher transport; it moved local bare-Git execution into test fixtures. Independent final full-suite boundary checks pass. This history is retained, not overwritten as an initial success.

Initial independent probe run: 6 tests, 4 passing, 1 failure (retirement race), 1 error (projection diff). Log `/tmp/aj0015-independent-initial.txt`.
Initial independent offline suite: 276 tests, 1 failure (retirement probe); source changed concurrently during run. Log `/tmp/aj0015-independent-full-initial.txt`.
After corrections: 278 tests passed. Final expanded run: **281 tests, 0 failures, 0 errors**, including the accepted 250 existing tests, 20 primary ledger tests, and 11 independent probes. Command `python -m tests.offline_suite`; log `/tmp/aj0015-independent-full-final.txt`. Network/socket/API and executable-launch audit guard active throughout this run.
Independent actual synthetic Git run: `python -B -m tests.git_bare_integration` PASS: actual SHA prepared before ref update; exact blobs; lost response; parent chain; CAS conflict; retired fence. This separate local Git integration invokes only local Git fixture commands; no network or real remote.

## Independent adversarial evidence

`tests/test_git_ledger_review.py` independently covers unknown cancellation freeze across restart, durable fingerprints after abandonment, changed payload rejection, authoritative-final-noop recovery budget across writer handoff, human cancellation across successor acquisition, same-SHA wrong-blob rejection, missing events and rehashed broken chain rejection, rehashed false Git-parent rejection, hidden no-op ancestry rejection, projection canonical-only rows, in-flight retirement serialization/rejection, and exact publication reconciliation after simulated process death.

## Scope and recommendation

No outstanding blocking defect found in this opt-in trusted-local-coordinator v1 after corrections. Recommend root acceptance for feature-only preservation after root acceptance. Agent Jobs remains current canonical operational/human authority. Git is prospective machine authority; no cutover, activation, migration, production remote adapter, Sheets write, Slack message, new credentials, PR, main merge, or deployment was performed.

Control-path flock provides an exclusive writer on the local/shared POSIX filesystem; distributed coordinators on unrelated control paths are outside this implementation's trust boundary. The live transport is deliberately absent. A future production adapter must obtain authoritative provider final/no-op receipts and exact remote ref/blob/parent evidence; generic cancellation and unchanged remote alone cannot permit recovery. Recovery condition verification is explicit trusted-caller attestation, not evidence-provider automation. Complete ancestry validation is linear in journal history and performs repeated reduction; no scaling claim is made. Secret filtering is not a DLP boundary: callers must obey minimum evidence-reference policy.

Before any future cutover follow the explicit A–H plan: resolve/fence AJ14 uncertainty; accept one reconciled bootstrap snapshot; genesis; independently compare all 17 columns to canonical; explicit machine-authority switch approval; project and verify Sheets; restart/lost-Git-response zero-duplicate proof; only then declare Git authoritative. AJ14's generic `user cancelled MCP tool call` has no handle/provider status. Repeated row/Drive history not visibly landed is observational evidence, not finality. Do not retry its Sheets write here.

## Reviewed file fingerprints

- `dispatcher/git_ledger.py` SHA-256 `30d25b206803e123958e22d4555af96b0f65361aeb0b87e9cc706a484bb338cc`
- `dispatcher/git_transport.py` SHA-256 `a2ef945064d944e1f799eb4ca32452d4c176577ea8c9cbb5ce77c5691e0aa0fd`
- `tests/test_git_ledger_review.py` SHA-256 `d4c665bf73fb96fa6f355e0c2b68947000ac3788ef7ed24fd687233808263de6`
