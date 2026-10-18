-- Read-only focused audit for source-byte, ledger-history, and graph coverage.
-- Run in the Poetics staging project as postgres. This script performs no writes.
-- It intentionally reports counts by artifact: duplicate section counts can be
-- legitimate only when they belong to distinct, identified source captures.

-- 1. Compare manifest bytes with ordered imported chunks and stored bytea.
WITH chunk_stats AS (
  SELECT artifact_id,count(*) AS chunk_count,min(part_no) AS first_part,
         max(part_no) AS last_part,string_agg(chunk_hex,'' ORDER BY part_no) AS joined_hex
  FROM poetics.artifact_import_chunks GROUP BY artifact_id
), rebuilt AS (
  SELECT a.id,a.source_uri,a.revision,a.sha256,a.original_bytes,
         octet_length(a.original_bytes) AS stored_bytes,cs.chunk_count,cs.first_part,cs.last_part,
         CASE WHEN cs.joined_hex IS NOT NULL THEN decode(cs.joined_hex,'hex') END AS rebuilt_bytes
  FROM poetics.artifacts a LEFT JOIN chunk_stats cs ON cs.artifact_id=a.id
)
SELECT id,source_uri,revision,sha256,stored_bytes,
  CASE WHEN rebuilt_bytes IS NULL THEN 0 ELSE octet_length(rebuilt_bytes) END AS rebuilt_bytes,
  chunk_count,first_part,last_part,
  CASE WHEN rebuilt_bytes IS NULL THEN NULL ELSE encode(extensions.digest(rebuilt_bytes,'sha256'),'hex') END AS rebuilt_sha256,
  CASE WHEN rebuilt_bytes IS NULL THEN NULL ELSE encode(extensions.digest(rebuilt_bytes,'sha256'),'hex')=sha256 END AS chunks_match_manifest,
  CASE WHEN rebuilt_bytes IS NULL THEN NULL ELSE original_bytes=rebuilt_bytes END AS stored_bytes_match_chunks
FROM rebuilt ORDER BY id;

-- 2. Show section/run/query/decision inventories per source artifact.
SELECT a.id AS artifact_id,a.media_type,octet_length(a.original_bytes) AS stored_bytes,
  count(DISTINCT ls.ordinal) AS section_count,count(DISTINCT rr.id) AS research_run_count,
  count(DISTINCT sq.id) AS search_query_count,count(DISTINCT d.id) AS decision_count,
  count(DISTINCT CASE WHEN rr.id IS NOT NULL AND ls.ordinal IS NULL THEN rr.id END) AS runs_without_section
FROM poetics.artifacts a
LEFT JOIN poetics.ledger_sections ls ON ls.artifact_id=a.id
LEFT JOIN poetics.research_runs rr ON rr.artifact_id=a.id
LEFT JOIN poetics.search_queries sq ON sq.run_id=rr.id
LEFT JOIN poetics.decisions d ON d.run_id=rr.id
GROUP BY a.id,a.media_type,octet_length(a.original_bytes) ORDER BY a.id;

-- 3. Identify missing run links, incomplete query provenance, and duplicate IDs.
SELECT 'run_missing_ledger_section' AS issue,rr.id AS record_id,rr.artifact_id AS detail
FROM poetics.research_runs rr
LEFT JOIN poetics.ledger_sections ls ON ls.artifact_id=rr.artifact_id AND ls.ordinal=rr.section_ordinal
WHERE ls.ordinal IS NULL
UNION ALL
SELECT 'query_missing_run',sq.id,sq.run_id FROM poetics.search_queries sq
LEFT JOIN poetics.research_runs rr ON rr.id=sq.run_id WHERE rr.id IS NULL
UNION ALL
SELECT 'query_missing_provenance',sq.id,concat_ws('; ',
  CASE WHEN nullif(sq.exact_query,'') IS NULL THEN 'exact_query' END,
  CASE WHEN nullif(sq.engine,'') IS NULL THEN 'engine' END,
  CASE WHEN nullif(sq.yield_text,'') IS NULL THEN 'yield_text' END,
  CASE WHEN nullif(sq.attribution,'') IS NULL THEN 'attribution' END)
FROM poetics.search_queries sq
WHERE nullif(sq.exact_query,'') IS NULL OR nullif(sq.engine,'') IS NULL
   OR nullif(sq.yield_text,'') IS NULL OR nullif(sq.attribution,'') IS NULL
UNION ALL
SELECT 'decision_missing_run',d.id,COALESCE(d.status,'') FROM poetics.decisions d
LEFT JOIN poetics.research_runs rr ON rr.id=d.run_id
WHERE d.run_id IS NOT NULL AND rr.id IS NULL
ORDER BY issue,record_id;

-- 4. Graph inventory and connection/claim/source completeness.
SELECT 'nodes' AS record_type,count(*) AS rows,count(DISTINCT id) AS distinct_ids,
  count(*) FILTER (WHERE original_record IS NULL) AS missing_original_payload FROM poetics.nodes
UNION ALL
SELECT 'connections',count(*),count(DISTINCT id),count(*) FILTER (WHERE original_record IS NULL) FROM poetics.connections
UNION ALL
SELECT 'claims',count(*),count(DISTINCT id),count(*) FILTER (WHERE original_record IS NULL) FROM poetics.claims
UNION ALL
SELECT 'claim_sources',count(*),count(DISTINCT (claim_id,source_id,relationship)),
  count(*) FILTER (WHERE nullif(supported_scope,'') IS NULL) FROM poetics.claim_sources
UNION ALL
SELECT 'aliases',count(*),count(DISTINCT (node_id,alias)),count(*) FILTER (WHERE nullif(alias,'') IS NULL) FROM poetics.aliases
UNION ALL
SELECT 'sources',count(*),count(DISTINCT id),count(*) FILTER (WHERE nullif(url,'') IS NULL) FROM poetics.sources
UNION ALL
SELECT 'decisions',count(*),count(DISTINCT id),
  count(*) FILTER (WHERE nullif(statement,'') IS NULL OR nullif(status,'') IS NULL) FROM poetics.decisions;

-- 5. Query schema security posture. This reports grants; it changes none.
SELECT n.nspname AS schema_name,
  has_schema_privilege('anon',n.oid,'USAGE') AS anon_schema_usage,
  has_schema_privilege('authenticated',n.oid,'USAGE') AS authenticated_schema_usage
FROM pg_namespace n WHERE n.nspname='poetics';

SELECT c.relname AS table_name,c.relrowsecurity AS rls_enabled,
  has_table_privilege('anon',c.oid,'SELECT') AS anon_select,
  has_table_privilege('anon',c.oid,'INSERT') AS anon_insert,
  has_table_privilege('authenticated',c.oid,'SELECT') AS authenticated_select,
  has_table_privilege('authenticated',c.oid,'INSERT') AS authenticated_insert,
  has_table_privilege('authenticated',c.oid,'UPDATE') AS authenticated_update
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='poetics' AND c.relkind='r' ORDER BY c.relname;

-- 6. Report durable recovery mechanisms visible to the project database role.
-- Supabase managed backups/PITR and restore tests must also be verified in its UI;
-- SQL catalog inspection alone does not prove a successful restore.
SELECT current_database() AS database_name,current_setting('server_version') AS postgres_version,
  current_setting('archive_mode') AS archive_mode,current_setting('wal_level') AS wal_level;
