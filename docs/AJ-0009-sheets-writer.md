# AJ-0009 exclusive Sheets Writer v1 — ImplementationRevision 3 interface

Lineage: **AJ-0009 / SpecRevision=1 / RunEpoch=1 / Attempt=1 /
Nonce=VA-SHEETS-0009-01**. ImplementationRevision **3** is separate from that
unchanged execution lineage. Correction authority: supplied Slack
`1791108457.730869`. Revisions 1 and 2 failed independent review; their complete
candidates, results and failing probes are preserved in [revision history](AJ-0009-implementation-revision-3.md).
Bounded implementation approval: Victor's Slack
message `1791107771.394749`, as supplied by the coordinator. Protocol recovery
requirements: supplied AJ-0008 Protocol v1.1.0 and Catalogue 1.0.0. This document
does not replace or edit that authoritative catalogue.

Base: `1057b5575f7cecb0da67295b6d0ea9308dc76c9c`, preserved branch
`aj-0007-dispatcher-adapter-v1`, repository
`Victoradex94/Command-Center-Gravity`. Implementation branch:
`aj-0009-sheets-writer-v1`. Candidate is **uncommitted**, pending coordinator
acceptance and explicit continuation before commit/push. No ledger mutation,
follow-on job, live connector, credential, installation or deployment is included.

## Files and boundaries

| Module | Responsibility |
| --- | --- |
| `dispatcher/sheets_writer.py` | Typed requests, outcomes, current row model, preflight, ownership, exact reconciliation, shared recovery budget and circuit events |
| `dispatcher/writer_journal.py` | SQLite FULL durable intents/evidence and advisory serialization spanning provider calls |
| `dispatcher/mock_sheets.py` | Separate persistent **local** provider fixture, fault injection and mock authority |
| `dispatcher/record_codec.py` | Versioned closed JSON encoding of local dispatcher aggregates; no pickle/dynamic class loading |
| `dispatcher/sheets_repository.py` | Implements the accepted `JobRepository` port without modifying the engine |

The original `AgentJob`, `Status`, `Dispatcher`, `InMemoryRepository`, adapters,
tests, and AJ-0007 history are unchanged. There are still exactly 17 A:Q cells and
seven statuses: Intake, Ready, Working, Review, Blocked, Done, Cancelled.
Outcome, ownership, incident and circuit states are internal controls, never new
job statuses. There is no Master Workplan write port.

## Coordinator API

Construct `SheetsWriter(journal, adapter, authority_reader, clock=...)` with one
configured, exact workbook/table scope. Only trusted coordinator code receives
this port. `claim(actor, authority_ref)` requires authenticated current root
authority, no active writer, and no unsettled operations, and returns a
`WriterToken(actor, epoch)`. A proxy uses the same exclusive port under root's
explicit scoped delegation. Caller attestations are not identity authentication.

`write(WriteRequest(...), token) -> WriteResult` accepts:

| Field | Meaning |
| --- | --- |
| `operation_id` | Stable incident/intent identity supplied before the first call; never regenerate to recover |
| `job_id` | Logical `AJ-...` ID; no row-number mutation API |
| `expected_revision` | `None` for create, positive current RecordRevision for update |
| `expected_lineage` | `None` for create; exact current typed `Lineage` for update |
| `intended_lineage` | Required typed Job ID / SpecRevision / RunEpoch / Attempt matching intended Q exactly |
| `lineage_change_ref` | Explicit authenticated lifecycle-decision reference when intended lineage changes |
| `cells` | Immutable tuple of all 17 intended string values; each at most 50,000 characters |
| `source_keys` | Nonempty unique canonical source identities; exact duplicate detection, preserving prior source history |
| `authority_ref` | Reference resolved by the injected current authority reader |
| `original_authority_ref` | For a fresh write using a renewal: the original stopped instruction covered by that attestation; blank for ordinary authority |
| `context_ref` | Reviewable authority/execution context evidence reference |
| `condition`, `route` | Verified stable safety context and authorized provider route |
| `aggregate` | Optional closed local dispatcher snapshot; never an 18th cell or another Sheet tab |

Q must contain exactly one positive token each for RecordRevision, SpecRevision,
RunEpoch and Attempt. RecordRevision advances by one; expected spec/run/attempt
must equal the current row before mutation, and intended lineage must equal Q.
Other Q text (nonce and historical information) is preserved.
The low-level writer preserves the entire supplied row exactly; the
repository bridge adds/updates only the RecordRevision token after the engine
has formed its intended row. It does not manufacture execution attempts.

An actual lineage change requires `AuthorityReader.inspect_lineage_change` to
return a `LineageChange` binding reference, scope, root actor, exact before/after
lineage, action, authentication and evidence. The writer checks the existing
engine's counter transformations: clarify increments SpecRevision; revise
increments SpecRevision and RunEpoch and resets Attempt to 1; reopen increments
RunEpoch and resets Attempt to 1; retry increments Attempt. Regressions and
mismatches are rejected, including raw writer calls. Full lifecycle readiness,
execution-effect, status and approval gates remain in the existing Dispatcher;
the authority adapter must attest the actual decision, not merely a reference string.
`SheetsRepository(..., lineage_change_reference=callback)` is the explicit bridge:
the coordinator callback maps `(before, after)` to the authenticated decision
reference after the engine's lifecycle command passes. It does not grant authority.

Each write checks exact header/scope, complete authoritative row index, duplicate
logical ID/source, current row/revision, source-history retention, status enum,
Needs Victor value, cell types/limits and the original transition graph. It
resolves one physical row and submits only A:Q values. Pending create positions
are reserved locally so another authorized independent create cannot occupy a
row where a late request may land. A create uses the next row after known and
reserved positions; no row insertion or sheet expansion is implemented.

Operation ID reuse with identical intent returns the recorded historical result
without submission. Different intent under that ID is a conflict. A different
operation/route/nonce for the same frozen Job ID or source is refused. Programmer
errors, stale writer tokens, identity collisions, explicit recovery gate failures
and journal I/O faults raise exceptions and never authorize a retry. A caller
must retain the original operation identity and reconcile after any infrastructure
exception that could follow intent persistence.

### Outcomes

* **SUCCESS:** authoritative settled application, no outstanding effects, complete
  duplicate-aware readback of all 17 cells and source identities exactly matches.
  An exception/timeout response cannot overrule a successful authoritative readback.
* **FAILED:** this call was locally rejected before any provider submission, or
  the exact provider attempt is authoritatively settled no-op with no outstanding
  effects and unchanged before-state. A failure response alone is insufficient.
* **UNCERTAIN:** intent exists but admission/effects/readback are unknown, active,
  partial, inconsistent or inaccessible. All duplicate-producing mutations for
  that logical ID/source and pending physical row are frozen.

A cached SUCCESS is a historical verification of that operation, not a promise
the row has never subsequently changed. `read(job_id)`/`snapshot()` supplies the
current row/revision; repository commits reread before every new write.

## Durability, restart and handoff

The journal commits full request, digest, before-state, target, actor/epoch,
authority/context, deterministic provider attempt ID (`operation/0` or `/1`),
and an UNCERTAIN intent **before** calling the adapter. Provider effects are
outside SQLite transactions. SQLite FULL commits and an advisory file lock cover
cooperating processes on the same supported local POSIX filesystem/path.
Each submission also records its effective authority reference; audit retains
both original and effective references when a reviewed renewal is used. Any
provider human-denial evidence fences that actual submission's authority.
ImplementationRevision 2 uses journal schema **2** with persistent permission
stops and renewal evidence. Schema-1 journals are rejected rather than silently
assuming their omitted denial history is safe. Any old-journal migration requires
separate reviewed reconciliation; none is implemented or performed here.

On restart:

1. Open the **same retained journal and provider scope**. Enumerate saved
   `operations` from `state()`; do not create a fresh journal to evade a freeze.
2. Call `reconcile(operation_id)` on every unresolved intent. This only inspects
   provider state and repairs local evidence/markers. It does not submit, claim,
   retry, change a row, or require revoked mutation authority to be reinstated.
3. Even an empty target or absent provider log remains UNKNOWN unless the provider
   can prove the original call cannot later apply. Partial effects remain frozen.
4. A replacement instance cannot mutate using a copied token. After every
   outstanding write settles, root explicitly calls
   `retire(old_token, authority_ref, evidence)`, then `claim(...)` for a fresh epoch.
   The old object/token is fenced. Claim is never an automatic lease takeover.
5. Adopt verified success. For a genuine resolved no-op, separately evaluate the
   one authorized changed-condition recovery; never invoke `write` as a retry.

The instance/PID mutation gate also blocks a forked copy from continuing an old
claim. The administrative token can be read from the journal for root retirement;
it is not a secret credential. Neither Python private fields nor journal files
are a security boundary against hostile code or arbitrary file edits.

## Recovery and circuit hooks

`recover(operation_id, RecoveryChange(...), token)` is the **only** mutating
recovery entry, for both the original route and fallback. It first re-inspects
the original attempt and exact target. A late success is adopted with zero replay.
Unknown, active, partial, mismatched or unresolved-permission cases cannot submit.

`RecoveryChange` binds original operation/digest/scope/condition, an evidenced
different condition and verified target/route/capability/access, authority reference,
and a clocked check no older than 60 seconds. The injected authority reader must
affirm both the effective original authority (or its explicitly reviewed renewal)
and recovery authority, including final preflight. Evidence is trusted coordinator
attestation; a string difference alone is not evidence of a real condition change.
Rephrasing, another writer, or waiting on a static failure does not qualify.

One recovery is charged durably **before** submission and shared across retries,
fallbacks, restarts and writer handoffs. Failure or uncertainty after that recovery
opens the circuit. Repeated observation of the same attempt does not increment
recurrence or emit another `circuit_open` event. New occurrence IDs do not reset
the incident. A matching open fingerprint also blocks another incident's recovery.

Fingerprints hash action family, configured target scope, primary failure class,
normalized signal, stable safety context, and initial effects uncertainty category.
Occurrence ID, Job ID, timestamps and actor/session names are stored separately.
Normalized codes prevent transport wording/request IDs from manufacturing new
failure families. The initial fingerprint/components and failed-attempt history
survive reconciliation. Recurrence counts distinct attempts in the same family;
any failed/uncertain recovery opens the circuit even if its failure family differs.

Authenticated human cancellation, denial or observed authority revocation is
saved immediately to a journal-wide permission-stop registry, even before any
provider submission and even if preflight later fails or the process dies.
Stops bind original authority reference plus logical Job ID/source identities.
The same reference cannot become usable because a later callback says valid;
changing operation, job alias with the same source, source with the same job,
context, route or writer does not clear the stop. An independently authorized
unrelated target using a separate reference is not blocked. Administrative
retirement/claim can proceed under current root authority after settlement,
but never restores stopped ledger-mutation authority.
An unverified human attribution leaves provenance
unresolved until authoritative evidence clarifies it. Generic tool cancellation
text by itself establishes neither revocation nor no-op; valid authority plus
authoritative settled no-op and verified change can use the one shared budget.

Explicit renewal interface: configure an authentic new instruction in
`AuthorityReader.inspect_renewal(reference, scope, root)` as `AuthorityRenewal`,
binding a **distinct new reference**, exact job/source set, `original_authority_ref`,
`intent_digest`, every matching stop ID, authenticated root review and evidence.
`WriteRequest.intent_digest` hashes the job, expected revision, all intended 17
cells, exact source tuple, aggregate snapshot, expected/intended lineage and
lineage-change reference. Occurrence ID, route, context and authority labels are
excluded so a fresh context cannot alter the granted outcome. These fields do not
replace the full immutable operation digest or provider idempotency evidence.
`review_renewal(reference, token)`
validates and durably audits that attestation. It preserves every old stop and
old reference; only the new reference may cover the enumerated stops for that
exact target. At least one stop must identify the stated original authority;
targeted stops must match both job and exact source set. Every mutation authority
gate checks the recorded scope **even when no local stop matches**. Renewal scope
is checked before replacing original recovery authority and again at the ordinary
preflight gates. It cannot supply unrelated recovery-condition or lineage authority.
No mutable valid/invalid callback alone is a renewal. Renewal
references are immutable; subsequent denial of a renewed reference requires
another explicit review. For an initial never-submitted rejection, a fresh
corrected request may use that reviewed reference and must also supply its bound
`original_authority_ref`. An existing submitted incident
must use `recover` with the reviewed reference in `RecoveryChange.authority_ref`;
it keeps the original immutable request/digest, incident and shared budget.

**Trusted attestation boundary.** `Authority.kind` explicitly distinguishes
`ordinary` and `renewal`; unknown kinds are rejected. The authority adapter must
authenticate the real instruction, classify every renewal as such, verify current
revocations and compute/check its binding from the actual approved mutation.
Arbitrary reference strings, caller-computed hashes and `authenticated=True` are
not independent proof of permission. An unreviewed renewal cannot be treated as
an ordinary grant, and a recorded renewal cannot be reclassified to escape its
scope. Targeted renewals do not authorize writer claim/retirement; use the separate
current ordinary root administrative authority. `MockAuthority` is deliberately
synthetic: it treats unconfigured references as ordinary valid grants for fixtures,
not as a production authentication implementation. A malicious or incorrect trusted
authority adapter remains outside this local protocol's authentication guarantees.

Old IR2 renewal records without original-authority/intent bindings fail closed;
there is no implicit upgrade or journal migration. Historical evidence is retained.
`SheetsRepository` propagates its configured reference through these same gates;
it does not infer an original reference or mint a renewal. Explicit scoped renewal
and incident recovery are coordinator operations on the writer interface.

Renewal does **not** reconcile effects, bypass lineage/readback gates, reset the
shared budget/circuit, or permit another fallback. `permission_stop` on an
operation is historical evidence; the registry and exact renewal binding govern
current permission. There is no automatic reset, second recovery, pattern
promotion, protocol/code mutation or scheduler. Mutation beyond an exhausted
budget still needs separately reviewed future resume design. Read-only
reconciliation remains available.
Late success resolves the operation without replay; any open circuit is retained
as historical/conservative scope protection until root-reviewed reset work.

Audit events include `write_attempted`, sanitized transport signal type,
`operation_observed`, `authoritative_reconciliation` with exact snapshot,
`verified_outcome`, `mutation_frozen`, `permission_stop`, `authority_renewed`,
`lineage_change_verified`, `recovery_authorized`,
`circuit_open`, `writer_retired` and `writer_claimed`. Sequence/time/operation IDs
support external event deduplication. Audit events do not send messages or edit
the shared recovery catalogue. No event is an execution acknowledgement.

## Future Google Sheets adapter contract — documentation only

Implement the `SheetsAdapter` protocol in a separately authorized scope:

* `snapshot(scope) -> Snapshot`: verify exact workbook/tab and A1:Q1; supply a
  complete authoritative ID/source index plus exact 17-cell rows, physical positions,
  current Q revisions and evidence. Canonical source keys must be derived and
  authenticated from the accepted existing J/source convention; never blindly
  trust a request's sidecar index. Raw source text equivalence is not NLP deduplication.
* `submit(Submission)`: issue **one** narrowly scoped values-only A:Q request with
  RAW/literal value semantics, preserving validation, formats, headers, other rows
  and tabs. No hidden SDK retries. Respect the configured current sole writer and
  authority. Persist/expose any actual provider request identity and result path.
  Resolve a changed row position before application or reject. Do not claim atomic
  compare-and-swap from a read followed by a Sheets values update.
* `inspect(Submission) -> Observation`: bind evidence to exact attempt/digest/scope.
  Report APPLIED/NOOP/PARTIAL/ACTIVE/UNKNOWN, settlement, all-effect resolution,
  authenticated cancellation provenance and normalized failure signal. An empty
  row or missing log is not settlement. If Google/tool infrastructure cannot prove
  finality, return UNKNOWN indefinitely and escalate the evidence gap; do not
  fabricate a provider idempotency guarantee from the client operation ID.
* Implement `AuthorityReader.inspect` from authentic current instructions and
  exposed approval/revocation provenance, plus explicit `inspect_renewal` and
  `inspect_lineage_change` attestations when those operations are requested.
  MockAuthority is a permissive local
  fixture only and must never be used for live authorization.

The row schema is unchanged; positive RecordRevision/source extraction and full
aggregate import for legacy rows require a separately reviewed compatibility
plan. This candidate rejects missing/malformed revisions rather than silently
bootstrapping a live ledger. A complete live J/M/Q aggregate import is not built.

## Explicit limitations

* This is local fault simulation, not live Sheets integration, provider exactly-once,
  a distributed lock, a remote CAS, cross-system transaction or unattended reliability.
* Same-path advisory locks serialize cooperating processes on **one POSIX host**.
  Separate journal paths, noncooperating writers, other hosts, network filesystems,
  journal loss/rollback, external Sheet edits and out-of-band calls are not fenced.
  Use one controlled writer deployment/path; never restore an old journal and assume
  its ownership or budgets are current. A live design must resolve these risks first.
* The mock has an atomic SQLite provider log and stronger settlement/CAS evidence
  than a Sheets values API. It intentionally rejects duplicate attempt submissions
  so tests cannot pass by relying on silent provider deduplication.
  Its persistent structural fixture includes seven-status/Yes-No validation,
  formatting, row heights/visibility, grid/table/filter bounds and neighbouring
  values outside A:Q. The submission port can address only values in one existing
  A:Q row; it has no format/validation/row-insertion fields. Tests compare this
  metadata across create/update, late application, rejection, partial effects,
  cancellation, crash and reconciliation. This is mock structural evidence only,
  not Google Sheets formatting behavior.
* The codec preserves full aggregates only in a trusted local journal sidecar.
  Loss of that sidecar, externally edited rows or an existing unimported ledger
  block repository adoption. Pre-job dispatcher acknowledgement state remains in
  memory; Slack/executor delivery restart safety is a different milestone.
* The journal rewrites its JSON state in a SQLite transaction and retains audit
  history without compaction. Large-ledger performance, hostile/corrupt file
  recovery, physical power loss/storage honesty, live cell limits and real format/
  validation preservation have not been established by these tests.
* The writer's low-level status transition check does not replace Dispatcher
  acceptance, parent mapping, assignment, gate, human-approval or execution rules.
  Use the repository through the accepted coordinator engine for those decisions.

## Next bounded live-test recommendation — not an assignment

After candidate review, separately authorized preservation, and separate adapter
implementation/approval, use a **designated non-production workbook** with the
exact 17 headers and seven validations. Root explicitly retires every former
writer, confirms settled outstanding calls, and names one writer and two scratch
row positions. Bound the test to **one create and one update** of a single stable
synthetic logical ID with exact pre/post 17-cell, revision, source, neighbouring
row, validation and format readback. Persist operation identities before each call.
Then restart and inspect the existing operations; perform **zero additional
mutations** for response-loss/restart observation. If settlement is unavailable,
freeze and report UNKNOWN. No production Agent Jobs/Master Workplan writes,
dispatch, message delivery, permission changes, automatic retry, follow-on job or
automatic cleanup; retain the scratch evidence for coordinator review. Approve
the concrete workbook, range, adapter and authority separately before any live call.
