-- PREPARED ONLY. Run by an authorized owner in PRIVATE staging after importing
-- the byte-verified graph artifact described in RECONCILIATION.md.
-- No artifact payloads or credentials are embedded. This is a one-shot delta,
-- not bootstrap, not permission changes and not an ordinal-based rewrite.
BEGIN;
SELECT pg_advisory_xact_lock(hashtext('poetics-graph-reconciliation-fa7ff494'));
LOCK TABLE poetics.nodes,poetics.connections,poetics.claims,poetics.claim_sources,
  poetics.sources,poetics.aliases IN SHARE ROW EXCLUSIVE MODE;
DO $$
DECLARE p jsonb; a poetics.artifacts%ROWTYPE; old_a poetics.artifacts%ROWTYPE;
BEGIN
 SELECT * INTO STRICT old_a FROM poetics.artifacts WHERE id='github-main-efee4944-graph-20261014' FOR SHARE;
 IF old_a.sha256<>'31009691dfc69103ba77a11672757fb8c49f2e42e0c8d29200f7836c8763522d'
 OR encode(extensions.digest(old_a.original_bytes,'sha256'),'hex')<>old_a.sha256 THEN
   RAISE EXCEPTION 'Baseline artifact hash mismatch; stop and reconcile'; END IF;
 SELECT * INTO STRICT a FROM poetics.artifacts WHERE id='github-main-fa7ff494-graph-20261014-reconcile' FOR SHARE;
 IF a.sha256<>'2ec44ef41b6536526882453738394ceda398448e559342649e79040d67d5c5ae'
 OR encode(extensions.digest(a.original_bytes,'sha256'),'hex')<>a.sha256
 OR octet_length(a.original_bytes)<>1270967
 OR convert_to(a.decoded_text,'UTF8') IS DISTINCT FROM a.original_bytes THEN
   RAISE EXCEPTION 'Current artifact bytes/text/hash mismatch'; END IF;
 p:=a.decoded_text::jsonb;
 IF p->>'sourceCommit'<>'fa7ff494bb29a193bd8965afadc1890786bbbfbd'
 OR jsonb_array_length(p->'rows')<>453 OR jsonb_array_length(p->'edges')<>667 THEN
   RAISE EXCEPTION 'Wrong source snapshot'; END IF;
 IF (SELECT count(*) FROM poetics.nodes)<>449 OR (SELECT count(*) FROM poetics.connections)<>664
 OR (SELECT count(*) FROM poetics.claims)<>664 OR (SELECT count(*) FROM poetics.claim_sources)<>664
 OR (SELECT count(*) FROM poetics.sources)<>187 OR (SELECT count(*) FROM poetics.aliases)<>31 THEN
   RAISE EXCEPTION 'Live inventory changed; do not overwrite newer work'; END IF;
 IF (SELECT count(*) FROM jsonb_array_elements(p->'rows') r JOIN poetics.nodes n ON n.id=r->>'id'
     WHERE n.original_record=r)<>449 THEN
   RAISE EXCEPTION 'An existing node differs from current source; rebase required'; END IF;
 -- Match edge payloads with multiplicity, never by array index or old ID suffix.
 IF EXISTS(SELECT original_record FROM poetics.connections EXCEPT ALL SELECT value FROM jsonb_array_elements(p->'edges')) THEN
   RAISE EXCEPTION 'Existing connection missing/changed in current source'; END IF;
 CREATE TEMP TABLE delta_nodes ON COMMIT DROP AS
   SELECT r AS record FROM jsonb_array_elements(p->'rows') r
   WHERE NOT EXISTS(SELECT 1 FROM poetics.nodes n WHERE n.id=r->>'id');
 IF (SELECT count(*) FROM delta_nodes)<>4 OR EXISTS
   (SELECT 1 FROM delta_nodes WHERE record->>'id' NOT IN ('yopafest-2021','yobe-arts-council','yobe-youth-sports-ministry','mcn-programme')) THEN
   RAISE EXCEPTION 'Unexpected node delta'; END IF;
 CREATE TEMP TABLE delta_edges ON COMMIT DROP AS
   WITH extra AS (SELECT value AS record FROM jsonb_array_elements(p->'edges')
     EXCEPT ALL SELECT original_record FROM poetics.connections)
   SELECT e.record,
     (SELECT ordinality-1 FROM jsonb_array_elements(p->'edges') WITH ORDINALITY x(value,ordinality)
       WHERE x.value=e.record LIMIT 1) AS current_ordinal,
     substr(encode(extensions.digest(convert_to(e.record::text,'UTF8'),'sha256'),'hex'),1,32) AS key
   FROM extra e;
 IF (SELECT count(*) FROM delta_edges)<>3 OR (SELECT count(DISTINCT record) FROM delta_edges)<>3
 OR EXISTS(SELECT 1 FROM delta_edges WHERE record->>'a'<>'yopafest-2021'
   OR record->>'b' NOT IN ('yobe-arts-council','yobe-youth-sports-ministry','mcn-programme')) THEN
   RAISE EXCEPTION 'Unexpected or ambiguous edge delta'; END IF;
 IF EXISTS(SELECT 1 FROM delta_edges d JOIN poetics.connections c ON c.id='edge-'||d.key)
 OR EXISTS(SELECT 1 FROM delta_edges d JOIN poetics.claims c ON c.id='claim-'||d.key) THEN
   RAISE EXCEPTION 'Content-key collision'; END IF;
 IF (SELECT count(DISTINCT record->>'url') FROM delta_edges)<>1 THEN
   RAISE EXCEPTION 'Unexpected source family delta'; END IF;
 INSERT INTO poetics.nodes(id,label,category,record_status,original_record,artifact_id,uncertainty)
   SELECT record->>'id',record->>'name',record->>'category','documented',record,a.id,
     coalesce(record->>'gaps','') FROM delta_nodes;
 INSERT INTO poetics.sources(id,url,title,source_family,evidence_type,publication_date_text,accessed_at,access_outcome,notes)
   SELECT 'src-'||substr(encode(extensions.digest(convert_to(d.record->>'url','UTF8'),'sha256'),'hex'),1,32),
     d.record->>'url','MCN January–June 2021 retrospective','British Council/MCN',
     'primary_support_programme',NULL,NULL,'opened',
     'Direct read documented in EV057 on 14 October 2026; exact access time/publication date not recorded. One source family; no independent corroboration.'
   FROM (SELECT DISTINCT record->>'url' AS url FROM delta_edges) u
   JOIN LATERAL (SELECT record FROM delta_edges WHERE record->>'url'=u.url LIMIT 1) d ON TRUE
   WHERE NOT EXISTS(SELECT 1 FROM poetics.sources s WHERE s.url=u.url);
 INSERT INTO poetics.claims(id,statement,evidence_status,date_text,date_role,geography_scope,uncertainty,artifact_id,original_record)
   SELECT 'claim-'||d.key,n.label||' — '||(d.record->>'label')||' — '||o.label,
     'attributed',d.record->>'date','reported event range',
     'Damaturu event association; no residence/headquarters/venue-room inference',
     'Primary support-programme account; one family, not independent corroboration. '||n.uncertainty||' '||o.uncertainty,
     a.id,jsonb_build_object('sourceCommit',p->>'sourceCommit','edgeOrdinal',d.current_ordinal,'original',d.record)
   FROM delta_edges d JOIN poetics.nodes n ON n.id=d.record->>'a' JOIN poetics.nodes o ON o.id=d.record->>'b';
 INSERT INTO poetics.connections(id,subject_id,predicate,object_id,claim_id,disposition,original_record,notes)
   SELECT 'edge-'||key,record->>'a',record->>'label',record->>'b','claim-'||key,'imported',record,
     'Additive source reconciliation; existing IDs and original claims were not rewritten.' FROM delta_edges;
 INSERT INTO poetics.claim_sources(claim_id,source_id,relationship,locator,supported_scope)
   SELECT 'claim-'||d.key,s.id,'supports','YOUTH PEACE INITIATIVES',
     'Source explicitly attributes '||(d.record->>'label')||'; one primary family; no current-office/HQ inference.'
   FROM delta_edges d JOIN poetics.sources s ON s.url=d.record->>'url';
 IF (SELECT count(*) FROM poetics.nodes)<>453 OR (SELECT count(*) FROM poetics.connections)<>667
 OR (SELECT count(*) FROM poetics.claims)<>667 OR (SELECT count(*) FROM poetics.claim_sources)<>667
 OR (SELECT count(*) FROM poetics.sources)<>188 OR (SELECT count(*) FROM poetics.aliases)<>31 THEN
   RAISE EXCEPTION 'Post-write inventory mismatch; rollback'; END IF;
 INSERT INTO poetics.audit_events(actor,action,detail) VALUES
   ('script:007_apply_verified_graph_delta','owner-reviewed additive reconciliation',
    jsonb_build_object('sourceCommit',p->>'sourceCommit','artifactId',a.id,'addedNodes',4,'addedConnections',3,
      'preservedExistingNodes',449,'preservedExistingConnections',664,'sourceStatus','attributed; one primary family'));
END $$;
COMMIT;
