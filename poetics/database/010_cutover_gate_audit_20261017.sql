-- Poetics Atlas migration gate audit, 17 October 2026.
-- Current audit rerun after user-directed Supabase authority decision.
-- Project: tknahlnirtnanzqqvufb (project name Poetics Staging; database branch UI reads main PRODUCTION).
-- Authority designation is user-directed and recorded; technical completion remains open.
--
-- Latest canonical Drive artifact is unchanged since its 09:18:44.944Z modifiedTime:
-- 660867 bytes, SHA256 e29d591dd91a08f1cdce79afecc97459315c7a3cc85ea8a288d677aeb32a3199.
-- Supabase original_bytes hash, ordered chunk reconstruction and history_lines reconstruction match exactly.
-- Latest capture contains 4632 distinct sequential source lines, 190 sections, 189 heading references and 1361 indexed passages.
-- There are no passage hash mismatches (query below).
--
-- Current graph/index counts: 463 nodes, 679 connections, 681 claims, 681 claim-source links,
-- 189 sources, 41 aliases, 24 artifacts, 193 research_runs, 136 search_queries and 4 decisions.
-- Stable IDs are unique. All audited foreign keys, source references, aliases and connection endpoints resolve.
-- All 24 artifact original_bytes hashes match manifests; source URLs are nonblank.
-- Payload JSON is preserved as source-shaped records, not assumed to be database row objects.
-- Four research_runs have no source-heading locator: earliest migration capture, two supplemental/recheck captures,
-- and the 17 October five-query search capture. These are explicitly indexed supplemental runs.
--
-- Access: all 20 poetics tables have RLS enabled and no table grants to PUBLIC, anon, authenticated or service_role.
-- The only anon grants are two reviewed SECURITY DEFINER RPCs:
-- read_poetics_atlas_snapshot exposes the intended public Atlas; submit_poetics_atlas_record validates submissions
-- into pending review. Direct PostgREST transport is still unverified from this environment.
-- Supabase org is Free plan; official docs say free projects should make regular off-site logical exports.
-- The scoped 18-table recovery package and base restore passed; its post-snapshot delta is hash-checked but not replay-tested.
--
-- Source state: main 0988b3197f00ade4ed6e1ee55503b6a09ddbbf1c; poetics-staging a221c05668739a15c0b1f664c5ab2d61bea6ebdd;
-- separate private review branch contains migration code. Sites source V76 commit e22287464f447cfec4f664c3b9ddf7be7b870b2e.
-- Sites deployment is succeeded and unchanged. No Site, WordPress, GitHub main or public permission was changed.
--
-- Still open: complete source-by-source semantic normalization of historical exact queries, results, decisions/status;
-- test the post-snapshot delta restore in isolation; establish durable recurring/off-site recovery for the Free project;
-- perform direct HTTP allow/deny checks from an authorized environment. Do not claim all technical gates passed.

select jsonb_build_object(
 'authority_decision',(select jsonb_build_object('id',id,'status',status) from poetics.decisions where id='CUTOVER-20261017-SUPABASE-AUTHORITY'),
 'latest_source',(select jsonb_build_object('bytes',octet_length(original_bytes),'sha256',sha256,'hash_ok',encode(extensions.digest(original_bytes,'sha256'),'hex')=sha256) from poetics.artifacts where id='drive-exact-20261017-verification-receipt'),
 'history_lines',(select count(*) from poetics.history_lines where artifact_id='drive-exact-20261017-verification-receipt'),
 'run_references',(select count(*) from poetics.history_run_references where artifact_id='drive-exact-20261017-verification-receipt'),
 'history_passages',(select count(*) from poetics.history_passages where artifact_id='drive-exact-20261017-verification-receipt'),
 'passage_hash_mismatches',(select count(*) from poetics.history_passages p where p.artifact_id='drive-exact-20261017-verification-receipt' and p.source_sha256<>encode(extensions.digest(convert_to((select string_agg(h.raw_line,E'\n' order by h.line_no) from poetics.history_lines h where h.artifact_id=p.artifact_id and h.line_no between p.line_from and p.line_to),'UTF8'),'sha256'),'hex')),
 'artifact_bad_hashes',(select count(*) from poetics.artifacts where encode(extensions.digest(original_bytes,'sha256'),'hex')<>sha256),
 'nodes',(select count(*) from poetics.nodes),
 'connections',(select count(*) from poetics.connections),
 'claims',(select count(*) from poetics.claims),
 'sources',(select count(*) from poetics.sources),
 'query_rows',(select count(*) from poetics.search_queries),
 'decisions',(select count(*) from poetics.decisions),
 'rls_enabled_tables',(select count(*) from pg_tables where schemaname='poetics' and rowsecurity),
 'direct_table_grants',(select count(*) from information_schema.role_table_grants where table_schema='poetics' and grantee in ('PUBLIC','anon','authenticated','service_role')),
 'site_updated',false,
 'public_access_widened',false
) as current_checkpoint;
