# AJ-0016 independent review

Lineage: AJ-0016 / SpecRevision 1 / RunEpoch 1 / Attempt 1 / Nonce VA-ISOLATION-0016-01. Identity remains **PENDING_CANONICAL_RECONCILIATION**. Feature `aj-0016-isolation-prototype-v1`, accepted base `ce956abbe6b8217c1101edea1cbed6f8c9addeb3`. Independent reviewer inspected `dispatcher/isolation.py`, AJ15 design/review and existing transport/ledger contracts, authored adversarial regression probes, and ran the audit-blocked offline suite. No implementation edits, staging, commits, pushes, API calls or canonical mutations by reviewer.

## Findings and disposition

1. **Dispatch snapshot race:** the first remote read verified selected head, but a second read supplying Ready selection did not compare its returned head. A changed remote between reads could produce a synthetic dispatch result labelled with the stale selected head. Independent probe failed against the initial implementation. Resolved by verifying the second snapshot head equals selected/requested head; final adversarial probe passes.
2. **Dispatch rollback race:** rollback to HELD between gate and selection still returned a synthetic dispatch result. Independent probe failed against the initial implementation. Resolved by revalidating the authority decision and transport head after snapshot selection; final adversarial probe passes. This is bounded local selection checking, not atomic execution fencing against future hosted workers.
3. Reviewer initial fixture used invented IDs outside AJ15's required `AJ-` numeric schema; corrected reviewer fixtures to invented `AJ-9000`–`AJ-9006`. This fixture error is separate from the two implementation defects. Early bootstrap schema validation is beneficial and was reported to the implementer.

Initial corrected independent run: `python3 -B -m unittest tests.test_isolation_review`, **7 tests, 2 failures, 0 errors**. Initial independent full run: `python3 -B -m tests.offline_suite`, **304 tests, 2 failures, 0 errors**, log `/tmp/aj0016-independent-initial.log`. The failed cases are the two dispatch races above. Final expanded independent run: `python3 -B -m unittest tests.test_isolation_review`, **11 tests, 0 failures/errors**; `python3 -B -m tests.offline_suite`, **310 tests, 0 failures/errors**, log `/tmp/aj0016-independent-final.log`. Independent `python3 -B -m tests.git_bare_integration` and `python3 -B -m tests.isolation_bare_integration` also PASS (local synthetic Git only). No outstanding blocking defect found after corrections.

4. **Bootstrap restart pending-prefix bug:** a process death after first-row publication but before receipt persistence left that already-imported row pending. Restart advanced to row two and compared its payload against row one's pending payload, holding instead of reconciling the existing exact identity. Independent new crash probe reported an error. Resolved by reconciling an exact already-imported pending operation before entering the remaining-row import loop; the final independent crash probe passes with seven publications and seven commits total. Expanded initial run: 308 tests, one error, zero failures. This is a recoverability defect; no duplicate publication occurred.

## Independent evidence

`tests/test_isolation_review.py` covers a remote change and rollback between gate and selection; final-check remote change; corrupt/missing durable authority; rehashed wrong repository/ref/base/source/lineage/provisional identity/history; rehashed per-cell reconciliation and import-operation corruption; permanently retired activation epoch; preserved UNKNOWN audit exception; blank versus absent and rejection of numeric/date serial/formula/datetime cells by exact string export; self-consistent altered bootstrap nonce/run epoch rejection at activation and restart; process death after publication before response persistence; and lost import responses across restart with seven constructed commits and seven publications total, no replay.

AJ15's closed event/file schema is unchanged. Isolation control is a separate explicitly versioned local capsule, and bootstrap creates one snapshot-import event per AJ15 commit. Manifest identity is externally accepted only by its exact digest; computing a digest does not grant human acceptance. Unit tests simulate that accepted digest solely for offline verification.

## Limits

Local atomic replacement, fsync and flock apply to cooperating processes sharing one POSIX path; this does not establish hosted/distributed consensus, malicious-code exclusion, atomic remote worker dispatch or production route completeness. Memory transport is synthetic. Route inventory is a required future integration contract, not proof that production paths are isolated. Native typed cell envelopes preserve supplied representation; the AJ15 literal-string export rejects unsupported/lossy semantics. Privacy declaration is explicit trusted-input policy, not secret detection. No automatic projection import or old authority fallback exists. Original legacy unconditional write remains UNKNOWN; late writes are simulated only on invented data.

Recommendation remains bounded offline feature review only, followed by Dẹkun's exact manifest acceptance before any commit/push. The smallest subsequent transport work is a separately authorized disposable hosted synthetic repository test of exact-ref CAS, parent/blob verification and lost-response reconciliation with two independent coordinators, without production destinations or activation.

## Reviewed implementation fingerprints

- `dispatcher/isolation.py`: SHA256 `9e5a10f52223eb84e165eba7a992bdb0c7a1c9378b36aeeb1b0f4f16d6777b52`
- `tests/test_isolation_review.py`: SHA256 `fd7a468712987cdda65b4e3b177fb20a0f8b8d990cb24556a8bb5be67b5cefba`
