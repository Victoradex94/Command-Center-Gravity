# AJ-0019 cutover readiness — NO-GO

Execution start 2026-10-05 11:47:33 UTC. AJ-0019 / SpecRevision=1 / RunEpoch=1 / Attempt=1 / nonce VA-READINESS-0019-01. PROVISIONAL PENDING_CANONICAL_RECONCILIATION. Owner authority Slack1791200689.604719; Dẹkun retains dispatch and ledger ownership. Candidate is uncommitted, unpushed and inactive. No automatic successor.

## Repository and compatibility

Verified origin Victoradex94/Command-Center-Gravity, exact base f469130a9632054a31cbb9d638170acaf841b52a; unused local and remote feature name verified before creating aj-0019-cutover-readiness-v1. Initial environment was main's initial commit; exact AJ16 fetched read-only. No AGENTS.md or repository SKILL.md discovered. No AJ17 refs fetched explicitly, invoked, reconstructed or modified. No AJ18 conversion implementation added.

Accepted artifacts are references, not a tested integrated release: AJ12 9c81bda8675477609e8f6697b9ae26ca6e1fbbe0 and AJ14 d9cec7635bba5a214b990a479ff5ad4f68667126 are separate descendants. AJ15 ce956abbe6b8217c1101edea1cbed6f8c9addeb3 and AJ16 f469130a9632054a31cbb9d638170acaf841b52a descend through AJ14. AJ12 controlled Slack integration requires an explicit integration candidate and regression tests; no merge performed. AJ16 POSIX shared provider is local fencing, not proven distributed CAS. Its import accepts literal strings only. Typed equality below is representation comparison, not native Sheets conversion, formula evaluation or AJ18 fidelity proof.

## Discoverable legacy paths and limits

Evidence is at the verified base, searched with `rg -n 'sheet|Sheet' dispatcher tools --glob '*.py'`; source line evidence is in route-inventory.json. Production target denial in GoogleSheetsAdapter is a scoped safeguard, not global retirement proof.

* dispatcher/google_sheets.py: GoogleSheetsAdapter snapshot reads metadata/cells via injected caller; submit sends batch_update_spreadsheet. SandboxTarget rejects production workbook and requires sandbox identity; 18-column sandbox includes sidecar, not a changed 17-column Agent Jobs contract.
* dispatcher/sheets_tool_bridge.py: StdioToolBridge allows metadata, cells and batch update, emits requests for supervising agent invocation. Agent/coordinator route remains external.
* dispatcher/sheets_writer.py: SheetsWriter adapter snapshot, submit, inspect; durable ownership/revision/uncertain-operation journal. Does not fence arbitrary external writers.
* dispatcher/sheets_repository.py: read/all/commit/reconcile expose Sheet-backed JobRepository; engine reads/commits through injected repository. SlackBoundary can indirectly trigger coordinator mutation; Codex worker returns require coordinator verification, never own ledger authority.
* dispatcher/sheets_sandbox.py and tools/aj0010_sandbox_session.py: fixture/setup requests, bounded execute/reconcile bridge route. Do not run against legacy workbook.
* dispatcher/mock_sheets.py: simulated snapshot/submit/resolve/seed only; tests/support.py, test_sheets_writer.py, test_google_sheets.py, test_sandbox_session.py and revision/review tests inject simulated routes. dispatcher/isolation.py simulates legacy roles reader/allocator/dispatcher/writer/cache/reverse_sync; those role labels are not discovery of actual deployments.
* docs/history contains preserved old implementation copies and probe scripts; docs/AJ-0010-live/verify_saved_evidence.py and live-independent-review/verify_live.py read saved evidence. Saved request JSON/SQLite are historical artifacts, not a route disablement certificate. No private artifact bodies copied into new fixtures.

UNKNOWN external routes: direct Sheets MCP calls outside checkout; Apps Script/triggers; webhooks; cron/hosted processes; human editors; service accounts; cached Ready queues; allocator/dispatcher instances; reverse sync/projection; old coordinator sessions; permission holders and in-flight tool operations. No deployed configuration, permission inventory, operation handles or access audit is available here. All must be owned, enumerated, fenced and independently evidenced before retirement; repository search cannot establish global completeness.

## Frozen snapshot and genesis schema

Metadata only: workbook 19mGYxNeyldQEK4N194Q8Yz7L6m_z7LSvFmHGzwuqA84, title Agent Jobs, gid 103260001. Parent observation 11:36 UTC Oct 5: 14 jobs AJ1–14; AJ14 row15 Ready, RecordRevision1. Intended revision2 update to L/M/P/Q not visibly landed. Tool cancellation has no operation handle/finality proof. These are supplied observations, not a local read or immutable byte capture. Repeated unchanged reads cannot prove no-op. Real immutable capture bytes/digest and cancellation finality remain UNKNOWN. Coordinator later supplied extent/native metadata observations below; these do not prove exact extraction or bootstrap equality.

Exact closed schemas are in bootstrap.schema.json. Snapshot schema has version2, exact source identity/range, complete capture reference/time/timezone (timezone-aware ISO timestamp, A1:Qn header-plus-row extent), exact ordered columns/statuses and ordered 17-cell rows including captured trailing absent template rows. Header+row extent must cover the captured grid, not just occupied jobs. Version2 retains the AJ16 kind/value/format/timezone cell contract and adds full-grid headers, grid metadata and a separate per-cell native provenance matrix; blank and absent differ; formula and literal differ; no trim, date conversion or Unicode normalization. Object key order is immaterial; list order, numeric JSON representation (1 versus 1.0), all types and metadata are exact. Native notes, format and validation objects are captured separately without conversion; all keys/values are compared exactly. Missing notes differ from empty notes. Native properties outside this capture contract must gate AJ18 rather than silently disappear. Date serials stay opaque; explicit interpretation policy and note provenance are required, never infer Lagos wall time from workbook timezone.

Genesis metadata binds job identity/spec/run/attempt/nonce, repository/base/ref, snapshot reference and SHA256, columns/statuses, ordered job identifiers, provisional inclusions, per-cell hashes, stable import operation identities, unknown history, privacy scope, legacy unknown exceptions, route retirements and accepted human approval reference. It contains no row bodies. Hashes/private identifiers stay in protected evidence, never public fixtures. Snapshot payload lives separately in protected storage. This schema does not change AJ15's closed event/tree contract: actual genesis writer must be integrated and reviewed after AJ18. One explicit snapshot-import event per job; never invent prior status history. Import identities bind complete snapshot digest, source, job and exact cells as AJ16 does. No operational manifest can be produced until real snapshot bytes and approvals exist.

## Equality and acceptance checklist

`python3 -B -m tools.aj0019_verify EXPECTED ACTUAL` opens only local files, rejects duplicate JSON keys and unsupported/malformed snapshots, emits PASS/HOLD without cell bodies or private hashes, never imports/writes/activates. Equal reports mean equality of already represented complete captures, not proof that Sheets extraction was complete. Both capture envelopes must use the same frozen provenance; fresh read timestamps belong in separate read receipts. Export files must be protected and excluded from repository; comparison failure details intentionally stay private.

Before bootstrap acceptance Dẹkun must verify authoritative complete capture, exact workbook/tab/range/header, all 17 columns and seven statuses, all jobs including approved provisional inclusion, duplicate/extra/missing rows, exact cell types/formulas/format/timezone/blank/absent semantics, per-cell and full snapshot digest binding, deterministic one-event genesis and restart prefix reconciliation, privacy scope, and independent output equality. Local synthetic tests exercise equality only; real snapshot equality is UNEXECUTED. A matching display-value read is insufficient.

## Criterion-to-evidence and go/no-go gates

| Criterion | Offline evidence/design | Remaining gate and owner |
| --- | --- | --- |
| Route inventory / legacy retirement | route-inventory.json; scoped source review above | UNKNOWN external routes and in-flight cancellation finality; Dẹkun must prove retirement, queues/cache/reverse-sync denial; no-op is not proved |
| Genesis contract | bootstrap.schema.json; accepted AJ16 model | Real complete frozen digest/approval absent; AJ18 integration gated |
| Bootstrap equality | test_cutover_readiness; read-only CLI | Real bytes unavailable; actual equality UNEXECUTED |
| Coherent RC | release-candidate.json pins exact refs | AJ12/AJ14 integration not tested; no main merge |
| Synthetic E2E | rehearsal steps below; inherited offline component tests | Composed integrated rehearsal not executed; separate authorization required |
| AJ17 transport/preservation | User reports accepted 341-test candidate, uncertain preservation, absent branch at 11:36 | Dẹkun resolves uncertainty elsewhere; no invocation/reconstruction here |
| AJ18 typed fidelity | Exact typed synthetic comparison only | Launch unknown; accepted native conversion and import proof required |
| Hosted transport | inherited local Git integration | Hosted two-client exact-ref CAS, closed tree readback, lost response reconciliation UNEXECUTED; caller-supplied distributed CAS unproven |
| Live projection/readback | Design: projection never authority | Separate approval and exact authorized readback required; no live projection |
| Restart/fault rehearsal | inherited AJ16 offline tests/local bare scenarios | Integrated hosted restart, lost reply, delayed write, fork/corruption/stale route cases UNEXECUTED |
| Rollback/fence | AJ16 local HOLD/no old reactivation tests | Cross-host worker fence and rollback verification required; never revive old writers automatically |
| Privacy scope | New synthetic fixtures, body-free CLI | Protected capture handling, access/retention review and human approval required |

Overall NO-GO for activation. Offline PASS facts do not satisfy live gates. Dẹkun exact-candidate acceptance permits later standing feature preservation only; commit/push await that review. Victor/Dẹkun approvals for cutover, live transports/projection, protected data handling and rollback are separate from candidate acceptance.

## End-to-end synthetic rehearsal plan (not executed)

1. Select disposable synthetic Slack inputs/destinations and Git refs, mock all transports; establish owner-authenticated grant outside payload. Invent AJ-9000 lineage; no real message bodies. Record pinned component revisions and offline audit guard.
2. Feed intake into SlackBoundary; classify command, reject unauthorized/edit collisions, duplicate identical source key/version without new work; preserve provisional canonical reconciliation state. Assert journal reservations before execution.
3. Record provisional Git journal operation with exact expected head/event/revision and stable nonce; independently read closed tree/ancestry. Inject stale head, two-client conflict and lost publication reply; same-operation reconciliation, no replacement identity/replay.
4. Dẹkun reserves eligible route only after contract/gates/fence. Fake Codex worker admits once; duplicate dispatch inspects same reservation. Inject unknown admission/restart and cancellation race; HOLD uncertain outcome.
5. Return same lineage/attempt/nonce, classify progress/complete/block; stale/conflicting/duplicate return cannot advance wrong revision. Worker output is evidence, not authoritative completion.
6. Dẹkun verifies outputs and accepted criteria, records Review then Done only after verification. Bind output digest to exact candidate. Test bad evidence, missing owner decision, fault before/after append and restart.
7. Queue Slack delivery with stable destination/thread/event; fake send/readback distinguishes found/authoritative absent/unknown. Lost reply holds or reconciles original delivery; human-read remains unknown. Never call Slack or send real messages.
8. Prove projection cannot promote authority, stale cached Ready and retired epoch are denied; rollback selects HOLD, never old authority. Capture synthetic transcripts, exact hashes, commands and independent review. Integrated AJ12/AJ14 adapter compatibility is a prerequisite, not assumed from component test success.

## Same-job coordinator supplement — 11:48 UTC Oct 5

Supplied coordinator observation, not a new local live read: Agent Jobs grid 201x17, locale en_US, timezone Africa/Lagos, frozen header/first column, occupied data ends row15. Counts: 199 string cells including 17 headers; 28 numeric date cells G2:G15/P2:P15; 3190 absent values; no explicit empty strings. No formulas, booleans, errors, chips, rich-text runs or cell hyperlink fields returned. Twelve notes contain UTC timestamp provenance and control-date semantics. DATE_TIME M/d/yyyy H:mm:ss on G/H/P template/data cells; strict seven-status validation E2:E201. K9 length 49473 characters; actual text is not copied. These observations do not supply immutable exact capture bytes, complete private digest or extraction fidelity proof.

Equality contract v2 must preserve the entire 201x17 captured grid including header and truly absent/template cells, native types, exact Unicode and long text without truncation, locale/timezone/frozen dimensions, every note, native format and validation object plus provenance, and explicit date interpretation policy. Workbook timezone alone does not establish what serial dates mean. Synthetic coverage includes 201x17 shape/absence, long decomposed Unicode/emoji strings over 49473 characters, note/format/validation mutations and policy changes. AJ18 retains native extraction, typed conversion and import integration ownership; this module merely compares supplied envelopes.

Confirmed coordinator reader/writer tools and known consumers are added to route-inventory.json. Other five tabs: 23 formulas inspected, no literal Agent Jobs/gid or IMPORT* references; indirect/external consumers remain unknown. shared=true is not complete ACL evidence. Original AJ14 request wrote all 17 userEnteredValue cells A15:Q15 despite changes only to L/M/P/Q. Late overwrite risk is full-row. No provider handle/finality exists, and an existing Git lock cannot fence the already submitted request. Legacy retirement is still unproved; unchanged reads do not close it.
