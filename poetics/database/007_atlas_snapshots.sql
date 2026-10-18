-- Private, versioned Atlas payload. No API role receives table access.
-- The snapshot seed is kept separately from this schema migration.
-- The first chunk import is retained intact for audit. The v2 table carries
-- per-chunk source hashes and is the byte-verified assembly source.
create table if not exists poetics.atlas_snapshots (
  snapshot_id text primary key,
  source_commit text not null,
  source_preview text not null,
  captured_at timestamptz not null,
  node_count integer not null check (node_count >= 0),
  edge_count integer not null check (edge_count >= 0),
  payload_sha256 text not null check (payload_sha256 ~ '^[0-9a-f]{64}$'),
  payload jsonb not null check (jsonb_typeof(payload) = 'object'),
  created_at timestamptz not null default now()
);
alter table poetics.atlas_snapshots enable row level security;
revoke all on table poetics.atlas_snapshots from public, anon, authenticated, service_role;

create table if not exists poetics.atlas_snapshot_chunks (
  snapshot_id text not null,
  chunk_index integer not null,
  chunk_text text not null,
  payload_sha256 text not null,
  primary key (snapshot_id, chunk_index)
);
alter table poetics.atlas_snapshot_chunks enable row level security;
revoke all on table poetics.atlas_snapshot_chunks from public, anon, authenticated, service_role;

create table if not exists poetics.atlas_snapshot_chunks_v2 (
  snapshot_id text not null,
  chunk_index integer not null,
  chunk_text text not null,
  source_sha256 text not null check (source_sha256 ~ '^[0-9a-f]{64}$'),
  primary key (snapshot_id, chunk_index)
);
alter table poetics.atlas_snapshot_chunks_v2 enable row level security;
revoke all on table poetics.atlas_snapshot_chunks_v2 from public, anon, authenticated, service_role;
