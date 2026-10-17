-- Poetics staging cutover gates, 17 October 2026.
-- READ-ONLY audit. No credentials, private ledger text or database exports.
-- Cutover was NOT recorded. Drive remains authoritative.
-- Exact Drive capture: 649081 bytes, provider-modified 2026-10-17T07:26:20.679Z,
-- SHA256 2c3f2c5eac5802438ad3901d32ea5235e2b2bc1002cadc3da0b8d289b77b156b.
-- Registered only after 13 staged chunks reconstructed exactly; 257 sections
-- concatenate byte-for-byte to that source. Older artifacts were preserved.
-- Supabase project is named Poetics Staging; selected base branch reads main Production.
-- Observed normalized graph: 463 nodes, 679 connections, 681 claims, 189 sources.
-- These totals include 5 proposed research nodes and 6 proposed relationships;
-- the app read RPC still returned 458 records / 673 edges, unchanged.
--
-- SQL role tests completed:
-- anon read RPC: allowed, 458/673.
-- anon direct poetics schema read: denied 42501.
-- authenticated read RPC: denied 42501 (not granted).
-- anon submission RPC: allowed; owner readback confirmed pending_review;
-- synthetic test transaction rolled back, zero test submissions retained.
-- These are database-role execution tests, NOT real HTTP/API client tests.
--
-- Open gates:
-- 1. Complete normalized run/query/decision/status history coverage;
--    exact raw history is now retained, but typed normalization is incomplete.
-- 2. Preserve and reconcile orphan chunk group drive-export-md-20261015-DB121:
--    52 chunks, 423048 bytes, reconstructed SHA256
--    cfb07ad89349a7955238bb4a94b81f3ae4deafd8727a3a50cbaac293dad8b3b6.
--    Upstream source capture is not verified; do not delete or invent provenance.
-- 3. Durable off-database backup plus isolated restore verification.
--    Dashboard explicitly reports Free Plan does not include project backups.
-- 4. Real API-client allow/deny tests. Do not widen grants to make tests pass.
-- 5. Fresh source-archive verification: GitHub archive blob metadata is available,
--    but this session's connector cannot return its binary bytes.
--    Sites v76 source e22287464f447cfec4f664c3b9ddf7be7b870b2e differs from
--    GitHub main 0988b3197f00ade4ed6e1ee55503b6a09ddbbf1c.
--    Sites archive metadata SHA256
--    06cc02de5da48764789dfbb8dba92e2d7279833ee27dd9855467c6018cafa8a4
--    is provider metadata, not independently rehashed bytes.
--
select jsonb_build_object('nodes',(select count(*) from poetics.nodes),'connections',(select count(*) from poetics.connections),'claims',(select count(*) from poetics.claims),'sources',(select count(*) from poetics.sources),'artifacts',(select count(*) from poetics.artifacts),'query_rows',(select count(*) from poetics.search_queries),'invalid_artifact_hashes',(select count(*) from poetics.artifacts where encode(extensions.digest(original_bytes,'sha256'),'hex')<>sha256),'dangling_connections',(select count(*) from poetics.connections c left join poetics.nodes a on a.id=c.subject_id left join poetics.nodes b on b.id=c.object_id left join poetics.claims cl on cl.id=c.claim_id where a.id is null or b.id is null or cl.id is null),'missing_source_links',(select count(*) from poetics.claims cl where not exists(select 1 from poetics.claim_sources cs where cs.claim_id=cl.id)),'source_url_gaps',(select count(*) from poetics.sources where btrim(url)=''),'synthetic_submissions_retained',(select count(*) from poetics.atlas_submissions where payload->>'name'='MIGRATION-ROLLBACK-TEST-20261017'),'rls_all',(select bool_and(c.relrowsecurity) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='poetics' and c.relkind='r'),'direct_public_grants',(select count(*) from information_schema.role_table_grants where table_schema='poetics' and grantee in ('PUBLIC','anon','authenticated','service_role')),'unregistered_chunk_groups',(select jsonb_agg(x) from(select c.artifact_id,count(*) chunks,sum(length(c.chunk_hex)/2) bytes,encode(extensions.digest(decode(string_agg(c.chunk_hex,'' order by c.part_no),'hex'),'sha256'),'hex') reconstructed_hash from poetics.artifact_import_chunks c left join poetics.artifacts a on a.id=c.artifact_id where a.id is null group by c.artifact_id) x),'typed_run_references_for_current_capture',(select count(*) from poetics.research_runs where artifact_id='drive-exact-20261017-082620')) as gate_audit;

-- Verify the lossless latest-ledger section and chunk reconstruction.
select a.id,
 encode(extensions.digest(a.original_bytes,'sha256'),'hex') = a.sha256 as source_hash_ok,
 (select convert_to(string_agg(body,'' order by ordinal),'UTF8')
  from poetics.ledger_sections where artifact_id=a.id) = a.original_bytes as sections_exact,
 (select decode(string_agg(chunk_hex,'' order by part_no),'hex')
  from poetics.artifact_import_chunks where artifact_id=a.id) = a.original_bytes as chunks_exact
from poetics.artifacts a
where a.id='drive-exact-20261017-082620';
