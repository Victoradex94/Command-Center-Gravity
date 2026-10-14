-- Read-only graph payload and source coverage audit.
-- Requires 004_restore_verified_artifact_bytes.sql to have restored decoded_text.
-- Run against the Poetics staging project as postgres; no data or permissions change.
WITH graph AS (
  SELECT decoded_text::jsonb AS payload FROM poetics.artifacts
  WHERE id='github-main-efee4944-graph-20261014'
), expected_nodes AS (
  SELECT value AS record, value->>'id' AS id
  FROM graph, LATERAL jsonb_array_elements(payload->'rows')
), expected_edges AS (
  SELECT value AS record, (ordinality-1)::integer AS edge_ordinal,
         'github-efee4944-edge-' || lpad(ordinality::text,4,'0') AS connection_id,
         'github-efee4944-claim-' || lpad(ordinality::text,4,'0') AS claim_id
  FROM graph, LATERAL jsonb_array_elements(payload->'edges') WITH ORDINALITY AS e(value,ordinality)
), expected_aliases AS (
  SELECT DISTINCT n.id AS node_id, a.value #>> '{}' AS alias
  FROM graph, LATERAL jsonb_array_elements(payload->'rows') AS n(value),
       LATERAL jsonb_array_elements(COALESCE(n.value->'searchAliases','[]'::jsonb)) AS a(value)
), expected_urls AS (
  SELECT DISTINCT url FROM (
    SELECT l.value->>'url' AS url FROM graph,
      LATERAL jsonb_array_elements(payload->'rows') AS n(value),
      LATERAL jsonb_array_elements(COALESCE(n.value->'links','[]'::jsonb)) AS l(value)
    UNION ALL
    SELECT y.value->>'url' FROM graph,
      LATERAL jsonb_array_elements(payload->'rows') AS n(value),
      LATERAL jsonb_array_elements(COALESCE(n.value->'years','[]'::jsonb)) AS y(value)
    UNION ALL
    SELECT e.value->>'url' FROM graph,
      LATERAL jsonb_array_elements(payload->'edges') AS e(value)
  ) u WHERE url IS NOT NULL AND url<>''
), checks AS (
  SELECT 'nodes: expected snapshot rows' AS check_name,
    (SELECT count(*) FROM expected_nodes) AS expected_count,
    (SELECT count(*) FROM poetics.nodes WHERE artifact_id='github-main-efee4944-graph-20261014') AS actual_count,
    (SELECT count(*) FROM expected_nodes e JOIN poetics.nodes n ON n.id=e.id WHERE n.original_record=e.record) AS exact_payload_matches
  UNION ALL
  SELECT 'connections: expected snapshot edges',
    (SELECT count(*) FROM expected_edges),
    (SELECT count(*) FROM poetics.connections WHERE id LIKE 'github-efee4944-edge-%'),
    (SELECT count(*) FROM expected_edges e JOIN poetics.connections c ON c.id=e.connection_id
      WHERE c.original_record=e.record AND c.subject_id=e.record->>'a'
        AND c.object_id=e.record->>'b' AND c.predicate=e.record->>'label')
  UNION ALL
  SELECT 'claims: source edge wrappers',
    (SELECT count(*) FROM expected_edges),
    (SELECT count(*) FROM poetics.claims WHERE id LIKE 'github-efee4944-claim-%'),
    (SELECT count(*) FROM expected_edges e JOIN poetics.claims cl ON cl.id=e.claim_id JOIN graph g ON TRUE
      WHERE cl.original_record=jsonb_build_object('sourceCommit',g.payload->>'sourceCommit',
        'edgeOrdinal',e.edge_ordinal,'original',e.record))
  UNION ALL
  SELECT 'aliases: exact node-alias pairs',
    (SELECT count(*) FROM expected_aliases),
    (SELECT count(*) FROM poetics.aliases a JOIN poetics.nodes n ON n.id=a.node_id
      WHERE n.artifact_id='github-main-efee4944-graph-20261014'),
    (SELECT count(*) FROM expected_aliases e JOIN poetics.aliases a ON a.node_id=e.node_id AND a.alias=e.alias
      WHERE a.resolution_status='unresolved')
  UNION ALL
  SELECT 'sources: unique source URLs',
    (SELECT count(*) FROM expected_urls),
    (SELECT count(*) FROM poetics.sources),
    (SELECT count(*) FROM expected_urls e JOIN poetics.sources s ON s.url=e.url
      WHERE s.id='src-' || substr(encode(extensions.digest(convert_to(e.url,'UTF8'),'sha256'),'hex'),1,32))
)
SELECT check_name,expected_count,actual_count,exact_payload_matches,
  (expected_count=actual_count AND actual_count=exact_payload_matches) AS pass
FROM checks ORDER BY check_name;

-- Show missing/extraneous source URLs, rather than only a summary count.
WITH graph AS (
  SELECT decoded_text::jsonb AS payload FROM poetics.artifacts WHERE id='github-main-efee4944-graph-20261014'
), expected_urls AS (
  SELECT DISTINCT url FROM (
    SELECT l.value->>'url' AS url FROM graph,LATERAL jsonb_array_elements(payload->'rows') n(value),
      LATERAL jsonb_array_elements(COALESCE(n.value->'links','[]'::jsonb)) l(value)
    UNION ALL
    SELECT y.value->>'url' FROM graph,LATERAL jsonb_array_elements(payload->'rows') n(value),
      LATERAL jsonb_array_elements(COALESCE(n.value->'years','[]'::jsonb)) y(value)
    UNION ALL
    SELECT e.value->>'url' FROM graph,LATERAL jsonb_array_elements(payload->'edges') e(value)
  ) x WHERE url IS NOT NULL AND url<>''
)
SELECT 'missing_in_sources' AS issue,e.url FROM expected_urls e
LEFT JOIN poetics.sources s ON s.url=e.url WHERE s.id IS NULL
UNION ALL
SELECT 'extra_in_sources',s.url FROM poetics.sources s
LEFT JOIN expected_urls e ON e.url=s.url WHERE e.url IS NULL
ORDER BY issue,url;
