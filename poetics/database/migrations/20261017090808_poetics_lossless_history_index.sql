CREATE TABLE poetics.history_lines (
artifact_id text NOT NULL REFERENCES poetics.artifacts(id),
line_no integer NOT NULL CHECK (line_no>=1),
raw_line text NOT NULL,
PRIMARY KEY(artifact_id,line_no));
ALTER TABLE poetics.history_lines ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON poetics.history_lines FROM PUBLIC,anon,authenticated,service_role;
COMMENT ON TABLE poetics.history_lines IS 'Lossless ordered source history. Every source line is retained, including queries, decisions, statuses, corrections and unknown metadata. Raw text is evidence, not an inferred typed assertion; typed research tables remain separately curated.';