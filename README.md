# Command-Center-Gravity — Dispatcher Adapter v1 core

AJ-0007 implements a **pure Python 3.12 protocol engine with in-memory adapters**.
It does not connect to Slack, Google Sheets, Codex Cloud, Gemini, Antigravity or
Gmail. No credential, external SDK, network call, deployment or scheduler is
included. The real Agent Jobs and Master Workplan are untouched.

## Run locally

From the actual repository root, using an existing Python 3.12 interpreter:

```sh
cd /workspace/Command-Center-Gravity
python3 --version
python3 -m unittest discover -s tests -v
python3 -m tests.simulate
python3 -m compileall -q dispatcher tests
```

Nothing needs to be installed. All imports are Python standard library modules.
The simulation prints deterministic JSON for nine scenario families, the
synthetic AJ-0006 recovery case, and review regressions; it exits nonzero if any
assertion fails. Its fixed timestamps and fake references are explicitly
synthetic. See [recorded results](docs/simulation-results.json) and
[acceptance evidence](docs/AJ-0007-acceptance.md).

## Architecture

| File | Responsibility |
| --- | --- |
| `dispatcher/model.py` | Exact 17-cell row, seven statuses, lineage, brief, gates, routes, returns and typed verification checks |
| `dispatcher/engine.py` | Coordinator commands, transition guards, dispatch reservation, run reconciliation, review, cancellation, revision and outbox recovery |
| `dispatcher/store.py` | Copy-on-read aggregate, audit records, exclusive writer, version/lineage comparison and readback; injected uncertain writes |
| `dispatcher/adapters.py` | Executor/message protocols and deterministic fakes; no live implementations |
| `tests/support.py` | Fixed-clock synthetic records and evidence, used only by tests |
| `tests/test_protocol.py` | Nine protocol families and isolated AJ-0006 failure/correction fixture |
| `tests/test_review_regressions.py` | Cases found during independent review and related boundary checks |

The engine receives a repository, coordinator writer identity and clock. It never
allocates a new job ID or creates a follow-on job on its own. The caller supplies
an authorized ID and bounded brief. Public mutations reread the job and require
its exact `Lineage`; commits compare both version and lineage and read back the
saved aggregate. Only the active exclusive writer may mutate. Root may explicitly
delegate that role to a recording proxy. Workers have no ledger-writing port.

`Record` is internal control state, not an extra ledger schema. JSON in existing
J and M and structured text in Q carry controls. `AgentJob.to_cells()` and
`from_cells()` preserve exactly this A–Q order:

| Column | Existing field | Model attribute |
| --- | --- | --- |
| A | Job ID | `job_id` |
| B | Parent Workplan ID | `parent_workplan_id` |
| C | Job / Deliverable | `job_deliverable` |
| D | Assigned Worker | `assigned_worker` |
| E | Status | `status` |
| F | Priority | `priority` |
| G | Assigned At | `assigned_at` |
| H | Control Date | `control_date` |
| I | Dependency | `dependency` |
| J | Source / Brief | `source_brief` |
| K | Output | `output` |
| L | Verification | `verification` |
| M | Return Summary | `return_summary` |
| N | Needs Victor | `needs_victor` |
| O | Victor Decision | `victor_decision` |
| P | Last Update | `last_update` |
| Q | Run / Revision ID | `run_revision_id` |

Statuses are exactly `Intake`, `Ready`, `Working`, `Review`, `Blocked`, `Done`,
`Cancelled`. `Partial` is a return class; `Paused` is a hold; delivery has separate
states. No schema/status migration is made.

## Fast path and state rules

1. `acknowledge(source)` validates the authenticated owner and records receipt
   before investigation. `deliver_acknowledgement(source, messenger)` explicitly
   invokes delivery in the original thread. Pending is never described as sent.
   `intake(..., actionable=False)` creates no job. Duplicate source/outcome lookup
   returns the existing job, including terminal work.
2. Supply a compact `Brief`: outcome, target, scope, criteria, exclusions,
   authority, inputs, destination, control point, stop/recovery behavior,
   verification method, return route and verified parent/reason. Seven `Gates`
   require true checks with evidence for authority, identity, capability, access,
   dependencies, readiness and return contract.
3. `ready(...)` checks the brief, gates and route. `dispatch(...)` rechecks
   volatile evidence (default freshness: 60 seconds), reserves the exact
   Job ID / SpecRevision / RunEpoch / Attempt before invoking the executor,
   then records admission. Repeated dispatch of a reservation is a no-op.
   Output, Verification, return fields and exhaustive provenance are not required
   before dispatch. Minimal gate evidence must still be real; unknown never passes.
4. Admission leaves `Ready`. Only `start(...)` with authenticated substantive
   work and a bound nonempty current run ID establishes `Working`. Assignment
   time is distinct. Unknown admission becomes `Blocked`; inspect the original
   reservation and call `recover_admission(...)` without another dispatch.
   Older activity cannot clear newer uncertainty or regress `LastSignalAt`.
5. `receive(...)` validates current lineage, nonce, worker/run, authentication,
   timestamps, return fields and criterion accounting. Contradictory Full claims
   become Partial. Partial output is retained. Cancelled, stale, malformed and
   conflicting returns remain audit evidence and cannot overwrite current output.
   Identical redelivery is a no-op. Paused returns remain held in Blocked.
6. `complete(...)` requires Review, a Full current return and independent
   `Verification`. Every criterion/outcome check must explicitly pass with
   `Check(passed, method, evidence)`. Unknown, untested, missing or failed evidence
   cannot pass. Check artifact, destination, tests/readbacks, permissions,
   dependencies, side effects, parent reconciliation and provenance. The checker
   must differ from the worker and inspect at/after the return. Delivery remains
   separately tracked; notification failure does not undo Done.

`ALLOWED_TRANSITIONS` is the full §7 graph, including Blocked → Working
reconciliation, Done → Review correction, and explicitly authorized Done/Cancelled
→ Intake reopening. Use guarded public commands, not the private transition
helper. Other pairs, including Working → Done, are rejected.

`Authorization` binds action, Job ID, authenticated owner source and evidence.
Cancel, pause/resume, retry, reopen and brief/assignment changes require it.
`retry` advances Attempt; `reopen` advances RunEpoch; material `revise` advances
SpecRevision and RunEpoch and retriages through Intake. A safely acknowledged
`clarify` advances only SpecRevision while keeping the execution. Prior briefs
and assignments remain in audit history. Notification retry changes no lineage.

Old runs must be completed/stopped/failed before redispatch, or an isolated retry
needs specific authorization and isolation evidence. Fencing prevents acceptance;
it cannot stop a physical worker or undo effects. `reconcile_prior_attempt`
records a fenced run's terminal state after reopening without adopting its output.
Pause and its hold are saved together. Explicit resume removes the hold; renewed
activity or current-return review still follows separately.

## Exact future adapter boundaries

These Python `Protocol` contracts are **not proof of a live route**. Each future
adapter requires separate authorization and verification. Authentication flags,
scoped authority, route evidence and check results are trusted adapter/coordinator
attestations, not cryptographic proof.

| Future system | Callable boundary | Adapter responsibilities |
| --- | --- | --- |
| Slack inbound | `SourceCommand(workspace, author, channel, message_ts, thread, version, permalink, authenticated)` → `acknowledge` / `intake` | Authenticate actual event and owner; preserve workspace/thread/version. Resolve actionable intent outside core. Display names, quotes, bots and forwarded content confer no authority. No-mention intake is unverified. |
| Slack outbound | `MessageAdapter.inspect(event_key, destination, thread) -> MessageObservation`; `send(event_key, destination, thread, text) -> str` | Resolve verified destinations. Inspect exact EventKey before any send/retry. Return `found` with reference, positively established `absent`, or `unknown`. Raise `RejectedDelivery` only for definitive nonacceptance. Enforce stricter provider retry rules. |
| Google Sheets | `JobRepository.read(job_id) -> Record`; `all() -> tuple[Record, ...]`; `commit(record, expected_version, expected_lineage, writer) -> Record`; `assert_writer(writer)`; `reconcile(job_id, writer) -> Record` | Verify A1:Q1 against `AGENT_JOB_COLUMNS`. Convert only 17 cells; restore controls/history. Reread by ID/revision, compare, write and read back; persist exclusive ownership/uncertainty. Do not assume row position, atomic claim or exactly-once transaction. |
| Codex Cloud | `ExecutorAdapter.dispatch(DispatchRequest) -> Admission`; `inspect(worker_run) -> RunObservation`; `inspect_reservation(DispatchRequest) -> ReservationObservation`; `request_stop(worker_run, reason) -> str` | Verify repository/environment and route; submit exact identity/brief/limits; retrieve native result as `ReturnEnvelope`; separate admission/start; recover original reservation. Stop-request acknowledgement is not termination proof. |
| Gemini | Same `ExecutorAdapter`, separate implementation and route candidate | Verify authorized execution and result retrieval. A subscription/documentation is insufficient. Preserve an unavailable explicit assignment; do not silently substitute. |
| Antigravity | Same `ExecutorAdapter`, separate implementation and route candidate | Verify environment, capability/access, native run identity, attribution, recovery and stop semantics. No current live route is claimed. |

`DispatchRequest` contains lineage, nonce, worker, route, brief and bounded limits;
its idempotency key is `Lineage.key`. `ReturnEnvelope` requires lineage, nonce,
worker/run, return ID, observation/finish timestamp, attempted work, output,
evidence, remaining work, blockers, side effects, recommendation, classification
claim, authentication, met/unmet criteria, next owner, failed gate, last confirmed
execution state and control point. Use explicit `Not applicable` or explained
unknowns where appropriate; unknown acceptance evidence still blocks Done.

`ReservationObservation` binds a recovered `RunObservation` to full lineage,
nonce, worker and route. `RunObservation` carries run ID, state, timestamp,
evidence, authentication and substantive-work flag. Task IDs are not start proof.

The outbox retains event identity, destination/thread, required time, text, state,
provider reference and attempts. Events cover acknowledgement, admission, start,
return, review, completion, escalation, delivery, reconciliation, revision and
rejected evidence. Missing markers can be repaired. Delayed intermediate reports
state the current job status; historical Done/Cancelled facts remain visible.
Fake `activity` and `attention` destinations are logical names, not live IDs.

## Operational limits

- State, duplicate indexes, acknowledgements and outbox are process-local. No
  durable restart, distributed lock, cross-system transaction, exactly-once
  delivery, acknowledgement SLA or ten-minute watchdog is claimed. Control points
  and observations support coordinator-driven checks; no scheduler is installed.
- Deduplication uses exact source first, then normalized outcome/target/scope/parent
  against all retained jobs. It is not a natural-language semantic classifier.
  The coordinator must identify differently worded equivalent outcomes before
  allocating IDs. IDs are never recycled inside the retained store.
- A durable codec reconstructing the internal aggregate from J/M/Q is future
  work; `from_cells` restores only the row. Large audit storage and live cell-size
  limits remain untested.
- This trusted coordinator library is not a security service. Private methods,
  repository implementations and caller attestations are not a boundary against
  hostile Python code. Future adapters must authenticate and enforce permissions.
- Synthetic passes cannot prove physical stop, actual message delivery,
  deployment, external integration or parent outcome completion. There is no
  parent write API. Child Done never closes a Master Workplan outcome.
- Conflicting duplicates are audited and completed work is reopened for review
  where appropriate. Changes to already returned work require a corrective
  attempt; progressive rewrites of a return are intentionally rejected.

Recommendation only; not assigned: build an offline 17-column aggregate codec
and restart/recovery contract tests using fixtures, preserving execution and
delivery identities without live connections. No follow-on job is created.

## AJ-0009 — exclusive Sheets Writer v1 candidate

AJ-0009 ImplementationRevision 3 adds an **optional local, journaled writer** behind the accepted
`JobRepository` interface. The original in-memory engine and its 58 tests remain
unchanged. Its historical acceptance documents above describe AJ-0007 only.
No live Sheets or Slack adapter is included, and the default dispatcher store
has not been replaced automatically.

`SheetsWriter` exposes deterministic create/update, exact 17-cell readback,
explicit SUCCESS/FAILED/UNCERTAIN, restart reconciliation, retirement/handoff,
and one shared changed-condition retry/fallback budget. `WriterJournal` uses
SQLite and a POSIX advisory lock on one shared local path. `SheetsRepository`
bridges the existing dispatcher with a closed JSON codec for local aggregate
state; it does not claim to import a complete aggregate from existing live cells.

Run all existing and new tests with external I/O blocked:

```sh
python3 -m tests.offline_suite
python3 -m tests.simulate
python3 -m compileall -q dispatcher tests
```

See [current writer interface and limits](docs/AJ-0009-sheets-writer.md),
[ImplementationRevision 3 corrections and test map](docs/AJ-0009-implementation-revision-3.md),
and [current component results](docs/AJ-0009-ir3-results.json). Revision 1 passed
its original suite but **failed independent permission-boundary probes**; its
[original verification](docs/AJ-0009-verification.md),
[original results](docs/AJ-0009-results.json), complete candidate archive and
failed-review evidence remain preserved. Revision 2 passed 131 tests but failed
the independent F2 renewal-scope probe; its complete candidate and failed review
are also retained under `docs/history`. Revision 3 binds renewal applicability
to exact job, sources, intended values and original authority at every mutation
gate; it does not change the shared recovery budget. These are local/mock results, not live
integration or unattended-operation acceptance.

## AJ-0010 — bounded Google Sheets transport candidate

AJ-0010 adds a native Google Drive MCP request/response adapter, a session-bound
agent tool bridge, durable exact-call receipts, and an isolated sandbox fixture
planner. It requires the existing authorised connector; it contains no network
client, credentials or authentication installer. The accepted writer and F1/F2
authority/recovery controls are unchanged.

The existing connector was exercised through the Python bridge in one private
sandbox. One synthetic create and one update each retained their original native
acknowledgement and passed exact 17-cell, neighbour, formatting, validation and
permission readback. A separate process reconciled the same journals with zero
additional writes. The positive path settles the acknowledged invocation;
missing/ambiguous acknowledgements remain UNCERTAIN even when cells match.
This bounded, agent-mediated result does not establish CAS, physical exactly-once,
direct Python authentication, production readiness or unattended operation.

See [AJ-0010 scope, evidence and limitations](docs/AJ-0010-google-sheets-sandbox.md),
[actual connection evidence](docs/AJ-0010-connection-evidence.json),
[exact saved fixture](docs/AJ-0010-fixture-plan.json),
[live verification](docs/AJ-0010-live/verification-result.json), and
[final offline results](docs/AJ-0010-final-tests.json). Run `python3 -B -m tests.offline_suite`
for all 193 tests, including the unchanged 152-test baseline and 41 new tests.
Commit/push remains gated on root acceptance of the final code/test/live evidence.
