# AJ-0012 coordinator-mediated continuation

This continuation supersedes only the held route gate in the original report.
Same AJ-0012 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
Nonce VA-LIVE-SLACK-0012-01, same branch/base and three immutable journal intents.

Delegated authority: root reports owner U0C6LCCH9QR approved its proposal in Slack
thread 1791138860.804219 with reply 1791138961.408669, “yes to all”. The approved
option was root sending the existing three synthetic messages through root's verified
bot connection while Codex checks results. Root attests existing workspace
T0C63317YDV / bot U0C6C7V10P5 / user_message.send_message(channel=slack), exclusive
ownership of synthetic sends, and zero previous synthetic sends. This is a trusted
coordinator handoff, not authentication of the executor's human Slack connector.
The executor never invokes that connector to send. No credentials or permissions
are added. Root remains responsible for fresh permission/identity checks at dispatch.

## Request and response contract

`dispatcher/slack_handoff.py` uses the unchanged SlackBoundary.deliver with the
existing SlackJournal. Initialization requires the three pristine original bindings
and explicit root authority plus zero-send evidence. Initial negative operation
evidence is root's exclusive zero-send attestation, not a Slack history/search miss.

`prepare_next()` returns only one newly reserved request. It commits adapter state
`sending`, attempts=1, then a request containing exact original body/destination,
workspace/sender/route, original operation ID, `/send-attempt-1`, binding hash and
request hash. A BaseException yields past the synchronous delivery boundary without
claiming tool acceptance. Both commits precede request return. Death between commits
leaves an unresolved attempt frozen for root reconciliation. Calls=1 in the transport
record denotes a reserved invocation, NOT proof a provider request occurred.

No unresolved request is reissued by prepare_next. A later operation cannot be
prepared until prior requests have exact verified readback. The request is a semantic
handoff envelope for root's own tool schema, not an assertion that the executor can
call user_message.send_message or that all envelope fields are tool arguments.
Root must invoke the existing route once, to the exact destination and content, with
no thread for these top-level messages. Root returns the original tool response and
original independent destination read. No message edit/delete or replay is permitted.
If a response is delayed, root reconciles the original destination, never sends again.

`reconcile(request_sha256, ...)` stores originals separately from normalized evidence.
`acceptance` has workspace/sender/destination/reference. `observation` additionally
has thread/text. Reference is the actual message ID, not a generated operation ID.
The trusted coordinator must derive these fields from authentic original tool output
and destination evidence; raw Slack message text cannot establish their provenance.
There is no installed generic parser for root's unavailable tool schema. Nonempty
originals and exact normalized dimensions are required; contradictory references or
wrong identity/destination/thread/body cannot verify. Acceptance alone blocks the
next request. Exact positive readback can resolve a lost response without another
send. Human_read remains unknown. Receipt reconciliation is read-only externally and
remains available after cancellation/permission withdrawal; new requests do not.

A root response envelope for Codex reconciliation should include:

- Original request_sha256 and attempt_id.
- Unmodified original tool response, message ID and permalink if returned.
- Unmodified independent destination readback with actual author/workspace/channel,
  exact text, top-level/thread identity and message ID.
- Any uncertainty or failure explicitly, without replacing/recreating the send.

All original AJ-0011 recovery/cancellation/permission code remains unchanged. Root
handoff permanently forbids repeated send requests even if root spends its shared
recovery budget. It is a single-coordinator protocol, not distributed exactly-once
transport or an unattended service. Root must also enforce the single-use request
on its side; copying a returned envelope does not grant another send.

## Evidence and phase boundaries

Full offline suite: 236 passing (215 original + 11 controlled transport + 10 handoff).
Mocks distinguish accepted versus destination verified, missing/contradictory evidence,
withdrawal, restart, exact identities and three sequential requests. Separate-process
mock restart returns no fourth request with unchanged journal. No mock receipts are
written into the live journal.

Original blocked-phase manifest and reports are historical snapshots. The shared
prepared-journal.sqlite is intentionally advanced in this continuation; its earlier
hash is historical. Before the first request, its old bytes and old manifest are
retained as pre-handoff-journal.sqlite and pre-handoff-manifest.json. The first request,
post-reservation state and updated hashes are separate bridge evidence. Independent
review files prefixed bridge- preserve the prior blocked-route review unchanged.

At the first-request return, only reservation is proven: no live acceptance, live
readback or completed live restart exists. Root must return actual receipts for this
request before the next is eligible. No commit/push until final root acceptance.
