# AJ-0010 Google Sheets transport and sandbox — partial milestone

Lineage: Job AJ-0010 / SpecRevision 1 / RunEpoch 1 / Attempt 1 /
Nonce VA-LIVE-SHEETS-0010-01. Bounded approval supplied by root: Victor's Slack
1791113671.468969. Protocol v1.1.0 / Catalogue 1.0.0. No production ledger writes,
new jobs, external messages, credentials, installations, permissions, main merge,
deployment, automatic successor or destructive cleanup occurred.

## Repository and preservation gate

Repository `/workspace/Command-Center-Gravity`, origin
`https://github.com/Victoradex94/Command-Center-Gravity.git`. Initial checkout was
`work` at `dea8cddc0bb6e7ab20479d8aca25121590749a3b`; the requested implementation
object was absent. `git ls-remote --heads origin main aj-0009-sheets-writer-v1
aj-0010-google-sheets-sandbox` confirmed the preserved branch at exactly
`78928bc29fe920143891061307d5ed44308b4c97` and no existing target branch. A targeted
`git fetch --no-tags origin refs/heads/aj-0009-sheets-writer-v1:refs/remotes/origin/aj-0009-sheets-writer-v1`
retrieved it, then `git switch -c aj-0010-google-sheets-sandbox
78928bc29fe920143891061307d5ed44308b4c97` created the new feature branch.
Main and prior branches were not changed. HEAD remains the preserved base; all
AJ-0010 changes are uncommitted and unstaged. Commit/push waits for root's explicit
acceptance of the code/test/live-evidence return.

An initial broad instruction-file search included an unreadable daemon directory
under `/tmp`, exit 2; the chained Git command did not execute. The corrected
repository-specific Git check/fetch succeeded, exit 0. No project AGENTS.md or
SKILL.md was found under `/workspace`. The Google Drive and Google Sheets skills,
their relevant references, the writer limits and F1/F2 history were read.

## Implementation

| File | Responsibility |
| --- | --- |
| `dispatcher/google_sheets.py` | Existing-MCP adapter; exact bounded reads, native and actual normalized metadata mapping, owner-only private access checks, source decoding, literal A:Q updateCells, durable exact-call receipts and conservative observations |
| `dispatcher/sheets_tool_bridge.py` | JSON-lines exchange with the supervising agent's supported tools; exact tool/argument binding, random per-bridge session and sequence; no networking, authentication, tool invocation or retries |
| `dispatcher/sheets_sandbox.py` | Pure fixture/setup planner; stable create/update requests; accepted-writer-only driver that stops on non-SUCCESS; read-only existing-operation reconciliation |
| `tests/test_google_sheets.py` | 28 simulated transport, privacy, structure, cancellation, crash, restart, freshness and fixture tests |
| `tests/offline_suite.py` | Corrected result wording; existing external-I/O guard unchanged |

The writer, repository, journal schema, authority reader contract, persistent
permission stops, exact renewal bindings, source/lineage protections, shared
retry/fallback budget, seven statuses and 17-column model are unchanged. No live
MockAuthority is used; tests use it only as a labelled synthetic fixture. A future
live driver still needs the current root-bound AuthorityReader and exclusive
ownership established under the existing contract. Planning never grants either.

The adapter supports only an explicitly configured private sandbox in My Drive
root, one tab, 2–100 rows, A:Q ledger plus R sentinels. AJ-0010 plans six rows.
The production workbook ID is explicitly rejected. No multi-tab/legacy import,
row insertion, expansion, table conversion or append mutation is implemented.
Rows decode source keys from actual J JSON `vicadex.sandbox.source.v1`, checked
against the configured synthetic source allowlist. Sidecar keys cannot override J.
Formulas, rich text and chips in the ledger are rejected before value updates.

Each submission persists its exact request and before capture before one call to
`mcp__codex_apps__google_drive_batch_update_spreadsheet`. It uses one `updateCells`
request, one row, columns 0–16, `fields=userEnteredValue`, and explicit
`stringValue` (including text beginning `=`). It never inserts or appends. A second
submission of the same attempt is refused by a persistent unique receipt key;
receipts are bound to the full submission, scope, authority and intended values.
Read-before-write detects observed drift but is not atomic CAS.

The adapter compares actual A:Q values and source identity, target row, exact
headers, sentinel cells, other rows, exposed sheet properties, user formatting,
notes and validation. It requires the original seven statuses and Yes/No rules.
It cannot attest metadata the tool omits, a globally consistent multi-read
snapshot, future ACL changes, or the absence of edits by another owner session.

## Actual connection evidence — read only

The executor itself exposes and successfully called:

- `mcp__codex_apps__google_drive_get_profile`: Adetimilehin VicAdex Inioluwa,
  `vicadtorex@gmail.com`, provider user ID `118217609254113054328`.
- `google_drive_search`: exact nontrashed workbook title and native Sheets MIME
  filter returned no results. No mutation was inferred from this absence.
- `google_drive_get_spreadsheet_metadata`: supplied production reference metadata
  read only. Its native `spreadsheetId/properties/sheets` structure is observed.
- `google_drive_get_spreadsheet_cells`: production reference `Agent Jobs!A1:B1`
  header read only, establishing the actual native CellData mapping and omitted
  zero offsets. No production test data or writes were sent.
- `google_drive_get_file_metadata`: actual normalized `title/mime_type/parent_ids/
  drive_id/permissions` output, despite requesting raw Drive fields. My Drive root
  `0AD1r1m5bkvJYUk9PVA` returned `shared=false`, `drive_id=null`, one user/owner
  permission for the authenticated email and `permission_metadata_available`.
  Production reference metadata returned `shared=true`; it is never a test target.
- A Python `StdioToolBridge` process emitted an exact root metadata request. The
  agent called that tool and returned the actual response with session, sequence
  and binding; normalized private-root validation and the process exited 0.

The connection is **agent-mediated MCP**, not direct or unattended Python access.
No credential/token was inspected, extracted or installed. OAuth scopes and
connector internal retry settings are not exposed. Root-only private metadata
does not establish the privacy of a workbook that has not been created.
Full recorded read evidence is in `AJ-0010-connection-evidence.json`.

## Live gates and outcome

The coordinator was given the exact route and proposed layout before creation.
An in-task coordination request to confirm sole ownership and no other creation
in flight is pending. It is not a request for Victor to approve the milestone
again. No coordinator-brokered route or alternate authentication was used.

The existing connector also provides **no operation-status or pending-retry/queue
terminality surface**. A synchronous provider-shaped success plus exact values
can establish observed `Effect.APPLIED`, but cannot prove all pending effects
settled through this tool layer. The adapter deliberately returns
`settled=false`, `effects_resolved=false`; the accepted writer therefore remains
UNCERTAIN, retains its fingerprint/budget, and blocks update/recovery. Matching
cells, an empty row, generic cancellation or outer “Action completed” never prove
no-op/finality. There is no configuration flag to manufacture stronger evidence.
All error responses remain retained in receipts; Python exceptions retain their
type only to avoid recording potentially secret exception strings.

Because these gates are unresolved, no sandbox creation or write was attempted.
The real adapter's batch response shape (`spreadsheetId`, one empty reply for the
one updateCells request) is documented/provider-derived and **simulated only**.
No live write response has confirmed that connector mapping.

| Live item | Actual result |
| --- | --- |
| Workbook creates / setup batches | 0 / 0 |
| Synthetic logical creates / updates | 0 / 0 |
| Recovery / replay writes | 0 / 0; no live operation exists |
| Production writes | 0 |
| Sandbox ID / workbook private-access proof | None / not available |
| Exact before/after cells, formatting and validation | Proposed fixture only; not observed live |
| Live restart/zero-replay demonstration | Not performed; no live journal exists |

The precise remaining technical requirement is supported authoritative settlement
and remaining-race handling for the same exact connector operation, plus root's
single-owner coordination. No new credentials or permissions are requested.
If that evidence is unavailable, retain this as a partial code/read-connection
result with the live branch held. Do not create a workbook merely to obtain a
known-unsettleable write, force SUCCESS, bypass the writer to execute the update,
or silently introduce another route.

## Proposed fixture — not executed

Title `Command Centre — Ledger Writer Sandbox`; tab `Agent Jobs Sandbox`; grid
6×18. A1:Q1 is the exact schema; A2:Q2 begins empty, rows 3–6 stay empty;
R1:R6 are distinct synthetic sentinels. E2:E6 validates exactly the seven statuses;
N2:N6 validates Yes/No. Setup provides literal text formatting, wrap and a light
grey bold header. A setup batch is counted separately from the two logical writes.

Stable operation IDs: `AJ-0010/sandbox/create-v1`,
`AJ-0010/sandbox/update-v1`; provider attempt IDs would be each plus `/0`.
Both use JobID AJ-0010, SpecRevision=1, RunEpoch=1, Attempt=1,
Nonce=VA-LIVE-SHEETS-0010-01, and a clearly synthetic source. Create uses Intake
and RecordRevision=1; update uses Ready and RecordRevision=2 with the same
execution lineage. All 17 proposed cells, empty before-row and exact setup
requests are in `AJ-0010-fixture-plan.json`. Its example sheetId 0 is a planner
placeholder, never an authorised target.

## Tests, review and limits

`AJ-0010-results.json` records every command, exit, duration and stdout/stderr hash;
logs are under `AJ-0010-evidence`. All counts below overlap.

| Command | Result |
| --- | --- |
| `python3 -m tests.offline_suite` on untouched preserved base | 152 pass, exit 0 |
| `python3 -m tests.offline_suite` final | 180 pass (152 existing + 28 new), exit 0 |
| `python3 -m unittest tests.test_google_sheets -q` | 28 pass, exit 0 |
| `python3 -m unittest tests.test_protocol tests.test_review_regressions -q` | 58 pass, exit 0 |
| `python3 docs/history/AJ-0009-ir1-review/test_review_probes.py` | Historical F1 4 pass, exit 0 |
| `python3 tests/probe_writer_f2.py` | Historical F2 1 pass, exit 0 |
| `python3 -m tests.simulate` | 11 groups / 58 tests, exit 0 |
| `python3 -m compileall -q dispatcher tests` | Exit 0 |
| `git diff --check`; `git diff --cached --exit-code` | Both exit 0; staging empty |

The full suite's external-I/O guard is unchanged. Simulated update mapping tests
exercise the transport directly only as a labelled fixture; they do not authorise
bypassing the writer live. Writer integration tests demonstrate the expected
UNCERTAIN freeze, same-journal restart, stable fingerprint, budget zero and one
provider submission with zero additional replay writes.

Independent reviewer `/root/aj0010_independent_review` found R1: a restarted bridge
could accept a prior instance's first reply. A per-instance random transport
session now participates in request/reply binding, leaving stable logical
operation IDs unchanged. The initial correction used `uuid`, rejected by the
existing import-boundary test; it now uses already-allowed `os.urandom`. The import
allowlist was not weakened. Failed author evidence is retained under
`history/AJ-0010-initial-verification`; independent failed/passing probes and
reviewed manifests are retained under `AJ-0010-independent-review`.

The independent final disposition is **PASS for bounded code/mock scope**, with
no unresolved code defect within that scope. The reviewer independently ran
`python -B -m tests.offline_suite` (180 pass, exit 0), the focused suite under the
offline guard (28 pass), five adversarial probes (5 pass, exit 0), retained F1
(4 pass) and F2 (1 pass) probes, and diff/core-comparison checks. All final exits
are 0; counts overlap. The five probes cover stale prior-instance replies, crash
after application before receipt, immutable receipt identity, wrong provider
target, and repeated same-journal reconciliation without replay/budget reset.
The reviewer used no connectors and made no repository edits. Source hashes
were rechecked against the reviewer's final manifest before this handoff.

The bounded deliverable is source code, simulated safety tests and verified
read-route evidence. The requested live create/update, actual sandbox privacy,
live structure preservation and live restart proof remain incomplete. Independent
review or author tests cannot turn those missing live criteria into a success.

Provider references used for request/response design:
[Sheets batchUpdate](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/batchUpdate),
[CellData](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/cells),
[Drive files](https://developers.google.com/workspace/drive/api/reference/rest/v3/files).
Google documents atomic application of a batch and the possibility of collaborator
changes; this does not supply the missing connector terminality or a CAS lock.
