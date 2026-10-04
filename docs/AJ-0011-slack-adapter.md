# AJ-0011 Slack command and notification boundary

Candidate for root acceptance; uncommitted and unpushed. Base:
`9f40ada529481dcc91d81cf286c0df1c4ccbf5c8` on preserved
`aj-0010-google-sheets-sandbox`; new branch `aj-0011-slack-adapter`.
Lineage: AJ-0011 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
Nonce VA-SLACK-0011-01. Root owns dispatch and the real Agent Jobs ledger.

## Scope and architecture

`dispatcher/slack.py` adds a standard-library-only, synchronous, mock-provider
boundary around the accepted Dispatcher and JobRepository ports. No accepted core,
exclusive Sheets writer, codec, 17-column contract, or seven statuses change.
Protocol v1.1 and Recovery Catalogue principles are implemented as Slack sidecar
controls; these are not new job statuses or a claim of full live certification.

`SlackJournal` persists command fingerprints, reserved/applied outcomes, immutable
notification identities/content, attempts, provider references, incidents and one
shared correction budget per job (per command for acknowledgements). SQLite commits
and FULL synchronous mode protect local reservations. Store this file on durable
local storage. Backup/loss recovery, multi-host leadership, journal compaction and
host failover are outside this milestone. One exclusive coordinator owns this
boundary; SQLite serialization is not distributed leader election.

`Command` is a normalized typed instruction, not a natural-language parser. The
trusted coordinator must construct a `Grant` bound to the exact command digest and
provide an independent `verify_grant` implementation. Its callback is a trusted
port, not something an incoming message may supply. Source `authenticated=True`,
display names, quoted instructions, agent claims and raw Slack fields alone grant
nothing. Fixtures grant only simulated owner authority. Only configured workspace,
owner and command channel are eligible. No observer from unrelated channels gains
intake authority. `observe` records an authorised nonactionable receipt without a
job. Explicit worker assignment is required for intake/revision.

Supported commands: intake, observe, revise, cancel, pause (including withdrawal).
Edits of an existing source require explicit revision. Duplicate source/version
with changed payload is rejected. Core semantic identity matching links repeated
instructions to existing work; it does not infer natural-language equivalence.
Cancellation fences returns without claiming physical termination. Pause retains
uncertain execution for reconciliation. Revision uses core old-run reconciliation,
lineage increments and stale-return rejection. Resume/retry/reopen/clarify remain
explicit coordinator core operations; there is no automatic successor chain.

Core readiness/dispatch/start/receive/complete continue to enforce route authority,
explicit worker selection, admission versus verified substantive activity, exact
worker/run/nonce returns, Full/Partial/Blocked classification and independent
completion verification. Neither acknowledgements nor Slack posts start a worker.
No Slack text is automatically executed. No bot-to-bot triggering is assumed.

## Restart and delivery rules

Command reservation and acknowledgement intent commit before core mutation. The
core retains canonical activity in its existing repository aggregate. Because the
Slack journal and core repository are separate stores, a crash between commits
leaves a reserved command. `reconcile_command` adopts exact canonical source or
fingerprinted mutation evidence without replay. If evidence is absent/uncertain,
root must reconcile it; the adapter does not reset or retry the command. Invalid
or failed post-reservation commands can therefore remain stopped for root review.

`sync(job_id)` deterministically rebuilds notification intents from canonical
material events. Returns, completion, revision, blocking and cancellation receive
an activity item and one direct owner-DM item per event. Genuine decisions also
receive a top-level attention item containing the original decision, recommendation,
consequence and deadline. Routine admission/start/progress emit no Slack chatter.
Events are explicitly historical so a delayed send cannot masquerade as current
status. A blocked return may produce distinct transition and return events; each
has its own canonical identity. Core legacy notification markers remain intact but
must not also be drained by a live integration: this boundary owns Slack delivery.

`deliver` inspects the exact key/destination/thread/content before sending. It
persists `sending` before invoking the provider. Only exact readback with a provider
reference becomes `verified`; `accepted` and `unknown` remain unsurfaced. A thread
reply cannot satisfy a top-level attention item. Human read always remains unknown.
After crash/timeout, original destination evidence verifies success without replay.
Unknown lookup never permits a send. Even authoritative absence after an attempted
send requires explicit bounded recovery; positive absence cannot be inferred from
an incomplete search or eventual-consistency delay.

`audit_surface` fingerprints `material-event-recorded-but-not-surfaced`; it is an
explicit control-point audit, not an unattended scheduler. Repeated polls do not
count as recurrence. `recover` requires a trusted root callback plus changed-condition
evidence. Retry/fallback share one budget for the group; destinations cannot change
and uncertain sends still require reconciliation. Failure after correction opens
the coordination circuit, blocking further sends for that group. Later successful
readback remains allowed and never erases the circuit or budget. An acknowledgement
failure uses the same conservative mechanism under its command group. Operators
must audit pending acknowledgements and material events at the agreed control point;
no delivery SLA or automatic escalation timer is implemented.

## Provider limits and future live gates

No Slack SDK/client, request-signature verifier, HTTP endpoint, credentials, secrets,
permission changes, real sends, live Sheets writes, deployment or scheduler exists
in this change. Configuration IDs are fixtures only: command C0C6331GE0P, activity
C0C7CRRJDLY, attention C0C6N5H1QCU, owner DM D0C6J9ZKF4J, owner U0C6LCCH9QR,
workspace T0C63317YDV. No live Slack documentation lookup or Slack call was needed
for this local port contract; current provider capabilities must be checked before
live adapter design.

A separately authorised live step must validate signing/replay checks, exact owner
scope and grant revocation, provider metadata integrity, complete destination lookup,
retention/pagination/permissions, top-level posts, DM accessibility, rate limits and
message-size/rendering/mention escaping. It must safely render structured untrusted
text (including `<@...>` and links), define conclusive negative evidence and prohibit
automatic retry on uncertainty. It must validate journaling durability, single-writer
ownership, permission withdrawal during pending sends, and independently inspect
original-message provenance rather than trusting an echoed key from another actor.
Slack provider acceptance is not destination readback or human reading. Exactly-once
Slack delivery and Slack bot-to-bot triggering are expressly not guaranteed. A live
integration must not enable the existing generic Dispatcher delivery path alongside
this outbox, which would duplicate notifications.

## Verification and independent review

All new tests use local mock providers and temporary SQLite files. The full suite
runs through `python -m tests.offline_suite`, which installs an audit hook rejecting
network and subprocess launches (a test guard, not a hostile-code security sandbox).
The baseline has 193 tests; final counts and retained stdout/stderr are in
`AJ-0011-evidence/`. Integration tests exercise the accepted exclusive Sheets writer
and persistent mock Sheets repository with a restarted Dispatcher. No real ledger
was edited. Independent probes, original findings and final disposition are retained
in `AJ-0011-review/`. Artifact hashes are in `AJ-0011-manifest.json`.

Recommended next bounded step: root review and acceptance of this candidate, then
feature-only commit/push preservation already authorised after acceptance. A future
live-adapter design is a separate gate; no follow-on job is created here.
