-- Exact restoration of all four preserved staging artifact payloads from imported chunks.
-- Run in the separate Poetics staging project only, as postgres.
-- Requires pgcrypto's digest function in the Supabase extensions schema.
-- Aborts if any reconstructed payload fails its manifest SHA256 or differs from
-- a non-empty original_bytes value. The rendered-ledger capture is a distinct
-- browser text capture, not the canonical Drive file's original bytes; preserve
-- its existing LF-normalised decoded_text while restoring its captured bytea.
BEGIN;
DO $$
DECLARE
  a record;
  payload bytea;
  actual_sha text;
  existing bytea;
BEGIN
  FOR a IN
    SELECT id, sha256, media_type
    FROM poetics.artifacts
    WHERE id IN (
      'drive-raw-20261014-1156',
      'drive-rendered-20261014-1130',
      'github-main-efee4944-graph-20261014',
      'github-main-efee4944-zip-20261014'
    )
    ORDER BY id
  LOOP
    SELECT decode(string_agg(chunk_hex,'' ORDER BY part_no),'hex')
      INTO payload
    FROM poetics.artifact_import_chunks
    WHERE artifact_id=a.id;

    IF payload IS NULL THEN
      RAISE EXCEPTION 'No imported chunks for artifact %', a.id;
    END IF;

    actual_sha := encode(extensions.digest(payload,'sha256'),'hex');
    IF actual_sha <> a.sha256 THEN
      RAISE EXCEPTION 'SHA256 mismatch for artifact %: expected %, got %', a.id, a.sha256, actual_sha;
    END IF;

    SELECT original_bytes INTO existing FROM poetics.artifacts WHERE id=a.id FOR UPDATE;
    IF octet_length(existing) > 0 AND existing <> payload THEN
      RAISE EXCEPTION 'Existing original_bytes differs from verified chunks for artifact %', a.id;
    END IF;

    UPDATE poetics.artifacts
    SET original_bytes=payload,
        decoded_text=CASE
          WHEN a.id='drive-rendered-20261014-1130' THEN decoded_text
          WHEN a.media_type IN ('text/markdown','application/json')
            THEN convert_from(payload,'UTF8')
          ELSE decoded_text
        END
    WHERE id=a.id;
  END LOOP;

  IF (SELECT count(*) FROM poetics.artifacts
      WHERE id IN ('drive-raw-20261014-1156',
                   'drive-rendered-20261014-1130',
                   'github-main-efee4944-graph-20261014',
                   'github-main-efee4944-zip-20261014')) <> 4 THEN
    RAISE EXCEPTION 'Expected exactly four source artifacts';
  END IF;
END $$;
COMMIT;
