-- Poetics staging. Run as project administrator in a NEW staging project.
-- No public/anonymous access; no changes to WordPress or existing Atlas files.
BEGIN;
CREATE SCHEMA poetics;
REVOKE ALL ON SCHEMA poetics FROM PUBLIC;

CREATE TABLE poetics.artifacts (
  id text PRIMARY KEY,
  source_uri text NOT NULL,
  revision text NOT NULL,
  captured_at timestamptz NOT NULL,
  sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  original_bytes bytea NOT NULL,
  decoded_text text,
  media_type text NOT NULL,
  capture_method text NOT NULL,
  UNIQUE(source_uri, revision, sha256)
);
CREATE TABLE poetics.ledger_sections (
  artifact_id text NOT NULL REFERENCES poetics.artifacts(id),
  ordinal integer NOT NULL CHECK (ordinal >= 0),
  heading text NOT NULL,
  body text NOT NULL,
  PRIMARY KEY(artifact_id, ordinal)
);
CREATE TABLE poetics.research_runs (
  id text PRIMARY KEY,
  artifact_id text NOT NULL REFERENCES poetics.artifacts(id),
  section_ordinal integer NOT NULL,
  actor text,
  occurred_at timestamptz,
  original_date_text text,
  summary text NOT NULL,
  FOREIGN KEY(artifact_id,section_ordinal)
    REFERENCES poetics.ledger_sections(artifact_id,ordinal)
);
CREATE TABLE poetics.sources (
  id text PRIMARY KEY,
  url text NOT NULL UNIQUE,
  title text,
  source_family text,
  evidence_type text NOT NULL,
  publication_date_text text,
  accessed_at timestamptz,
  access_outcome text NOT NULL,
  notes text NOT NULL DEFAULT ''
);
CREATE TABLE poetics.nodes (
  id text PRIMARY KEY,
  label text NOT NULL,
  category text NOT NULL CHECK(category IN
    ('People','Places','Platforms','Prizes','Publications')),
  record_status text NOT NULL CHECK(record_status IN
    ('proposed','documented','disputed','withdrawn')),
  original_record jsonb NOT NULL,
  artifact_id text NOT NULL REFERENCES poetics.artifacts(id),
  uncertainty text NOT NULL DEFAULT ''
);
CREATE TABLE poetics.aliases (
  node_id text NOT NULL REFERENCES poetics.nodes(id),
  alias text NOT NULL,
  resolution_status text NOT NULL CHECK(resolution_status IN
    ('source_variant','confirmed','unresolved')),
  source_id text REFERENCES poetics.sources(id),
  notes text NOT NULL DEFAULT '',
  PRIMARY KEY(node_id,alias)
);
CREATE TABLE poetics.claims (
  id text PRIMARY KEY,
  statement text NOT NULL,
  evidence_status text NOT NULL CHECK(evidence_status IN
    ('indexed_lead','announced','attributed','reported','verified','disputed','withdrawn')),
  date_text text,
  date_role text,
  geography_scope text,
  uncertainty text NOT NULL,
  run_id text REFERENCES poetics.research_runs(id),
  artifact_id text NOT NULL REFERENCES poetics.artifacts(id),
  original_record jsonb NOT NULL
);
CREATE TABLE poetics.claim_sources (
  claim_id text NOT NULL REFERENCES poetics.claims(id),
  source_id text NOT NULL REFERENCES poetics.sources(id),
  relationship text NOT NULL CHECK(relationship IN ('supports','contradicts','context')),
  locator text,
  supported_scope text NOT NULL,
  PRIMARY KEY(claim_id,source_id,relationship)
);
CREATE TABLE poetics.connections (
  id text PRIMARY KEY,
  subject_id text NOT NULL REFERENCES poetics.nodes(id),
  predicate text NOT NULL,
  object_id text NOT NULL REFERENCES poetics.nodes(id),
  claim_id text NOT NULL REFERENCES poetics.claims(id),
  disposition text NOT NULL CHECK(disposition IN
    ('proposed','imported','disputed','withdrawn')),
  original_record jsonb NOT NULL,
  -- No automatic equivalence, residence, attendance or chronology inference.
  notes text NOT NULL DEFAULT ''
);
CREATE TABLE poetics.search_queries (
  id text PRIMARY KEY,
  run_id text NOT NULL REFERENCES poetics.research_runs(id),
  exact_query text NOT NULL,
  engine text NOT NULL,
  searched_at timestamptz,
  original_date_text text,
  yield_scope text NOT NULL CHECK(yield_scope IN ('individual','combined_batch')),
  batch_id text,
  yield_text text NOT NULL,
  attribution text NOT NULL
);
CREATE TABLE poetics.decisions (
  id text PRIMARY KEY,
  run_id text REFERENCES poetics.research_runs(id),
  statement text NOT NULL,
  status text NOT NULL,
  approval_evidence text,
  supersedes text REFERENCES poetics.decisions(id)
);
CREATE TABLE poetics.audit_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  actor text NOT NULL,
  action text NOT NULL,
  detail jsonb NOT NULL
);

-- Default-deny every table, including for ordinary authenticated users.
-- Add narrowly scoped membership policies only after actual identities are known.
DO $$ DECLARE t record; BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='poetics' LOOP
    EXECUTE format('ALTER TABLE poetics.%I ENABLE ROW LEVEL SECURITY',t.tablename);
    EXECUTE format('REVOKE ALL ON TABLE poetics.%I FROM PUBLIC',t.tablename);
  END LOOP;
END $$;
ALTER DEFAULT PRIVILEGES IN SCHEMA poetics REVOKE ALL ON TABLES FROM PUBLIC;
COMMENT ON SCHEMA poetics IS 'Private staging only. Drive remains authoritative until migration reconciliation and cutover are verified.';
COMMIT;
