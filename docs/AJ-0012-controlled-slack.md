# AJ-0012 blocked live verification / offline candidate

Job AJ-0012 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
Nonce VA-LIVE-SLACK-0012-01. New branch `aj-0012-controlled-slack` starts at
accepted `a845dd7dc36edaaa029f4d73147a3d4a4bc197b1` from `aj-0011-slack-adapter`.
Initial checkout was README-only; exact preserved feature was fetched and verified.
No local AGENTS.md or .agents/skills was present. Root owns ledger and dispatch.

## Result and exact gate

Live result: BLOCKED BEFORE SEND. Zero synthetic sends, zero accepted test receipts,
zero test-message IDs/permalinks, zero actual test destination-presence readbacks.
Human reading is unknown. No commit/push, ledger mutation, merge, deployment,
credential acquisition, permission request, alternate route or successor occurred.

Supported executor tools are `mcp__codex_apps__slack_slack_list_workspaces`,
`slack_slack_read_user_profile`, `slack_slack_read_channel` and
`slack_slack_send_message` under that same namespace. Workspace read confirms
T0C63317YDV. Default current-user read confirms Victor U0C6LCCH9QR, Bot No.
The send schema provides destination/message/thread controls but no sender selector
or sender-authentication operation. Activity history contains dot bot U0C6C7V10P5
messages, including root's ordinary AJ-0012 admission. Those historical messages do
not prove which identity this executor's next send would use. The current-user
profile likewise does not conclusively establish send behavior: it establishes
Victor as the read identity, not dot bot as the sending identity.

The unmet gate is a supported read-only verification binding this executor's
existing send route to workspace T0C63317YDV and dot bot U0C6C7V10P5. No probe send
is allowed to establish that identity. No connector denial was encountered or
bypassed. No new credentials/permissions/route were sought. Root must resolve this
gate within the already-authorised route before any live step; this candidate does
not claim a working or certified real transport.

## Safe implementation

`dispatcher/slack_controlled.py` adds a bounded callback provider around the
unchanged accepted SlackBoundary. `bind_synthetic` atomically binds exactly three
immutable identities, contents and destinations in the same SlackJournal, without
creating a core job or assignment. Event identity is
`AJ-0012/1/1/1/VA-LIVE-SLACK-0012-01/synthetic-transport`; operation suffixes:

- `/activity`: C0C7CRRJDLY
- `/attention`: C0C6N5H1QCU, top level
- `/owner`: D0C6J9ZKF4J, verified intended owner U0C6LCCH9QR

All three have empty thread and exact content `Synthetic test — no action required. `
followed by their full operation key. No mentions, approval request or instruction.

The wrapper checks exact workspace, sender and route plus a trusted identity verifier
and fresh cancellation/permission callback. It persists a transport reservation
before calling the send port, retains original callback responses and normalized
read evidence, and forbids re-invocation for that operation permanently. Exact
readback must match sender, workspace, destination, key, thread and text. Incomplete
or uncertain absence never permits a send. Even authoritative absence after a
transport reservation remains unknown, preserving uncertain-delivery freezes.
The accepted shared recovery budget/circuit remains unchanged; this job's stricter
three-call ceiling allows no corrective send. There is no automatic retry.

Callbacks are trusted coordinator ports, not an implemented Slack tool bridge or
authentication parser. A future supported agent-mediated bridge must supply original
tool responses, validate provenance, normalize exact readback and prove complete
negative coverage. No such callbacks are installed for live use here. In particular,
plain historical text, supplied identity strings, or boolean flags in Slack payloads
are not authentication. A trusted callback can lie; this module is not a security
boundary against a malicious coordinator. A send callback must invoke its provider
at most once. Single exclusive coordinator and durable local SQLite remain required.

## Provider limits and evidence

The supported tool describes 5000 characters per text element, Markdown rendering,
no Slack Connect sends, and optional thread replies. It exposes no client idempotency
key, native exactly-once guarantee, read receipt, or sender selector. Channel reads
are paginated (1–100 messages); a partial page or search miss cannot prove absence.
No live rate-limit, write permission, bot identity, DM access or render behavior was
proven. Original read responses are preserved in AJ-0012-evidence; the reviewer
independently retained their own identity/workspace reads and tool schemas. Existing
activity messages are preflight evidence only, not synthetic test receipts.

The prepared journal contains three pending intents and no operations or attempts.
A second process reopened that same journal and confirmed zero sends. This is
pre-dispatch durability evidence only. The separate-process *mock* test verifies
three simulated receipts followed by zero additional sends. Neither is the requested
live restart verification, which remains unexecuted behind the identity gate.

## Verification

Commands from repository root:

- `python -m tests.offline_suite` before changes: 215 passed.
- `python -m tests.offline_suite` after changes: 226 passed (215 original + 11 new).
- Original AJ-0011 independent probes rerun under the same offline audit hook: 8 passed.
- New independent adverse probes: 6 passed; reviewer separately reproduced 226 tests.
- Independent probes and final disposition: `docs/AJ-0012-review/`.

All test transports are local fixtures. The original suite's audit hook blocks
outbound network and executable launches; the POSIX fork test inherits that guard.
Core, accepted Slack adapter, recovery logic and original test files are unchanged.
Root acceptance is required before feature-only commit/push; candidate remains
uncommitted and unpushed. No live success is asserted.
