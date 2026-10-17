-- Idempotent compatibility overlay for the ledger-backed Atlas records.
-- Applied on 17 October 2026 to Supabase project tknahlnirtnanzqqvufb,
-- branch main PRODUCTION. This changes the read function only; it does not
-- replace or rewrite the snapshot, normalized records, evidence, or submission queue.
-- Prerequisites: 007_atlas_snapshots.sql, 008_public_atlas_api.sql and the
-- reconciled artifact drive-export-md-20261016-004313 already exist.
-- CREATE OR REPLACE preserves the function's existing execute grants.

begin;

create or replace function public.read_poetics_atlas_snapshot()
returns jsonb
language sql
stable
security definer
set search_path to ''
as $function$
with base as (
  select s.payload
  from poetics.atlas_snapshots as s
  where s.snapshot_id = 'github-main-0988b31-preview75-reconciled-sql-20261016'
), extra_rows as (
  select coalesce(jsonb_agg(n.original_record order by n.id), '[]'::jsonb) as value
  from poetics.nodes as n
  cross join base as b
  where n.artifact_id = 'drive-export-md-20261016-004313'
    and n.record_status = 'documented'
    and n.original_record is not null
    and not exists (
      select 1
      from pg_catalog.jsonb_array_elements(b.payload->'rows') as existing
      where existing->>'id' = n.id
    )
), extra_edges as (
  select coalesce(jsonb_agg(c.original_record order by c.id), '[]'::jsonb) as value
  from poetics.connections as c
  join poetics.claims as cl on cl.id = c.claim_id
  cross join base as b
  where cl.artifact_id = 'drive-export-md-20261016-004313'
    and c.disposition = 'imported'
    and c.original_record is not null
    and not exists (
      select 1
      from pg_catalog.jsonb_array_elements(b.payload->'edges') as existing
      where existing->>'a' = c.original_record->>'a'
        and existing->>'b' = c.original_record->>'b'
        and existing->>'label' = c.original_record->>'label'
    )
)
select pg_catalog.jsonb_set(
  pg_catalog.jsonb_set(b.payload, '{rows}', (b.payload->'rows') || r.value),
  '{edges}', (b.payload->'edges') || e.value
)
from base as b
cross join extra_rows as r
cross join extra_edges as e;
$function$;

commit;
