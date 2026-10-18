# Poetics Atlas staging database

**Status: Supabase is the user-directed authoritative current source (17 October 2026, 11:36 WAT). Technical cutover verification remains open.** This project is separate from WordPress.

## Current sources

- Supabase: project `Poetics Staging`, ref `tknahlnirtnanzqqvufb`, EU West. The branch selector reads `main PRODUCTION`; this is a database branch label within the separately named staging project. The dashboard currently shows a service-investigation banner.
- GitHub `main` HEAD observed 14 October 2026: `f2a92a07aa9ea158de21faa1c8b5583feaea91b9`. `poetics/dist/atlas-data.json` was last changed at `a221c05668739a15c0b1f664c5ab2d61bea6ebdd`.
- `poetics-staging` remains at `a221c05668739a15c0b1f664c5ab2d61bea6ebdd`, four commits behind main. Main contains `poetics/archives/sites-v45-retained-artifacts.tar.gz`, last changed at `efee4944d8177766173dc46411ee48bac76be155`; the path is absent from staging.
- The Sites Atlas preview says “Sign in required”. Its current rendered version cannot be compared with GitHub. GitHub changes do not automatically publish to Sites.
- Latest verified raw Drive download: 14 October 11:56, 153,555 bytes, SHA256 `b24cffd7c301cb92692914cd4e866da11560c3979a008cdcdfc738442047186a`. The provider revision and newer ledger text remain unverified because Google requires identity verification.

## Current database inventory

Fresh read-only SQL confirmed that `public` contains no tables and the private `poetics` schema has 13 tables: 449 nodes, 664 connections, 664 claims, 664 claim-source links, 187 sources, 31 aliases, 4 artifact manifests, 469 artifact chunks, 114 ledger sections, 30 research runs, 78 search queries, 0 normalized decisions, and 3 audit events.

The hash-gated restoration in `004_restore_verified_artifact_bytes.sql` completed successfully. All four payloads were rebuilt from ordered chunks and compared with stored bytes and manifest SHA256:

| Artifact | Bytes | Chunks | SHA256 |
|---|---:|---:|---|
| `drive-raw-20261014-1156` | 153,555 | 20 | `b24cffd7c301cb92692914cd4e866da11560c3979a008cdcdfc738442047186a` |
| `drive-rendered-20261014-1130` | 154,655 | 20 | `5db750a0fa809b27359d1a6d88ea08c1d4e9733ea968eda0efe7729cd83c5a64` |
| `github-main-efee4944-graph-20261014` | 1,597,040 | 200 | `31009691dfc69103ba77a11672757fb8c49f2e42e0c8d29200f7836c8763522d` |
| `github-main-efee4944-zip-20261014` | 1,825,048 | 229 | `edd0097c89266cc856e1816b61f1c81af6227599ede3c3d8b093e1dfbdc702d2` |

The rendered ledger is a separate browser capture, not the original Drive file. Its `original_bytes` preserve CRLF introduced by browser paste; its `decoded_text` is LF-normalised. The restoration preserves this distinction.

The read-only graph round-trip audit passes exact payload and stable-ID checks for all 449 nodes, 664 connections, 664 claim wrappers, 31 aliases and 187 source URLs. The missing/extra source URL query returns no rows. Endpoint and provenance checks found no missing connection subjects, objects or claims; no missing claim-source or alias references; no blank supported scope; and no missing original records.

History inventory by artifact: the raw Drive capture has 57 sections, 30 research runs and 78 search queries; the separate rendered capture has 57 sections and no runs or queries; the GitHub graph and ZIP have no ledger sections or runs. The duplicate 57 section rows belong to separate source captures; this does not identify the latest Drive revision. Query/run/section and search provenance checks returned no gaps. `poetics.decisions` has zero rows; decisions and status history remain in raw ledger narrative and still need evidence-based normalization.

All 13 tables have RLS enabled with no policies or `anon`/`authenticated` grants observed. This is default-deny. No authorized application identity path or scoped read/write check has been verified. The Supabase Free Plan reports no project backups; no durable recovery or restore test is complete.

## Remaining gates

1. Complete Google identity verification, read the current Drive text and provider revision, preserve newer contributions, then append and read back the same file ID.
2. Reconcile current Drive against the latest GitHub data, aliases, retained archive and branch differences. Do not assume Sites sync; its current preview is behind a sign-in wall.
3. Normalize decision and status history from the reconciled source while retaining the full narrative record and original date meanings.
4. Verify a narrowly authorized application identity and unauthorized denial without widening public access.
5. Establish durable backup/recovery and demonstrate a restore path.
6. Reconcile proposed research connections, including Cross Country identity and P012, against refreshed Drive and GitHub sources before importing new graph claims.

## Files and operating rules

- `001_staging_schema.sql`: historical bootstrap; not idempotent and must not be rerun on this project.
- `002_import_support_schema.sql`: data-free artifact chunk schema.
- `003_integrity_audit.sql`, `005_graph_roundtrip_audit.sql` and `006_history_artifact_reconciliation.sql`: read-only audit scripts.
- `004_restore_verified_artifact_bytes.sql`: transactional, SHA256-gated restoration for the four captured payloads; successfully run and read back against ordered chunks.

Keep this branch private and staging-only. Store schema, migration and data-free audit SQL only. Never add credentials, connection strings, ledger dumps, CSV imports, private submissions or artifact payloads. No live WordPress change, public database/API, Sites publish or cutover is recorded.


## Verified status checkpoint — 15 October 2026

This checkpoint supersedes the earlier source pointers and inventory above; those figures remain as historical snapshots. The audits below were read-only. The canonical Drive ledger remains authoritative and no cutover is recorded.

### Source state

- Canonical Drive file: Poetics-Atlas-Working-Ledger.md, ID 13qDg2XVdUM5ZAbplLoeNT5X6hB89cnSq. The authenticated preview currently displays entries through DB082-20261015-CURRENT-DRIVE-AND-STAGING-AUDIT. Drive metadata says it was modified on 15 October, but no exact provider revision ID or byte-exact current Markdown export was obtained.
- Two append artifacts must remain distinct. drive-ledger-append-20261015-0853 records the canonical file ID but is only an append payload. The normalized DB082 section is attached to drive-ledger-append-20261015-0911, whose recorded source URI contains a different Google Doc ID (1zuYwUn5O82BqqYiIc-A3exCGuypE_3GZIVsHStwDcsc). The current canonical preview contains DB082, but exact payload equality has not been established. Do not treat the 09:11 artifact as a byte-verified capture of the canonical file.
- GitHub main HEAD: c840387909221dd16f3f92f460910b33ad9e9b7b. The current poetics/dist/atlas-data.json file was last changed at a221c05668739a15c0b1f664c5ab2d61bea6ebdd; the later main commits inspected change UI/release files, not that graph export.
- GitHub poetics-staging remains at a221c05668739a15c0b1f664c5ab2d61bea6ebdd, 12 commits behind main at inspection; its tree lacks the retained-assets archive. The separate migration branch codex/poetics-supabase-migrations is at 5bb2cea52aa049044592379a91e887c1ef637fb0, 13 commits ahead and 11 behind main. Its six SQL scripts are migration/audit work, not proof that the canonical ledger has been fully reconciled.
- The Sites preview was last observed as V55 with the five city shortcuts matching the inspected main feature. This is a feature/marker comparison only; no byte-for-byte GitHub-to-Sites sync is established.

### Current Supabase staging audit

Fresh read-only inventory for project tknahlnirtnanzqqvufb: 449 nodes, 31 aliases, 664 connections, 664 claims, 188 sources, 664 claim-source links, 7 artifacts, 504 artifact chunks, 198 ledger sections, 38 research runs, 91 search queries, 0 decisions and 8 audit events.

All seven artifact payloads pass the database-internal byte/chunk/SHA256 reconstruction check. The 16 declared foreign keys are validated. All 664 connection endpoints and claim/source references resolve. These checks establish internal integrity, not completeness against the current Drive file. All 664 imported graph claims have NULL run_id; do not invent run associations. All 38 normalized runs and 91 query rows resolve internally, but decision and status history coverage against the current ledger remains open.

RLS is enabled on all 13 poetics tables, with zero policies and no table grants observed for PUBLIC, anon, authenticated or service_role. This describes configured restrictions; API denial, a narrowly authorised application identity, and durable backup/recovery have not been demonstrated. Do not widen access as part of this checkpoint.

### Open gates

1. Obtain an exact current same-ID Drive export and revision metadata if available; reconcile the DB082 source-identity mismatch and preserve all newer text before any write.
2. Finish full section/run/query/decision/status reconciliation without inferring claim-to-run links.
3. Complete narrowly scoped authorized access and unauthorized-denial checks, plus a durable recovery/restore demonstration, without public exposure.
4. Continue source-backed node and connection review. P012 (the MJC Echeruo / ANA Imo poetry-prize identity) remains open; the latest search found no new corroborating source, so no connection was added.
5. Keep the retained archive and Sites preview as separate source states; do not assume branch or deployment synchronization.

No database rows, access settings, Drive content, Sites content or live WordPress content were changed during this checkpoint.

## Staging app connection overlay — 16 October 2026

This branch starts from the current `main` app commit `0988b3197f00ade4ed6e1ee55503b6a09ddbbf1c` and preserves the existing SQL history above. The staging client adds three UI bundle updates plus the Supabase RPC client, and adds migrations `007_atlas_snapshots.sql` and `008_public_atlas_api.sql`.

The last local staging verification read snapshot `github-main-0988b31-preview75-reconciled-sql-20261016` with 458 records and 673 connections. The browser can fall back to the bundled Atlas if the database is unavailable. Submissions go only to pending review. No submission or evidence record was created by this Git synchronization.

The snapshot payload is not included in Git. It remains in the Supabase project; these SQL files contain schema and RPC definitions only. The database should not be reset from this repository without a separately verified seed export and integrity check. The public publishable client key is used by the browser; no service-role credential is tracked.

The branch is not merged to `main` and no hosting or WordPress deployment was triggered.



## Atlas read overlay — 17 October 2026

The Supabase project’s selected database branch is labelled `main PRODUCTION`. The local staging app already calls `public.read_poetics_atlas_snapshot()`; that function had returned only the fixed Version 75 snapshot, omitting reconciled ledger records held in normalized tables.

Migration `009_overlay_reconciled_ledger_records.sql` updates that read function without replacing the original snapshot or changing normalized source, claim, connection, artifact, or submission records. It appends only documented records from the reconciled ledger artifact when their IDs are absent, and imported relationships supported by that artifact when their endpoints/label tuple is absent. Submission still enters the pending-review queue. The migration was applied directly in Supabase on 17 October and then recorded in commit `6896634` on the open staging review branch; this GitHub commit does not rerun or merge the database change.

Read verification returned 458 records and 673 connections, including four YOPAFEST/MCN/Yobe records and three festival connections. A fresh local staging Atlas search showed four results and the event’s three connections. No public website deployment occurred. The frozen snapshot remains in Supabase; the full raw research payloads remain separately preserved in the database artifact tables and canonical Drive ledger.


## Supabase authority and history reconciliation — 17 October 2026

By explicit user instruction, Supabase project `tknahlnirtnanzqqvufb` is the authoritative current source for Poetics Atlas data and reconciled research, effective 11:36 Africa/Lagos. The same decision is recorded in `poetics.decisions` as `CUTOVER-20261017-SUPABASE-AUTHORITY`. The latest Drive capture is retained in Supabase as provenance and recovery evidence; it is no longer the current authority.

The exact latest source capture is 660,867 bytes, SHA256 `e29d591dd91a08f1cdce79afecc97459315c7a3cc85ea8a288d677aeb32a3199`. Its 4,632 source lines are retained in `history_lines`; all 190 sections reconstruct exactly. A source-linked retrieval index adds 189 run-heading references, 145 retrospective run index rows with unknown actors/dates left NULL, and 1,361 line passages. All passage hashes match their referenced text. Classification tags are retrieval aids only, not atomic factual claims. Graph counts remain 463 nodes, 679 connections and 681 claims; no graph additions were made by the index.

The 17 October P012 search capture records five exact queries across system1/system2 search. The returned NewsTap descriptor is secondary evidence only and does not identify a prize edition. No P012 node, claim or connection was added; the prize identity remains open.

The private history tables have RLS enabled and no anon/authenticated SELECT grants. No grant was widened and no site was changed. Remaining verification: typed semantic history coverage is incomplete, real HTTP/API transport could not be tested from this environment, and the packaged post-snapshot recovery delta has not yet been replay-tested in isolation. The earlier 18-table base restore passed independently; its proof does not cover this later delta.

Migration `20261017101308_poetics_source_linked_history_reconciliation.sql` records the private source-linked history schema. Keep this branch private and staging-only; no payload dumps, credentials, public-access changes, PR merge, or site deployment are included.


## Verification checkpoint — 17 October 2026, 11:30 UTC

The latest same-ID Drive read returned modifiedTime 2026-10-17T09:18:44.944Z and 660,867 bytes, SHA256 `e29d591dd91a08f1cdce79afecc97459315c7a3cc85ea8a288d677aeb32a3199`. It is byte-identical to Supabase artifact `drive-exact-20261017-verification-receipt`; the project artifact digest, reconstructed ordered chunks and reconstructed source lines match. This verifies the current capture, not a Google revision ID (the provider did not expose one).

Fresh database inventory: 463 nodes, 679 connections, 681 claims, 189 sources, 41 aliases, 24 artifacts, 193 research_runs, 146 search_queries and 4 decisions. All 24 artifact SHA256 digests match original_bytes; all 20 poetics tables have RLS enabled and zero direct table grants to PUBLIC, anon, authenticated or service_role. Stable IDs, source URLs, audited FK references and graph endpoints have no gaps. The two anon SECURITY DEFINER RPCs are the reviewed public Atlas snapshot and validated pending-review submission paths. Supabase organization plan is Free.

The latest source has 4,632 unique sequential lines, 190 sections, 189 heading references and 1,361 passage locators. Ten additional historical exact queries from EV074, EV080 and EV081 were normalized in `011_historical_query_batches_20261017.sql`. Their execution timestamps remain NULL; aggregate batch yields remain explicitly aggregate. Audit event 24’s query count of 11 was corrected by event 25 to 10. The earlier 136 typed query rows plus these 10 yield 146. Typed normalization is still incomplete: the source index labels 452 passages as query history and 417 as decision history; those retrieval tags do not themselves constitute normalized semantic records.

GitHub main is `0988b3197f00ade4ed6e1ee55503b6a09ddbbf1c`; `poetics-staging` remains `a221c05668739a15c0b1f664c5ab2d61bea6ebdd`; the retained archive is present only on main and its exact bytes/hash/member list were verified. Sites V76 source is `e22287464f447cfec4f664c3b9ddf7be7b870b2e`; its deployment succeeded and the site was not changed. GitHub and Sites remain distinct source states; no automatic synchronization is assumed.

Technical completion remains open. The packaged recovery delta after the earlier verified base restore has not been replay-tested. The Free project has no automatic backups; no recurring off-site dump/restore was established. The direct HTTP/PostgREST allow/deny test remains blocked by this execution environment. No public-access widening, site update, WordPress change, main-branch merge or data export was made.
