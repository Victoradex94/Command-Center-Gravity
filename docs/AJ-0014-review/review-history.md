# AJ-0014 independent review history

All evidence and test provider operations in this directory are synthetic/offline. No live dispatch, external messages, ledger writes, staging, commits, or pushes.

Candidate: `codex-worker-route-v1`, accepted base `a845dd7dc36edaaa029f4d73147a3d4a4bc197b1`. Scope reviewed initially: complete `dispatcher/codex_worker.py`, complete `tests/test_codex_worker.py`, existing `adapters.py`, `writer_journal.py`, model gates/route/return contracts, engine start/return integration.

## Round 1

Command `python -m unittest discover -v`: 237 tests, PASS. Output `initial-full-suite.txt`.

Command `python -m unittest discover -s docs/AJ-0014-review -p test_independent_probes.py -v`: 5 independent tests, all FAIL on initial candidate. Output `initial-probes-isolated.txt`. Earlier `initial-probes.txt` also collected 22 imported fixture tests; retained as historical evidence, not counted as independent tests.

- R1 HIGH: terminal receipt may regress to authenticated substantive Running. Sticky terminal flag then permits a replacement following fence, despite observed running conflict. Two independent tests reproduce regression and unsafe replacement.
- R2 HIGH: attributed provider `failed` execution does not enter durable failure/recovery accounting. Fence, restart, and distinct attempt dispatch succeed without changed-condition recovery. This bypasses shared recurrence budget.
- R3 MEDIUM: envelope `authenticated='false'` passes baseline truthiness validation and is normalized. Strict transport-boundary type validation needed.
- R4 HIGH: permission denial during exact-handle lookup is returned as generic uncertainty and leaves no durable permission stop. New wrappers/restart lose that critical access condition; adoption must also respect the stop.

Findings delivered to implementation owner for correction in same lineage. Reviewer changes are confined to this review directory.

## Round 2 and final disposition

R1-R4 corrected in the same candidate. Expanded independent tests verified permission-stop acceptance fencing, idempotent observation failure accounting, and recurrence after changed-condition recovery. Intermediate guarded offline suite: 244 PASS. Seven independent probes: PASS. Outputs: `round2-offline-suite.txt`, `round2-probes.txt`.

R5 MEDIUM: rejected lookup receipts were discarded, preserving only error text and losing exact contradictory recovery evidence. Reproduced with wrong-nonce receipt (`round2-r5-probe.txt`); corrected with durable `rejected_receipt` alongside lookup error. The initial reproduction used a provisional `raw` field assertion; final test asserts the implemented `rejected_receipt` field and exact original receipt contents.

Final implementation also binds valid normalized returns to execution observations, so terminal evidence fences later regression and failed returns enter the shared budget exactly once. Added independent tests for both paths. Reviewed the complete final adapter, all 25 primary tests, all 10 independent tests, and architecture/recovery/acceptance matrix document. Stop intent/lost-ack process-crash coverage and true Blocked-return normalization additions reviewed.

Final commands:

- `python -m tests.offline_suite`: 250 PASS, 0 failures, 0 errors; outbound I/O/executable-launch audit guard active. 215 unchanged baseline + 25 primary adapter + 10 independent regression tests. Output `final-offline-suite.txt`.
- `python -m unittest discover -s docs/AJ-0014-review -p test_independent_probes.py -v`: 10 PASS. This is the independent subset already included above, not 10 additional unique cases. Output `final-probes.txt`.
- `sha256sum dispatcher/codex_worker.py tests/test_codex_worker.py tests/test_codex_worker_review.py docs/AJ-0014-worker-route.md`: exact reviewed content hashes in `reviewed-candidate.sha256`.

All five findings are corrected and independently verified. No remaining in-scope blocker found. Baseline tracked implementation/contracts remain unchanged; all candidate changes are additions. Parent requested the independent probes also be added to normal suite as `tests/test_codex_worker_review.py`; that is the sole reviewer-authored path outside this review directory.

Limits: this review supports LOCAL/MOCK acceptance only. Trusted caller/current-authority inputs, a shared dedicated journal on one POSIX host, JSON-serializable fixture evidence, and no live-provider guarantees remain explicit. Root acceptance and separate preservation approval remain gates. No staging, commit, push, external communication, live dispatch, ledger writes, or AJ-0012 access performed.
