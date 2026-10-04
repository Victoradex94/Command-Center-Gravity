# AJ-0007 implementation evidence

Implementation evidence for Dẹkun's review; not a ledger update or live acceptance.

## Exact lineage and repository observation

- Job ID: **AJ-0007**; SpecRevision: **1**; RunEpoch: **1**; Attempt: **1**.
- Nonce: **VA-DISPATCHER-0007-01**. Coordinator: **Dẹkun**.
- First substantive UTC observation: **2026-10-04T05:56:04Z**, actual shell
  inspection of root, identity, ref, files and interpreter.
- Actual root: `/workspace/Command-Center-Gravity`; `/workspace` was not used as
  the working repository.
- Origin: `https://github.com/Victoradex94/Command-Center-Gravity.git`.
- Actual branch: `work`; no local `main` assumed.
- Base/HEAD: `dea8cddc0bb6e7ab20479d8aca25121590749a3b`, also the locally available
  `origin/main` at inspection. No fetch was performed.
- Baseline: only `README.md`. No applicable root/ancestor `AGENTS.md` found.
  Runtime: Python **3.12.14**.
- Real AJ-0006 evidence was not present in this checkout and was not accessed or
  changed. Its test is an isolated in-memory fixture.

## Acceptance mapping

| Request | Implementation and evidence | Boundary |
| --- | --- | --- |
| 1. Exactly 17 fields | `AgentJob`, `AGENT_JOB_COLUMNS`, round-trip/wrong-width tests | No sheet schema change |
| 2. Exactly seven statuses | `Status`; complete vocabulary asserted | Holds, return classes and delivery state separate |
| 3. Validated transitions | Full graph and guarded commands; all 49 status pairs exercised | Truth of supplied evidence remains caller responsibility |
| 4. Identity, dedup, nonce | `Lineage`, source/outcome lookup, reserve-before-dispatch, attribution tests | In-memory deterministic matching |
| 5. Routing/override | Capability/access/readiness inputs and seven gates; unavailable/unauthorized/override tests | No live route proven |
| 6. Return classes/Done | Complete return contract, classification, explicit passing criterion/outcome checks and Review-before-Done | Tests are synthetic |
| 7. Late/stale fencing | Cancellation, reassignment, supersession and nonce/worker/run/attempt tests; retained rejected evidence | No physical stop guarantee |
| 8. Audit/delivery | Events/outbox, uncertain send and missing-marker recovery | No durable exactly-once transaction |
| 9. Scenarios/AJ-0006 | `python3 -m tests.simulate` and full unittest suite | Fixture-only recovery |
| 10. Setup/interfaces | README architecture, schema and exact future adapter ports | No live implementations |
| Fast-path correction | Immediate receipt, compact brief/gates, dispatch with empty Output/Verification, separate admission/start | Pending delivery is not sent; provenance required before Done |

## Nine exact required scenario families

This maps the coordinator's nine required families to actual tests in
`tests/test_protocol.py`. The simulation retains its test-class grouping so
additional protocol invariants also execute; its results are in
`simulation-results.json`. Every test named below passes in the corrected suite.

| Required family | Actual test names | Expected and observed behavior |
| --- | --- | --- |
| Duplicate instruction | `test_exact_and_semantic_duplicates_never_create_or_dispatch`; `test_completed_duplicate_returns_existing_output` | PASS: existing identity/output retained; no extra execution. Matching uses normalized identity fields, not natural-language inference. |
| Explicit assignment to an incapable worker | `test_named_unavailable_worker_is_preserved`; `test_subscription_or_documentation_is_not_route_proof` | PASS: explicit unavailable assignment preserved; a named worker with insufficient capabilities is ineligible. |
| Blocked dependency | `test_blocked_dependency_requires_usable_evidence_and_all_readiness_gates` | PASS: concrete failed prerequisite is recorded as Blocked; no dispatch; Done label alone rejected; resolution evidence recorded; all six other gates and current route rechecked before Ready. |
| Partial completion | `test_partial_output_preserved_and_cannot_complete` | PASS: partial output retained through Review/Blocked; incomplete work cannot reach Done. |
| Claimed completion without adequate verification | `test_missing_or_stale_acceptance_evidence_blocks_done`; `test_no_direct_working_to_done_or_worker_self_verification` | PASS: missing/stale evidence, skipped Review and worker self-rating cannot establish Done. |
| Recommended follow-on work | `test_routine_recommendation_is_not_attention_or_new_job` | PASS: recommendation creates neither another job nor a routine attention escalation. |
| Lost acknowledgement | `test_lost_command_ack_does_not_create_execution` | PASS: uncertain accepted acknowledgement recovered without resend or execution. |
| Missing completion notification | `test_definitive_failed_notification_retry_only_after_absence_check`; `test_unknown_send_observed_existing_message_is_not_resent` | PASS: notification after Done is recovered separately; no duplicate accepted message or worker rerun. |
| Late result after cancellation or reassignment | `test_cancelled_late_result_never_reopens_or_overwrites`; `test_reassignment_fences_old_worker_and_requires_safe_previous_state` | PASS: late returns cannot revive cancelled work or overwrite reassigned current output. |

AJ-0006's fixture records a wrong-path failure in `/workspace`, confirms the old
process failed with no effects, rejects mismatched authorization, then runs an
explicitly approved Attempt 2 in the discovered repository root. The failed
attempt stays preserved. It does not reopen the real AJ-0006.

## Independent review and verification

A separate read-only reviewer exercised four initial failures: pause hold lost
across uncertain writes, unknown verification permitting Done, admission recovery
missing/nonempty run IDs unchecked, and obsolete delayed notifications. All were
fixed with regressions. The reviewer independently ran the then-current 54-test
suite and confirmed these fixes. A second pass identified stale activity clearing
later uncertainty and a return during pause preventing resume. Both were fixed
with two further regressions. Final independent review found no remaining concrete
blockers within the offline scope. All six findings are fixed. The reviewer ran
the final **57-test suite: 0 failures, 0 errors, OK (0.445s)** and confirmed that
the simulation exactly matches the saved JSON. The implementation run also passed
all **57 tests (0.473s)**; compile and complete-diff whitespace checks passed.
Additional evolving-clock probes verified fresh resume evidence without redispatch.

## Corrective implementation revision after coordinator review

This correction stays within **AJ-0007 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
VA-DISPATCHER-0007-01**; it is not a new execution attempt, job or follow-on.
Read-only acceptance review identified missing end-to-end blocked-dependency
coverage. The added test uses only an isolated prerequisite fixture; it creates
no real prerequisite job or external dispatch.

The test initially reproduced a defect: `Gate(True, "Done")` released Blocked
work without usable prerequisite evidence. The smallest runtime correction in
`Gates.validate` rejects a bare status label as dependency evidence, ignoring
case and surrounding whitespace. Empty evidence was already rejected. This is
an additional guard, not an artifact verifier; factual usability remains an
explicit trusted coordinator/adapter attestation.

The corrected test records the failed prerequisite and its owner/unblock action,
proves zero dispatch while Blocked, records artifact/version and checked-result
resolution evidence, fails each other readiness gate in turn, rejects an offline
route, and reaches Ready only after all checks pass. Lineage is unchanged and no
attempt is dispatched merely by becoming Ready. The six previous independent
review fixes and all prior tests remain in place. The corrected full suite has
**58 tests**, with zero failures/errors; the simulation, compilation and final
diff whitespace checks pass. This correction's execution results are reported
in the task return; the earlier independent review counts above are historical.

Commands: `python3 -m unittest discover -s tests -v`, `python3 -m tests.simulate`,
`python3 -m compileall -q dispatcher tests`, `git diff --check`.
No dependency installation is needed or performed.

There are no credentials/API keys, live clients or external API calls in the
implementation. This task performs no Slack/Sheets/Gmail/Gemini/Antigravity live
connection, deployment, permission/sharing change, external message, spend,
ledger/Master Workplan edit, push, merge, PR or follow-on creation.

Code is available in the cloud task repository diff. HEAD remains at the base
commit; changes are uncommitted. The task return contains file and diff counts.

Limitations: process-local state; trusted authority/evidence; no remote auth,
scheduler, durable aggregate reconstruction, distributed claim/transaction,
natural-language duplicate inference or physical worker-control guarantee.
Implementation tests prove synthetic code behavior, not operational adoption.

Recommendation only; not assigned: one bounded offline aggregate-codec and
restart/recovery contract-test job. Dependency: this core and recorded fixtures.
Suitable worker: Codex. Verify exact 17-cell round trips, retained lineage and
outbox history, and no duplicate fake dispatch/delivery after restart. No live
access or new persistent connection is needed. No job or assignment is created.
