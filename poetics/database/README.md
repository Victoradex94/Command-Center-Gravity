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
