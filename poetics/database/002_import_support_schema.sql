-- Data-free schema for preserving exact source artifact bytes in staging.
-- This file intentionally contains no source URLs, artifact records or payload inserts.
CREATE TABLE poetics.artifact_import_chunks (
  artifact_id text NOT NULL,
  part_no integer NOT NULL CHECK (part_no >= 0),
  chunk_hex text NOT NULL CHECK (chunk_hex ~ '^[0-9a-f]*$'),
  chunk_text text,
  PRIMARY KEY (artifact_id, part_no)
);
ALTER TABLE poetics.artifact_import_chunks ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE poetics.artifact_import_chunks FROM PUBLIC;
