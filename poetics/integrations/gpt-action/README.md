# Poetics read-only GPT Action — prepared, not deployed

Source base: `codex/poetics-supabase-migrations` at `5bb2cea52aa049044592379a91e887c1ef637fb0`, schema `001_staging_schema.sql`. Work is isolated on `codex/poetics-read-action`; the migration branch, main, Sites and WordPress are unchanged.

This branch inherits an older application snapshot from the migration branch. Merge only `poetics/integrations/gpt-action/` after review; do not replace current main/Sites application files with this branch's inherited app files.

## What this provides

Four authenticated GET routes: `/nodes`, `/connections`, `/sources`, `/ledger`. No arbitrary SQL, mutation, artifact bytes/chunks, audit-event or credential endpoint. Node reads match labels and aliases. Connections include their claim status, date meaning, uncertainty, source families and supported scopes. Ledger reads require an explicit captured artifact ID and return at most 4000 characters per body with a truncation flag. Every response identifies itself as a staging snapshot. Pagination is capped at 20 rows and responses at 64 KB; errors do not expose driver messages.

The branch README reports 449 nodes/664 connections from an older import; the latest preview contains 453/667. Those database counts are source-attributed, not independently queried here. This action does not reconcile/import newer data, replace the Drive ledger, connect Preview 50 to SQL, or configure automatic GitHub/Sites/database synchronization.

## Why direct server-side Postgres

The `poetics` schema is private, revoked from PUBLIC, and has default-deny RLS with no application policies/grants documented. An Edge Function does not automatically make that schema available through PostgREST. This implementation therefore uses a server-side SQL connection and fixed parameterized SELECTs inside `BEGIN READ ONLY`, with a 3-second statement timeout. It does not expose the schema or add grants/policies. Each request releases its pooled connection and rolls back failures.

`POETICS_READ_DB_URL` must belong to a separately approved server identity able to SELECT these tables under the actual RLS configuration. No automatic fallback to built-in administrator credentials, Supabase secret keys or ordinary authenticated users is provided. A normal role with no RLS policy may see no rows; deployment acceptance must confirm a known fixture, not treat an empty response as working authorization. Creating a new SQL reader role/grants/RLS exception would be a separate database access change; none is executed or scripted here. Keep the connection string only in Supabase function secrets, using the appropriate TLS-enabled pooled connection. Never put it in GPT authentication, browser code, repository, logs or this chat.

## Dedicated Action authentication

The GPT receives only a separate high-entropy Action token through its Builder authentication settings (API Key, Bearer). The function stores its SHA-256 hex digest in `POETICS_ACTION_TOKEN_SHA256`; token comparison uses SHA-256 and a fixed-length comparison. Set token/hash through secure local tooling and Supabase Secrets without committing or pasting real values. Generate at least 32 random bytes. Rotation means replacing the server digest and the GPT's encrypted token. No real secret is included in these files.

`supabase/config.toml` disables gateway JWT verification only for this function because the GPT token is not a Supabase JWT. The handler rejects unauthenticated requests itself before any query. This is configuration text only; it has not changed deployed settings. No anonymous data access is supported.

## Activation steps — owner environment required

1. Review/approve the SQL reader identity against live staging permissions; preserve existing private schema and RLS unless a separate change is authorized.
2. Set `POETICS_READ_DB_URL` and `POETICS_ACTION_TOKEN_SHA256` as server secrets. No default connection is accepted.
3. From this directory, use an authenticated Supabase CLI: `supabase functions deploy poetics-read --project-ref tknahlnirtnanzqqvufb`. Confirm the deployed function config and secret presence; deployment is not performed here.
4. Verify live missing/wrong-token denial, POST denial, a known node and claim/source result, ledger artifact selection, size/time bounds and failure behaviour. Confirm no data writes. Verify denied roles/known fixture so RLS-empty results cannot pass as success.
5. Import `openapi.json` into the intended GPT's Actions and configure only the dedicated bearer token. Test the four operations there before marking connected. Keep that GPT's audience within the authorized research group; no sharing change is included.

## Verification performed / limits

`node test-read-action.mjs` passes authentication denial without query, GET-only routing, bounds/repeated/unsupported parameter rejection, literal parameterized injection text, uncertainty preservation, explicit ledger capture, generic failure/no credential echo, response-size cap and no-store headers. `node --check` checks JS/TS syntax only. Deno is unavailable in this runtime; remote dependencies, actual Postgres driver execution, RLS/SQL permissions, live schema/data, deployment and GPT Builder configuration are NOT verified. No Supabase connector/session/API credentials are available here. Do not call this connected or production-ready.

## Official references checked 14 October 2026

- https://developers.openai.com/api/docs/actions/authentication — API key authentication in GPT editor.
- https://supabase.com/docs/guides/functions/connect-to-postgres — server-side SQL clients and pooled connections.
- https://supabase.com/docs/guides/functions/function-configuration — per-function gateway JWT setting.
- https://supabase.com/docs/guides/functions/secrets — server-only secrets.
