# AJ-0014 durable Codex worker route — synthetic candidate

Lineage: AJ-0014 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
Nonce VA-CODEX-ROUTE-0014-01. Base a845dd7dc36edaaa029f4d73147a3d4a4bc197b1
(accepted aj-0011-slack-adapter), working branch codex-worker-route-v1.
Delegated authority references: proposal Slack 1791135833.518579 and Victor's
“yes to all” 1791138961.408669. These references came from the delegation;
this implementation performs no live Slack verification or dispatch.

## Architecture and caller responsibilities

`dispatcher.codex_worker.CodexWorkerAdapter` implements the existing four-method
ExecutorAdapter port. DispatchRequest, Admission, RunObservation,
ReservationObservation, ReturnEnvelope and all ledger/engine code are unchanged.
The adapter never writes a ledger, sends a report, launches a child task, or
imports a network provider. It is opt-in and is not wired into a production entrypoint.

Use one dedicated WriterJournal path/scope per coordinator deployment, shared by
ALL adapter instances, attempts, wrappers and fallback routes. A trusted coordinator
injects a clock and a fresh Authority callback, with exact request digest, current
lineage/nonce, active status, authority reference, Gates, selected RouteCandidate
and required capabilities. This is a trusted local boundary, not authentication
of arbitrary Python callers. Explicit Codex assignment, exact route, fresh gates,
usably evidenced dependencies and readiness are checked before dispatch and
return adoption. Root must propagate cancellation/reassignment/supersession
immediately through `fence`, and revoke `Authority.active` in its own durable
source of truth. Historical inspections remain permitted; they cannot accept output.

`DeterministicMockProvider` uses a separate durable fixture journal. It records
submit invocations, deterministic task/turn handles and receipts, including accepted
work whose response is lost. Its `observe` method is a synthetic fixture control,
not a provider API. A transport must declare `synthetic_only=True`. The declaration
is an injection guard, not a security sandbox against malicious Python code.
There is no production transport implementation or activation switch.

## Durable evidence and crash recovery

SQLite synchronous FULL commits and the existing POSIX advisory lock serialize
cooperating local callers across threads/processes. Locks span provider calls;
provider effects are outside the journal transaction. The journal persists exact
request, limits, brief, authority/gates, lineage/nonce/worker/route, intent timestamp,
task and turn, admission, raw observations, accepted and rejected raw returns,
stop/fence states, stable failure fingerprint and changed-condition evidence.
All generated receipts, stored evidence containers and observations are synthetic.

| Crash/ambiguity | Permitted recovery | Submission policy |
|---|---|---|
| Before intent commit | Fresh dispatch with current gates | No recorded intent exists |
| After intent, before submit | Inspect original reservation | Frozen even if authoritative lookup is absent |
| Accepted, response lost / receipt not saved | Inspect original reservation; bind exact attributable task+turn | Never send replacement |
| Admission receipt saved | Same bound request returns same admission | No new submission |
| Task+turn known, lookup missing/conflicting | Inspect same handles; retain uncertainty | Never fall back to another handle |
| Stop response lost | Inspect exact handles | Stop intent fences output; no repeated stop send |

Intent is committed before mock submission. Every repeat of the same identity
compares the entire canonical request; changed nonce, brief, limits, worker or
route is rejected. Same-handle reads are observations and do not consume a retry
budget. Missing handles, lookup failures and negative lookups never prove that
replacement is safe. This intentionally sacrifices liveness after a pre-submit
crash; there is no automated resubmission/reset facility.

Admission maps to a non-substantive running observation because the unchanged
RunObservation contract has no admitted state. It cannot pass Dispatcher.start.
Only attributed running evidence with explicit substantive work can pass start.
A provider return cannot bind admission. It needs a known exact handle, current
authority, full attribution, explicit completeness, no truncation, all return fields,
criterion coverage, coherent execution state and a valid ReturnEnvelope. Missing,
conflicting and truncated evidence is retained in rejected_returns with a reason.
Duplicates are idempotent; conflicting duplicates and later replacement outcomes
are retained as rejections, never overwrites. Partial/Blocked/Full classify worker
claims only. Root uses Dispatcher.receive and independent Verification/complete;
report delivery stays in the existing coordinator-owned outbox. The adapter never
sets independently_accepted=True or changes a ledger status.

`request_stop` journals requested/fenced before transport, then records acknowledged,
unsupported or unknown. Acknowledgement is not physical termination. Only an
attributable stopped observation confirms stopped. Conflicting observations after
a terminal state latch an unresolved conflict, retain the raw receipt and prohibit
automatic replacement even after fencing; this candidate provides no reset API. Root may fence unresolved work
without asserting termination; a successor requires confirmed terminal evidence
AND an explicit fence. Unsupported cancellation remains uncertain.

## Recovery budget and permission stops

Failures are grouped by job, excluding attempt, route and wrapper. The fingerprint
is a stable hash of job + worker-execution-boundary, deliberately coarse to prevent
relabelled failures evading the budget. Execution failures from valid observations or returns are recorded once per operation;
repeated reads never inflate the count. A second failure opens the circuit, including
recurrence after the one allowed changed-condition recovery. Permission errors latch
a permanent permission stop in this candidate; there is no permission renewal API.
`authorize_recovery` requires fresh exact authority and explicit changed-condition
evidence, consumes one persisted job budget, and binds that allowance to a specific
future identity. It cannot resubmit a frozen intent, bypass unresolved prior execution,
clear a circuit, or undo permission denial. Choosing a different journal would bypass
local history; callers must preserve the shared path, and this code does not claim
distributed deduplication or protection against administrators deleting its database.

## Acceptance-to-test matrix

All tests and provider results below are synthetic. Primary tests are in
`tests/test_codex_worker.py`; independent regressions are in
`tests/test_codex_worker_review.py`. The unchanged baseline contributes 215 tests.

| Acceptance | Tests / evidence |
|---|---|
| 1 duplicate binding, changed request | duplicate_restart_one_submission; changed_payload_rejected; concurrent_wrappers_one_submit |
| 2 ambiguous admission, original lookup | timeout_after_acceptance_reconciles; timeout_missing_handle_never_replaced; exact_handles_no_rebinding |
| 3 crash windows, same-handle reads | crash_before_submit_freezes; crash_after_acceptance_recovers; crash_after_receipt_is_idempotent; shared_budget_and_recurrence |
| 4 admission/start/return/acceptance/report separation | substantive_start_only_with_attributed_evidence; engine_admission_start_return_independent_review; partial_blocked_returns_do_not_accept; baseline delivery tests |
| 5 idempotent attributed output | full_return_duplicate_and_conflict; incomplete_conflicting_truncated_attribution; cancelled_reassigned_superseded_returns_fenced; revoked_authority_cannot_adopt |
| 6 stop stages | stop_ack_is_not_termination; unsupported_stop_fences_return; crash_stop_intent_and_lost_ack_fence_without_termination |
| 7 gates and explicit selection | gates_explicit_worker_readiness_dependency; revoked_authority_cannot_adopt; stale_authority_and_route_are_rejected |
| 8 restart recovery controls | permission_stop_survives_restart; shared_budget_and_recurrence; timeout_missing_handle_never_replaced |
| 9 baseline/exclusive writer/synthetic boundary | full tests.offline_suite, production_transport_rejected; engine/ledger/writer files unchanged |

Independent regression coverage additionally exercises terminal regression and replacement
fences, execution-failure recovery and recurrence, strict boolean return authentication,
lookup permission stops and acceptance fences, and raw rejected receipt retention.

Independent adversarial review and retained findings are under `AJ-0014-review/`.
Final command results and file hashes are under `AJ-0014-evidence/` and the artifact
manifest. Manifest excludes itself to avoid recursive hashing. Test output timing
is observational, not an acceptance criterion.

## Limits and remaining gates

Local POSIX host only; all cooperating users need the same journal. No distributed
lease, provider exactly-once guarantee, genuine Codex API authentication, live route
verification, cancellation guarantee, or unattended service is claimed. Inputs and
raw evidence must be JSON serializable. Synthetic receipt authentication means a
trusted fixture assertion. Current authority is provided by root, not looked up in
Slack/Sheets. No migrations, new permissions/credentials, automatic successors,
commit/push/merge/deployment or AJ-0012 changes are included. Root acceptance and
separate preservation approval remain outstanding; live activation is out of scope.
