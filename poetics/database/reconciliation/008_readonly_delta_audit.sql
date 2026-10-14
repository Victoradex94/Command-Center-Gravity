-- Run before AND after 007. Read-only; never rewrites ordinal-based IDs.
SELECT 'nodes' AS kind,count(*) AS rows FROM poetics.nodes UNION ALL
SELECT 'connections',count(*) FROM poetics.connections UNION ALL
SELECT 'claims',count(*) FROM poetics.claims UNION ALL
SELECT 'claim_sources',count(*) FROM poetics.claim_sources UNION ALL
SELECT 'sources',count(*) FROM poetics.sources UNION ALL
SELECT 'aliases',count(*) FROM poetics.aliases;
SELECT id,label,record_status,artifact_id,uncertainty FROM poetics.nodes
 WHERE id IN ('yopafest-2021','yobe-arts-council','yobe-youth-sports-ministry','mcn-programme') ORDER BY id;
SELECT c.id,c.subject_id,c.predicate,c.object_id,cl.evidence_status,cl.date_text,cl.date_role,cl.uncertainty,
 s.url,s.source_family,cs.supported_scope FROM poetics.connections c
 JOIN poetics.claims cl ON cl.id=c.claim_id JOIN poetics.claim_sources cs ON cs.claim_id=cl.id
 JOIN poetics.sources s ON s.id=cs.source_id WHERE c.subject_id='yopafest-2021' ORDER BY c.id;
-- The historical node/edge/claim/alias checks in 005 must still pass.
-- Exact old source coverage is now a SUBSET, so 005's global source count/extra
-- source query must be interpreted as one intentionally added source, not loss.
WITH old_graph AS (SELECT decoded_text::jsonb p FROM poetics.artifacts
 WHERE id='github-main-efee4944-graph-20261014')
SELECT 'old node payload matches' AS check_name,count(*) AS matches
 FROM old_graph,LATERAL jsonb_array_elements(p->'rows') r JOIN poetics.nodes n ON n.id=r->>'id'
 WHERE n.original_record=r;
SELECT id,revision,sha256,octet_length(original_bytes) AS bytes,
 encode(extensions.digest(original_bytes,'sha256'),'hex')=sha256 AS bytes_match
 FROM poetics.artifacts WHERE id='github-main-fa7ff494-graph-20261014-reconcile';
