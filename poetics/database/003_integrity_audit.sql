-- Read-only audit for the Poetics staging schema. Run as postgres in SQL Editor.
-- No data, security or schema changes.

-- Counts by relation.
SELECT 'artifacts' AS table_name, count(*) AS row_count FROM poetics.artifacts
UNION ALL SELECT 'artifact_import_chunks', count(*) FROM poetics.artifact_import_chunks
UNION ALL SELECT 'ledger_sections', count(*) FROM poetics.ledger_sections
UNION ALL SELECT 'research_runs', count(*) FROM poetics.research_runs
UNION ALL SELECT 'search_queries', count(*) FROM poetics.search_queries
UNION ALL SELECT 'nodes', count(*) FROM poetics.nodes
UNION ALL SELECT 'aliases', count(*) FROM poetics.aliases
UNION ALL SELECT 'sources', count(*) FROM poetics.sources
UNION ALL SELECT 'claims', count(*) FROM poetics.claims
UNION ALL SELECT 'claim_sources', count(*) FROM poetics.claim_sources
UNION ALL SELECT 'connections', count(*) FROM poetics.connections
UNION ALL SELECT 'decisions', count(*) FROM poetics.decisions
UNION ALL SELECT 'audit_events', count(*) FROM poetics.audit_events
ORDER BY table_name;

-- RLS posture. A policy count of zero means default-deny for API roles.
SELECT c.relname AS table_name, c.relrowsecurity AS rls_enabled,
       c.relforcerowsecurity AS rls_forced, count(p.policyname) AS policy_count
FROM pg_class c
JOIN pg_namespace n ON n.oid=c.relnamespace
LEFT JOIN pg_policies p ON p.schemaname=n.nspname AND p.tablename=c.relname
WHERE n.nspname='poetics' AND c.relkind='r'
GROUP BY c.relname,c.relrowsecurity,c.relforcerowsecurity
ORDER BY c.relname;

-- Reconstruct source artifact bytes and compare hashes. Requires pgcrypto.
WITH reconstructed AS (
  SELECT artifact_id, count(*) AS chunk_count,
         decode(string_agg(chunk_hex,'' ORDER BY part_no),'hex') AS payload
  FROM poetics.artifact_import_chunks GROUP BY artifact_id
)
SELECT a.id AS artifact_id, a.sha256 AS expected_sha256,
       encode(extensions.digest(r.payload,'sha256'),'hex') AS reconstructed_sha256,
       octet_length(r.payload) AS reconstructed_bytes, r.chunk_count,
       a.sha256=encode(extensions.digest(r.payload,'sha256'),'hex') AS hash_match,
       octet_length(a.original_bytes) AS stored_original_bytes
FROM poetics.artifacts a LEFT JOIN reconstructed r ON r.artifact_id=a.id
ORDER BY a.id;

-- Detect missing graph and history references.
SELECT
 (SELECT count(*) FROM poetics.connections c LEFT JOIN poetics.nodes n ON n.id=c.subject_id WHERE n.id IS NULL) AS missing_subjects,
 (SELECT count(*) FROM poetics.connections c LEFT JOIN poetics.nodes n ON n.id=c.object_id WHERE n.id IS NULL) AS missing_objects,
 (SELECT count(*) FROM poetics.connections c LEFT JOIN poetics.claims x ON x.id=c.claim_id WHERE x.id IS NULL) AS missing_connection_claims,
 (SELECT count(*) FROM poetics.claim_sources cs LEFT JOIN poetics.sources s ON s.id=cs.source_id WHERE s.id IS NULL) AS missing_claim_sources,
 (SELECT count(*) FROM poetics.search_queries q LEFT JOIN poetics.research_runs r ON r.id=q.run_id WHERE r.id IS NULL) AS missing_query_runs,
 (SELECT count(*) FROM poetics.research_runs r LEFT JOIN poetics.ledger_sections l ON (l.artifact_id,l.ordinal)=(r.artifact_id,r.section_ordinal) WHERE l.ordinal IS NULL) AS missing_run_sections;

-- Current executor's view of API-role privileges.
SELECT current_user,
       has_schema_privilege('anon','poetics','USAGE') AS anon_schema_usage,
       has_table_privilege('anon','poetics.nodes','SELECT') AS anon_nodes_select,
       has_schema_privilege('authenticated','poetics','USAGE') AS authenticated_schema_usage,
       has_table_privilege('authenticated','poetics.nodes','SELECT') AS authenticated_nodes_select;
