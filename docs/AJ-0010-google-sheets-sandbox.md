# AJ-0010 Google Sheets adapter and isolated live sandbox

Current result: implementation and bounded live test PASS; independent code and
live evidence reviews PASS. Root acceptance governs preservation. No commit
or push has occurred. This report supersedes earlier partial reports retained in
`history/AJ-0010-before-ack-correction` and the earlier stage evidence directories.

Lineage: AJ-0010 / SpecRevision1 / RunEpoch1 / Attempt1 /
Nonce VA-LIVE-SHEETS-0010-01. Victor approval: Slack1791113671.468969.
Protocol v1.1.0 / Catalogue1.0.0. Root confirmed this executor sole owner of workbook
creation/setup and both synthetic mutations through the existing executor-local,
agent-mediated MCP route. No production ledger mutation, new job, external message,
credential, permission change, installation, deployment, main merge, automatic
successor or destructive cleanup occurred.

## Repository and preservation gate

Repository `/workspace/Command-Center-Gravity`; origin
`https://github.com/Victoradex94/Command-Center-Gravity.git`.
Initial branch `work` at `dea8cddc0bb6e7ab20479d8aca25121590749a3b`
did not contain the preserved object. Remote inspection confirmed the preserved
branch/commit and no existing target branch. These commands succeeded:

```sh
git fetch --no-tags origin refs/heads/aj-0009-sheets-writer-v1:refs/remotes/origin/aj-0009-sheets-writer-v1
git switch -c aj-0010-google-sheets-sandbox 78928bc29fe920143891061307d5ed44308b4c97
```

Current branch `aj-0010-google-sheets-sandbox`; base and HEAD
`78928bc29fe920143891061307d5ed44308b4c97`. Main/prior branches unchanged.
Work remains unstaged/uncommitted. Root must explicitly accept this code/test/live
return before feature-only commit/push preservation. The final artifact manifest
covers modified and ordinary untracked files, including journals and raw evidence;
ordinary Git diff alone excludes additions. Ignored caches are outside that manifest.

No project AGENTS.md/SKILL.md was found under /workspace. Relevant Google Drive/
Sheets skills, references, current writer limits and F1/F2 history were read.
An initial broad instruction search hit an unreadable daemon directory (exit2);
its chained Git command never executed. Corrected scoped checks passed.

## Implementation

| File | Responsibility |
| --- | --- |
| dispatcher/google_sheets.py | Existing-MCP adapter, native/normalized mapping, private target checks, complete reads, narrow literal writes, durable receipts, conservative settlement |
| dispatcher/sheets_tool_bridge.py | One request at a time; fresh session, sequence and exact binding; no credentials/network/retries |
| dispatcher/sheets_sandbox.py | Pure fixture planner, stable IDs, accepted-writer create/update and existing-operation reconciliation |
| tools/aj0010_sandbox_session.py | Exact fixture driver, root-bound session authority, exclusive journal guards, separate execute/reconcile processes, raw evidence |
| tests/test_google_sheets.py | 37 simulated adapter tests |
| tests/test_sandbox_session.py | 4 simulated driver/bridge tests |
| tests/offline_suite.py | Output wording only; I/O guard unchanged |

The accepted writer, repository, journal schema and model remain unchanged,
including ownership/handoff, authority/renewal scope, F1/F2 protections, permission
stops, fingerprints and shared recovery/fallback budgets. Exactly 17 ledger columns
and seven statuses remain. SessionAuthority is a trusted attestation of the current
bounded root instruction, not MockAuthority, OAuth or a general authorization
service. Reconcile has no mutation authority, claim, renewal or lineage change.

The adapter rejects the production ID and supports one explicit private My Drive
root sandbox, one tab, 2–100 rows, A:Q plus R sentinels. J contains
`vicadex.sandbox.source.v1` JSON; decoded source keys must match the configured
allowlist and sidecar. No legacy import, append, row insertion/expansion or overwrite
of rich text, formula cells or chips is supported.

The writer and adapter preflight row, logical ID/source, revision/lineage, owner
and scope. Before emission a SQLite FULL receipt stores exact submission, request
and baseline under a unique stable attempt ID. One updateCells request writes
A2:Q2 using only fields=userEnteredValue and explicit stringValue entries.
There is no adapter retry/alternate route. Read-before-write is not atomic CAS.

Settlement requires the retained original synchronous native acknowledgement for
the exact request/target, one empty reply, no contradictory envelope, exception or
cancellation, plus exact 17-cell/source/position and exposed structure readback.
Optional updatedSpreadsheet:null is actual connector normalization when no resource
was requested. A non-null resource must identify the same spreadsheet. Null alone,
wrapper success or reassuring text proves nothing. Lost receipts, timeouts,
generic cancellations, unfamiliar envelopes, partial values and permission/
structure drift remain UNCERTAIN even if cells match.

Google's synchronous contract supports the bounded positive path:
[batchUpdate](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/batchUpdate),
[empty update replies](https://developers.google.com/workspace/sheets/api/guides/batch),
[updateCells](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/request#UpdateCellsRequest).
It settles the acknowledged invocation; it supplies no CAS/distributed exclusion,
physical exactly-once guarantee or immunity to subsequent owner edits.

## Actual connection and private workbook

Successful existing tools: mcp__codex_apps__google_drive_get_profile, search,
get_file_metadata, create_file, get_spreadsheet_metadata, get_spreadsheet_cells,
batch_update_spreadsheet. The agent invokes these and binds actual responses back
to Python over JSON lines. This is **agent-mediated existing MCP**, not direct/
unattended Python authentication or a coordinator-brokered connection. No token or
credential was inspected/extracted/installed. OAuth scope strings and internal
connector retry/queue settings are not exposed.

Authenticated profile: Adetimilehin VicAdex Inioluwa, vicadtorex@gmail.com,
provider user ID118217609254113054328. Earlier production-reference reads were only
metadata and Agent Jobs!A1:B1 headers to establish mapping. No production writes.
Read-stage evidence remains in AJ-0010-connection-evidence.json.

Exactly one workbook:
[Command Centre — Ledger Writer Sandbox](https://docs.google.com/spreadsheets/d/1yk-mBJf4RQhRC7M7QK0cHRMQhqHWStC-yQpbB2KxksE/edit).

- ID `1yk-mBJf4RQhRC7M7QK0cHRMQhqHWStC-yQpbB2KxksE`.
- Tab Agent Jobs Sandbox, metadata-derived sheetId1505506183.
- Provider creation time 2026-10-04T12:29:10.246Z.
- Exact-title search: no result before creation, exactly this ID before setup,
  create and update. Stable intents and original responses retained.
- Before any fixture data: shared=false, drive_id=null,
  source_visibility_status=permission_metadata_available and one user/owner
  permission for authenticated vicadtorex@gmail.com.
- Its sole parent was 0AD1r1m5bkvJYUk9PVA. Actual fileId=root resolved that same
  My Drive root, itself unshared, no shared-drive ID/parent, same sole owner
  permission. No inherited shared parent existed. Every later capture rechecked
  both permissions and exact parent.

Normalized metadata omits some raw fields including capabilities and permission
IDs; those omitted fields are not asserted as observed.

## Live sequence and evidence

One setup batch (seven requests): rename/tab6×18/frozen header, exact17 headers,
six R sentinels, TEXT/WRAP, bold grey header, seven-status E2:E6 validation and
Yes/No N2:N6 validation. Initial Sheet1 A1:R6 was blank. Setup returned seven empty
replies. Its optional null response was first observed here, before logical writes.
Both logical writes were held while the mapping correction was independently
reviewed. Setup was never replayed. An exact requested-RGB diagnostic exited1:
Google normalized requested0.9 to actual0.8980392. Original evidence and that
failure are retained. Preservation then compared the actual baseline exactly,
without tolerance or another setup.

| Operation | Attempt/count | Actual result |
| --- | --- | --- |
| AJ-0010/sandbox/workbook-v1 | one create_file | Exact workbook and privacy verified |
| AJ-0010/sandbox/setup-v1 | one7-request batch | Fixture verified |
| AJ-0010/sandbox/create-v1 | /0; execute sequence17 | SUCCESS; Intake; RecordRevision1 |
| AJ-0010/sandbox/update-v1 | /0; execute sequence34 | SUCCESS; Ready; RecordRevision2 |

Exactly two logical submissions, no recovery/replay. Each original response is
isError=false, exact spreadsheetId, replies:[{}], updatedSpreadsheet:null.
Original responses survive independently in supervisor files, driver response
files and receipts.sqlite. Writer state has one submission per operation,
recovery_used0 and no open circuit.

The unchanged saved fixture AJ-0010-fixture-plan.json SHA-256 is
`c448dd13a66e038f1bc9bd554dba124002a05b5ff80780cc6a1a0c4edf746e48`.
All17 cells of both operations match it, including blank B and create's literal
K `=literal RAW text; Vic’Adex` (not a formula). Update changes only E,K,L,M,Q.
Q advances RecordRevision1→2 with the same SpecRevision1/RunEpoch1/Attempt1/nonce.
Fixture timestamps are synthetic saved values, not claimed execution times.
The synthetic L value “readback pending” remains exact fixture data, not report state.

Create readback is in the update receipt baseline and intervening raw CellData;
revision2 is in execute-after.json and both reconcile captures. Full exposed
metadata, ACLs, A1:Q1, A3:Q6, R1:R6, formatting, notes and validation compare equal
before/after when only A2:Q2 userEnteredValue is masked.

Execute process tool session83514 / bridge97ff1d51b9f89ada8a9bec9e6b81a14b exited0:
46 calls =44 reads +2 writes. After it exited, a separate OS process opened the
same journals: tool session19163 / bridgef5b464e90ecfc18b6d448351ddf93616, exited0,
eight reads and **zero writes**. Both persisted operations remain SUCCESS and
submission count remains2. Historical create success is retained; current live
row remains revision2. Reconcile does not overwrite it to reproduce revision1.

Commands (interactive transport uses stty -echo -icanon):

```sh
python3 -B -u -m tools.aj0010_sandbox_session execute docs/AJ-0010-live/config.json docs/AJ-0010-fixture-plan.json docs/AJ-0010-live
python3 -B -u -m tools.aj0010_sandbox_session reconcile docs/AJ-0010-live/config.json docs/AJ-0010-fixture-plan.json docs/AJ-0010-live
PYTHONPATH=. python3 -B docs/AJ-0010-live/verify_saved_evidence.py
```

All exit0. Saved-evidence verification performs no new connector calls.
Do not rerun execute: existing journals reject it. Repeating the driver reconcile
also stops on preserved filenames; later observation requires coordinated evidence
preservation. The workbook is retained; no cleanup was attempted.

## Verification and independent review

AJ-0010-final-tests.json records exact commands, times, duration, exits, output
sizes and hashes; complete logs in AJ-0010-final-test-evidence. Counts overlap.
Simulated faults are separate from two actual successful writes.

| Command/check | Result |
| --- | --- |
| Untouched preserved baseline python3 -m tests.offline_suite |152 pass; exit0 |
| python3 -B -m tests.offline_suite |193 pass =152 preserved +37 adapter +4 driver; exit0 |
| python3 -B -m unittest tests.test_google_sheets tests.test_sandbox_session -q |41 pass; exit0 |
| python3 -B docs/history/AJ-0009-ir1-review/test_review_probes.py |F1:4 pass; exit0 |
| python3 -B tests/probe_writer_f2.py |F2:1 pass; exit0 |
| python3 -B -m tests.simulate |11 groups /58 tests; exit0 |
| In-memory compile dispatcher/tests/tools |PASS; no bytecode |
| git diff --check; git diff --cached --exit-code |Both exit0; staging empty |

Independent reviewer /root/aj0010_independent_review found and verified fixes for
prior-instance bridge reply replay and an initial uuid/import-boundary issue.
Random fresh session binding using already-allowed os.urandom corrected these
without weakening the I/O guard. Failed and passing histories remain. Earlier
blanket-unsettled candidate was archived before root-approved positive-ack mapping.
No uncertain logical live write was replayed to obtain a better response.

Latest independent code review: guarded193 pass, nullable probes3, ack probes8,
driver probes4, retained F1/F2 4/1 (all exit0). Evidence directories:
AJ-0010-independent-review (earlier stage), AJ-0010-ack-independent-review,
AJ-0010-null-independent-review. Reviewed adapter SHA-256
`b923263a64e3fed76b46b27e0339b17bc328fa82a074e4eeace6b216a7d2e617`;
driver `65fd8bdfcea305ae75cd42868000b59d11f017bbea61b77de7c4fd3878ac3171`.
Reviewer made no connector calls/mutations. Independent live review PASS is retained
in AJ-0010-live-independent-review: 1,228 assertions, both SQLite integrity checks,
exact values/structure/permissions and separate-process zero-replay checks passed,
exit 0. No defects or unreconciled effects were found. This review inspected
retained original evidence, not a new connector read or live fault injection.

## Limits and remaining gate

This proves the bounded sole-owner sandbox flow, not production/unattended
readiness. Google Sheets has no CAS for this update. Local advisory locks and
preflight do not exclude another device/session. Multi-read permission/grid
captures are not atomic. Unexposed metadata, connector internal retries/hidden
pending calls and physical exactly-once are not proven. Missing/ambiguous original
receipts remain frozen regardless of matching cells. No live timeout/cancellation/
fault injection occurred; those branches have simulated evidence only.

No production authority import, distributed writer, external trigger, delivery
adapter, scheduler or unattended authentication is installed. Root's explicit
acceptance of final code/test/live evidence remains the gate before authorized
feature-only commit/push. No main merge or successor is implied.
