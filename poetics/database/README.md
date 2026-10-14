# Poetics Atlas staging database

This directory documents the private Supabase staging migration for Poetics Atlas. The canonical Drive ledger remains authoritative until source reconciliation, history coverage, access checks, and recovery are verified. The database is at project tknahlnirtnanzqqvufb. Do not connect this staging database to the live WordPress site.

## Current verified state (14 October 2026)

- Dashboard project: Poetics Staging; project URL: https://tknahlnirtnanzqqvufb.supabase.co
- The project dashboard shows a technical-issue investigation banner. Read-only checks succeeded during this session.
- Tables contain 449 nodes, 664 claims, 31 aliases, 187 sources, 4 artifact records, 664 connections, 664 claim-source links, 30 research runs, 78 queries, 449 artifact chunks, 114 ledger sections, 3 audit events, and 0 decisions.
- All tables in the poetics schema have row-level security enabled and no policies. Neither anon nor authenticated has schema usage or node-select privilege. This is private default-deny posture.
- Referential summaries show no missing run-to-section links, query-to-run links, or connection endpoints. Exact source-byte reconstruction hashes matched the three archived captures inspected.
- The ledger's decision/status history has not been fully represented in the decisions table. An authorised application identity read/write test and a durable recovery test remain open.

## Files

- 001_staging_schema.sql: original bootstrap schema used in the staging project. It is a record of setup; it is not idempotent and must not be rerun against the existing project.
- 002_import_support_schema.sql: safe, data-free schema for artifact chunks. Raw data inserts are intentionally excluded.
- 003_integrity_audit.sql: read-only row-count, RLS, chunk-hash and relationship checks.

## Operating rules

1. Keep this branch and database private and staging-only. Never place API keys, connection strings, ledger exports, CSVs, private submissions, or artifact payloads in GitHub.
2. Inspect the current Drive revision and GitHub main before any new import. Preserve newer source text and record source commit IDs and divergence.
3. Do not label Drive as superseded until decision/status history, role-based access, and recovery are verified and the user has a clear cutover record.
4. Preserve stable IDs, original JSON payloads, source URLs, query wording, dates as written, evidence scope, uncertainty, aliases, and all connections.
5. SQL files in this directory are reviewable records. They are not connected to Supabase migrations and are not automatically deployed. The dashboard currently shows no migration history and no GitHub integration.


## Latest byte-level recheck (14 October 2026)

- The Drive source payload reconstructs to 153,555 bytes and matches its recorded SHA-256. The GitHub graph snapshot reconstructs to 1,597,040 bytes and matches. The GitHub archive reconstructs to 1,825,048 bytes and matches.
- A fourth artifact manifest, drive-rendered-20261014-1130, has no imported chunks and zero stored bytes. Its original rendered payload is not preserved in Supabase. Keep this as an open evidence gap; do not treat the three verified payloads as all four artifact records.
- The separate search found 0 decisions. The full ledger sections retain source text, but normalized decision/status history coverage remains incomplete.
