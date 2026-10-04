# AJ-0012 bounded live result — pending root acceptance

Completed the authorised three-message coordinator-mediated test and separate-process
restart. This supersedes the earlier blocked-route result for this same job. No fourth
request, replay, message edit/delete, executor send, ledger mutation, commit or push.
Root's unrelated AJ14 ledger uncertainty remains untouched.

Branch `aj-0012-controlled-slack`; accepted base
`a845dd7dc36edaaa029f4d73147a3d4a4bc197b1` on `aj-0011-slack-adapter`.
Lineage: AJ-0012 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
Nonce VA-LIVE-SLACK-0012-01. Root owns ledger and dispatch.

## Live operations

The owner explicitly approved root's existing verified bot route in thread
1791138860.804219, reply 1791138961.408669. Root invoked
`user_message.send_message(channel=slack)` once per durable request as bot
U0C6C7V10P5 in workspace T0C63317YDV. Executor never sent as Victor and never
acquired bot credentials. Root supplied original send responses and independent
actual destination reads; executor retained and checked them before advancing.

Original event: `AJ-0012/1/1/1/VA-LIVE-SLACK-0012-01/synthetic-transport`.
Operations append `/activity`, `/attention`, `/owner`; each attempt appends
`/send-attempt-1`. Each exact original body is `Synthetic test — no action required. `
followed by the operation ID. Every thread is empty; acceptance thread_id is null.
Original binding SHA256:
`be9def73448d3aed229ab458a1b54891645a4dccccb40a40f153d6eb3ce5a58c`.

| Operation | Exact destination | Actual Slack message timestamp | Request SHA256 |
|---|---|---|---|
| activity | C0C7CRRJDLY | 1791139471.957359 | 230a7797b0b98dcbc2b193256f69baf321a1b4adbffb697edb5f4f755cad990f |
| attention | C0C6N5H1QCU | 1791139693.278939 | 881d023b609325e9e4dd630a8ce8d7cdf6d976c94a92a7369ad9d3954b4272bf |
| owner | D0C6J9ZKF4J | 1791139894.566079 | fcf4f1f06cd20c3816ac26f925e7737ede038a51252fe2dbb25c494bf83e5547 |

Provider references are `slack:<destination>::<timestamp>` exactly as returned.
Actual source-returned permalinks, obtained by a subsequent read-only executor search:

- https://vicadexcommandcenter.slack.com/archives/C0C7CRRJDLY/p1791139471957359
- https://vicadexcommandcenter.slack.com/archives/C0C6N5H1QCU/p1791139693278939
- https://vicadexcommandcenter.slack.com/archives/D0C6J9ZKF4J/p1791139894566079

The search returned exactly those three matches and end-of-results, confirming fresh
positive presence after restart and DM participants bot/owner U0C6LCCH9QR. It does
not establish globally exhaustive duplicate absence beyond the query/index.

All three operations are `verified`, each attempts=1, transport reservation calls=1,
with exactly three original receipt/readback evidence pairs. Root reports exactly
three provider sends. Acceptance, destination presence and human reading remain
separate: acceptance and presence are proven; human_read remains `unknown` for all.
The DM readback is a JSON-wrapped rendered record; JSON decoding resolves escaped
slashes/unicode, and exact full-record matching confirms destination/author/TS/body.
No synthetic fixture is used as live evidence.

## Restart and safety

Reconciliation process PID 1463 closed the same durable journal after the third
receipt. Separate process PID 1472 reopened it, checked all three request digests,
original archived bindings, exact destinations/content/thread, actual response
bindings and counters, then reconciled each through unchanged SlackBoundary.deliver.
The send callback was replaced with a fail-on-call guard. All three returned verified;
prepare_next returned None; zero callback calls and zero new requests. Network and
subprocess I/O were blocked during this restart process.

Both journal bytes and logical state stayed unchanged. Journal SHA256:
`bf3b00c1f119b6e4500efe89ebf071064fdc17b3af4b156a2de9e2a0721a1fbf`.
Restart used retained authentic destination evidence; the separate subsequent executor
search supplied fresh positive presence, without any send. Zero duplicate sends in
this controlled run is supported by the three single-use root dispatches plus zero
restart sends; this is not an absolute Slack exactly-once guarantee.

The original adapter/core/recovery files are unchanged. New transport and handoff
modules enforce exact binding, pre-effect reservation, sequential requests, fresh
permission checks, uncertain-result freezes, retained originals and no request replay.
The accepted v1.1 shared recovery budget remains intact; this bounded bridge is stricter
and never generates a corrective fourth request. No real task/core job was created.

## Tests and independent review

Final commands and retained logs:

- `python -m tests.offline_suite`: 236 passed (215 original + 21 new tests).
- Original AJ-0011 probes via runpy with tests.offline_suite.reject_external: 8 passed.
- `PYTHONPATH=. python docs/AJ-0012-review/probes.py`: 6 independent probes passed.
- `PYTHONPATH=. python docs/AJ-0012-review/bridge-probes.py`: 7 independent probes passed.
- `PYTHONPATH=. python docs/AJ-0012-evidence/restart-verification.py`: actual-journal restart passed.

Full tests and all 21 probes are offline/network-blocked. Fault/crash simulations use
temporary journals and mock receipts; actual operation evidence lives only in the
explicit root response/readback artifacts and shared journal. Independent review of
bridge, each receipt phase and final restart is retained under AJ-0012-review.

## Limits and preservation

This is a trusted, single-coordinator, agent-mediated request/response bridge, not
executor bot credentials, a generic authenticated Slack SDK, distributed leadership,
an unattended service or production rollout. Root is the dispatch and normalization
provenance authority; executor independently checked returned messages via its existing
read-only connector. Root's send responses have no sender field; actual readbacks
corroborate the approved sender. The root transport exposes no tested idempotency key
or human-read guarantee; no live rate-limit/retry behavior was exercised. Raw response
schemas differ for channel and DM reads, and there is no generic schema parser claimed.
No new access route, credentials or permissions were acquired.

Earlier manifests/reports are phase snapshots; the shared prepared-journal.sqlite
advanced intentionally. Pre-handoff bytes are separately archived. The final manifest
lists current exact files/hashes, including those historical artifacts. Candidate
remains uncommitted/unpushed, pending root acceptance before approved feature-only
preservation. No main merge or successor is requested.
