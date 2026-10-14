export const queries={
  nodes:{text:`SELECT n.id,n.label,n.category,n.record_status,n.uncertainty,n.artifact_id,
    n.original_record->'city' AS location,n.original_record->'summary' AS details,
    n.original_record->'dateFact' AS date_fact,n.original_record->'years' AS evidence_years,
    n.original_record->'verification' AS verification,n.original_record->'links' AS source_links
    FROM poetics.nodes n WHERE ($1='' OR strpos(lower(n.label),lower($1))>0 OR EXISTS
    (SELECT 1 FROM poetics.aliases a WHERE a.node_id=n.id AND strpos(lower(a.alias),lower($1))>0))
    AND ($2='' OR n.id=$2) AND ($3='' OR n.category=$3) ORDER BY n.id LIMIT $4 OFFSET $5`,
    args:p=>[p.q,p.id,p.category,p.limit,p.offset]},
  connections:{text:`SELECT c.id,c.subject_id,c.predicate,c.object_id,c.disposition,c.notes,c.claim_id,
    cl.statement,cl.evidence_status,cl.date_text,cl.date_role,cl.geography_scope,cl.uncertainty,
    (SELECT jsonb_agg(jsonb_build_object('source_id',s.id,'url',s.url,'source_family',s.source_family,
      'relationship',cs.relationship,'locator',cs.locator,'supported_scope',cs.supported_scope) ORDER BY s.id)
      FROM poetics.claim_sources cs JOIN poetics.sources s ON s.id=cs.source_id WHERE cs.claim_id=cl.id) AS evidence
    FROM poetics.connections c JOIN poetics.claims cl ON cl.id=c.claim_id
    WHERE (c.subject_id=$1 OR c.object_id=$1) AND ($2='' OR strpos(lower(c.predicate),lower($2))>0)
    ORDER BY c.id LIMIT $3 OFFSET $4`,args:p=>[p.nodeId,p.q,p.limit,p.offset]},
  sources:{text:`SELECT id,url,title,source_family,evidence_type,publication_date_text,accessed_at,access_outcome,notes
    FROM poetics.sources WHERE $1='' OR strpos(lower(coalesce(title,'')||' '||url),lower($1))>0
    ORDER BY id LIMIT $2 OFFSET $3`,args:p=>[p.q,p.limit,p.offset]},
  ledger:{text:`SELECT l.artifact_id,l.ordinal,l.heading,substring(l.body from 1 for 4000) AS body,
    length(l.body)>4000 AS body_truncated,a.source_uri,a.revision,a.captured_at,a.sha256
    FROM poetics.ledger_sections l JOIN poetics.artifacts a ON a.id=l.artifact_id
    WHERE l.artifact_id=$1 AND ($2='' OR strpos(lower(l.heading||' '||l.body),lower($2))>0)
    ORDER BY l.ordinal LIMIT $3 OFFSET $4`,args:p=>[p.artifactId,p.q,p.limit,p.offset]}
};
