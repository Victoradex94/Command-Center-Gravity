# Poetics Atlas staging database

**Status: imported into private Supabase staging, not ready for cutover.** The canonical Drive ledger remains authoritative. This project is separate from WordPress.

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
