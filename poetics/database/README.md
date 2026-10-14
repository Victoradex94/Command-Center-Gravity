# Poetics Atlas staging database

**Status: imported into private Supabase staging, not ready for cutover.** The canonical Drive ledger remains authoritative. This project is separate from WordPress.

## Current sources

- Supabase: project `Poetics Staging`, ref `tknahlnirtnanzqqvufb`, EU West. The branch selector reads `main PRODUCTION`; this is a database branch label within the separately named staging project. Dashboard showed a service-investigation banner during review.
- GitHub `main` HEAD observed 14 October 2026: `f2a92a07aa9ea158de21faa1c8b5583feaea91b9`. `poetics/dist/atlas-data.json` was last changed at `a221c05668739a15c0b1f664c5ab2d61bea6ebdd`.
- `poetics-staging` remains at `a221c05668739a15c0b1f664c5ab2d61bea6ebdd`, four commits behind main. Main contains `poetics/archives/sites-v45-retained-artifacts.tar.gz`, last changed at `efee4944d8177766173dc46411ee48bac76be155`; the path is absent from staging.
- The Sites Atlas preview currently says “Sign in required”. Its current rendered version cannot be compared with GitHub. GitHub changes do not automatically publish to Sites.
- Latest verified raw Drive download: 14 October 11:56, 153,555 bytes, SHA256 `b24cffd7c301cb92692914cd4e866da11560c3979a008cdcdfc738442047186a`. Provider revision metadata was not retrieved. A fresh read currently requires Google “Verify it’s you”.

## Current database inventory

Fresh read-only SQL confirmed that `public` contains no tables and the private `poetics` schema has 13 tables: 449 nodes, 664 connections, 664 claims, 664 claim-source links, 187 sources, 31 aliases, 4 artifact manifests, 469 artifact chunks, 114 ledger sections, 30 research runs, 78 search queries, 0 normalized decisions, and 3 audit events.

All four captured payloads were rebuilt from ordered chunks and compared with `original_bytes` and the manifest SHA256. Every payload matched:

| Artifact | Bytes | Chunks | SHA256 |
|---|---:|---:|---|
| `drive-raw-20261014-1156` | 153,555 | 20 | `b24cffd7c301cb92692914cd4e866da11560c3979a008cdcdfc738442047186a` |
| `drive-rendered-20261014-1130` | 154,655 | 20 | `5db750a0fa809b27359d1a6d88ea08c1d4e9733ea968eda0efe7729cd83c5a64` |
| `github-main-efee4944-graph-20261014` | 1,597,040 | 200 | `31009691dfc69103ba77a11672757fb8c49f2e42e0c8d29200f7836c8763522d` |
| `github-main-efee4944-zip-20261014` | 1,825,048 | 229 | `edd0097c89266cc856e1816b61f1c81af6227599ede3c3d8b093e1dfbdc702d2` |

The rendered ledger is a separate browser capture, not the original Drive file. Its `original_bytes` preserve CRLF introduced by browser paste; its `decoded_text` is LF-normalised. The restore script preserves this distinction.

A fresh access query found all 13 tables with RLS enabled, zero policies, and zero SELECT grants to `anon` or `authenticated`. This is default-deny; no authorised application read/write path has been tested.

## Remaining gates

1. Reauthenticate to Google, read the current Drive text and provider revision, preserve newer contributions, then append and read back the same file ID.
2. Reconcile current Drive against GitHub data, aliases, the retained archive, and the branch differences. Do not assume Sites sync.
3. Rerun complete stable-ID, payload, endpoint, source-URL, query, run, decision and status-history checks against the reconciled source. Raw ledger sections retain narrative status history; `poetics.decisions` has zero rows.
4. Verify a narrowly authorised application identity and unauthorised denial. Do not widen public access.
5. Demonstrate durable backup/recovery. The Supabase Free Plan reports no project backups; no restore test is complete.
6. Reconcile the Cross Country identity proposal and P012 research before importing supported new claims or connections.

## Files and operating rules

- `001_staging_schema.sql`: historical bootstrap; not idempotent and must not be rerun on this project.
- `002_import_support_schema.sql`: data-free artifact chunk schema.
- `003_integrity_audit.sql`, `005_graph_roundtrip_audit.sql`, `006_history_artifact_reconciliation.sql`: read-only audits.
- `004_restore_verified_artifact_bytes.sql`: transactional SHA256-gated restoration for all four captured payloads; not run in this read-only check.

Keep this branch private and staging-only. Commit safe schema and SQL only. Never add credentials, connection strings, ledger dumps, CSV imports, private submissions, or artifact payloads. No live WordPress change, public database/API, Sites publish, or cutover is recorded.
