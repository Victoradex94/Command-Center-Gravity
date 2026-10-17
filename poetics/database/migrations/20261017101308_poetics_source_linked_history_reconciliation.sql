-- Source-linked indexes for lossless retrospective research history.
-- This migration is data-free. Raw evidence remains in artifacts/history_lines;
-- tags are retrieval aids, not validated claims or current task status.
CREATE TABLE poetics.history_run_references (
  artifact_id text NOT NULL REFERENCES poetics.artifacts(id),
  line_from integer NOT NULL,
  line_to integer NOT NULL,
  run_id text NOT NULL REFERENCES poetics.research_runs(id),
  source_heading text NOT NULL,
  source_date_text text,
  PRIMARY KEY (artifact_id, line_from),
  FOREIGN KEY (artifact_id, line_from)
    REFERENCES poetics.history_lines(artifact_id, line_no),
  FOREIGN KEY (artifact_id, line_to)
    REFERENCES poetics.history_lines(artifact_id, line_no),
  CHECK (line_to >= line_from)
);
CREATE INDEX history_run_references_run_id_idx
  ON poetics.history_run_references (run_id);
ALTER TABLE poetics.history_run_references ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON poetics.history_run_references FROM PUBLIC, anon, authenticated, service_role;

CREATE TABLE poetics.history_passages (
  artifact_id text NOT NULL REFERENCES poetics.artifacts(id),
  passage_no integer NOT NULL CHECK (passage_no > 0),
  line_from integer NOT NULL,
  line_to integer NOT NULL,
  run_id text REFERENCES poetics.research_runs(id),
  record_kinds jsonb NOT NULL,
  classification_basis text NOT NULL,
  source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
  PRIMARY KEY (artifact_id, passage_no),
  FOREIGN KEY (artifact_id, line_from)
    REFERENCES poetics.history_lines(artifact_id, line_no),
  FOREIGN KEY (artifact_id, line_to)
    REFERENCES poetics.history_lines(artifact_id, line_no),
  CHECK (line_to >= line_from)
);
CREATE INDEX history_passages_run_id_idx
  ON poetics.history_passages (run_id);
CREATE INDEX history_passages_record_kinds_idx
  ON poetics.history_passages USING gin (record_kinds);
ALTER TABLE poetics.history_passages ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON poetics.history_passages FROM PUBLIC, anon, authenticated, service_role;
COMMENT ON TABLE poetics.history_passages IS
  'Verbatim historical-source locations. Tags indicate literal vocabulary/context for retrieval, not validated atomic facts, complete semantic parsing or current task status. Unknown metadata stays unset; source_sha256 hashes newline-joined referenced original lines.';
