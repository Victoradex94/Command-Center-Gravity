-- Poetics staging migration verification, 17 October 2026.
-- Current checkpoint supersedes earlier open-gate notes in this file.
-- Supabase is authoritative by explicit user instruction, 17 Oct 2026 11:36 WAT.\n-- Technical verification remains open; no site update or grant widening.
--
-- Passed: exact latest Drive import (654893 bytes; SHA256
-- 08a50dd198f25de9f532d84c3cd63aec295666749f43d9848fccaf3816d6d627);
-- section/chunk round trips; all source hashes; zero broken endpoints,
-- unvalidated FKs, missing claim sources, blank source URLs or public table grants.
-- All source history is also preserved in ordered history_lines. Unknown dates,
-- engines and attribution remain unknown. Retrospective semantic normalization
-- into typed run/query/decision tables is incomplete; no completion is asserted.
-- Unknown-provenance chunk group DB121 retained under its existing ID and
-- registered as quarantined, non-authoritative bytes. No claims derived.
--
-- Recovery: a consistent18-table package was downloaded, rehashed, reuploaded
-- from the saved file, and restored into an isolated schema. Every table's
-- JSON row payload matched exactly; constraints validated; rollback confirmed.
-- 16685 history lines, 986 sections, 19 source artifacts, 463 nodes /679 edges.
-- Recovery ciphertext 11087991 bytes; SHA256
-- 2bdb051b6006755a08c6345b56e78da4432c44df746a778e550e7cce3c014d67.
-- Excludes backup-wrapper rows/chunks to avoid recursive backup, plus hosting,
-- Auth/project settings and credentials. This is scoped research recovery.
--
-- Access: real SQL-role read, pending-review write and denied private reads
-- passed; synthetic transaction rolled back. Direct HTTP verification did NOT
-- pass: shell403 network policy and browser ERR_BLOCKED_BY_CLIENT.
-- verify_http_cutover.py records the remaining HTTP checks without credentials.
-- Do not declare cutover until that access gate and history review are closed.
-- Unintended rls_auto_enable() execution revoked from public API roles.
-- Remaining advisors: intentional private default-deny RLS information and
-- two approved anon SECURITY DEFINER RPC warnings. No access widening.
--
-- Sources: main0988b3197f00ade4ed6e1ee55503b6a09ddbbf1c;
-- poetics-staging a221c05668739a15c0b1f664c5ab2d61bea6ebdd;
-- Sitesv76 e22287464f447cfec4f664c3b9ddf7be7b870b2e.
-- Sites checkout was inspected read-only:386 files identical to main poetics/,
-- 41 Sites-only retained assets, two same-path differences (README.md and an
-- inactive older directory bundle). Five key data JSON layers match exactly.
-- Active directory bundle matches main. Hosted site shows453 entries while
-- DB read RPC returns458/673. Local staging, hosting and DB are separate states.
-- Retained archive verified946585 bytes/SHA256217542cedef4b9f8f302ec66552cc75bb79e12a4bdf2926ab4c896b435028832,
-- 38 members (corrects earlier37 note). No site changes or publishing.
--
select jsonb_build_object('nodes',(select count(*) from poetics.nodes),'connections',(select count(*) from poetics.connections),'claims',(select count(*) from poetics.claims),'sources',(select count(*) from poetics.sources),'artifacts',(select count(*) from poetics.artifacts),'query_rows',(select count(*) from poetics.search_queries),'invalid_artifact_hashes',(select count(*) from poetics.artifacts where encode(extensions.digest(original_bytes,'sha256'),'hex')<>sha256),'dangling_connections',(select count(*) from poetics.connections c left join poetics.nodes a on a.id=c.subject_id left join poetics.nodes b on b.id=c.object_id left join poetics.claims cl on cl.id=c.claim_id where a.id is null or b.id is null or cl.id is null),'missing_source_links',(select count(*) from poetics.claims cl where not exists(select 1 from poetics.claim_sources cs where cs.claim_id=cl.id)),'source_url_gaps',(select count(*) from poetics.sources where btrim(url)=''),'synthetic_submissions_retained',(select count(*) from poetics.atlas_submissions where payload->>'name'='MIGRATION-ROLLBACK-TEST-20261017'),'rls_all',(select bool_and(c.relrowsecurity) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='poetics' and c.relkind='r'),'direct_public_grants',(select count(*) from information_schema.role_table_grants where table_schema='poetics' and grantee in ('PUBLIC','anon','authenticated','service_role')),'unregistered_chunk_groups',(select jsonb_agg(x) from(select c.artifact_id,count(*) chunks,sum(length(c.chunk_hex)/2) bytes,encode(extensions.digest(decode(string_agg(c.chunk_hex,'' order by c.part_no),'hex'),'sha256'),'hex') reconstructed_hash from poetics.artifact_import_chunks c left join poetics.artifacts a on a.id=c.artifact_id where a.id is null group by c.artifact_id) x),'typed_run_references_for_current_capture',(select count(*) from poetics.research_runs where artifact_id='drive-exact-20261017-082620')) as gate_audit;


select a.id,
 encode(extensions.digest(a.original_bytes,'sha256'),'hex')=a.sha256 source_hash_ok,
 (select decode(string_agg(chunk_hex,'' order by part_no),'hex') from poetics.artifact_import_chunks where artifact_id=a.id)=a.original_bytes chunks_exact,
 (select convert_to(string_agg(raw_line,E'\n' order by line_no),'UTF8') from poetics.history_lines where artifact_id=a.id)=a.original_bytes history_exact
from poetics.artifacts a where media_type in ('text/markdown','text/plain');


-- Current authority and lossless-history verification. Read-only.
select jsonb_build_object(
 'authority_decision',(select jsonb_build_object('id',id,'status',status) from poetics.decisions where id='CUTOVER-20261017-SUPABASE-AUTHORITY'),
 'latest_source',(select jsonb_build_object('bytes',octet_length(original_bytes),'sha256',sha256,'hash_ok',encode(extensions.digest(original_bytes,'sha256'),'hex')=sha256) from poetics.artifacts where id='drive-exact-20261017-verification-receipt'),
 'history_lines',(select count(*) from poetics.history_lines where artifact_id='drive-exact-20261017-verification-receipt'),
 'run_references',(select count(*) from poetics.history_run_references where artifact_id='drive-exact-20261017-verification-receipt'),
 'history_passages',(select count(*) from poetics.history_passages where artifact_id='drive-exact-20261017-verification-receipt'),
 'passage_hash_mismatches',(select count(*) from poetics.history_passages p where p.artifact_id='drive-exact-20261017-verification-receipt' and p.source_sha256<>encode(extensions.digest(convert_to((select string_agg(h.raw_line,E'\\n' order by h.line_no) from poetics.history_lines h where h.artifact_id=p.artifact_id and h.line_no between p.line_from and p.line_to),'UTF8'),'sha256'),'hex')),
 'new_p012_queries',(select count(*) from poetics.search_queries where run_id='WEB-P012-ANA-SEARCH-20261017-1136'),
 'site_updated',false,
 'public_access_widened',false
) as current_checkpoint;
