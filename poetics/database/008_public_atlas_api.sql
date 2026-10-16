-- Controlled Poetics API surface. Public access is limited to the two reviewed RPCs.
begin;

create table if not exists poetics.atlas_submissions (
  submission_id uuid primary key default gen_random_uuid(),
  submitted_at timestamptz not null default now(),
  review_status text not null default 'pending_review'
    check (review_status in ('pending_review', 'accepted', 'declined')),
  payload jsonb not null check (jsonb_typeof(payload) = 'object')
);
alter table poetics.atlas_submissions enable row level security;
revoke all on table poetics.atlas_submissions from public, anon, authenticated, service_role;

create or replace function public.read_poetics_atlas_snapshot()
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select s.payload
  from poetics.atlas_snapshots s
  where s.snapshot_id = 'github-main-0988b31-preview75-reconciled-sql-20261016'
$$;
revoke all on function public.read_poetics_atlas_snapshot() from public, anon, authenticated, service_role;

create or replace function public.submit_poetics_atlas_record(p_submission jsonb)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  submission_id uuid;
  clean_payload jsonb;
  image_url text := nullif(btrim(p_submission->>'image'), '');
begin
  if jsonb_typeof(p_submission) is distinct from 'object'
     or octet_length(p_submission::text) > 12000 then
    raise exception 'Invalid submission payload';
  end if;
  if nullif(btrim(p_submission->>'name'), '') is null
     or length(p_submission->>'name') > 160
     or nullif(btrim(p_submission->>'details'), '') is null
     or length(p_submission->>'details') > 2000
     or nullif(btrim(p_submission->>'location'), '') is null
     or length(p_submission->>'location') > 180
     or coalesce(p_submission->>'category', '') not in ('People', 'Places', 'Platforms', 'Prizes', 'Publications')
     or coalesce(p_submission->>'source', '') !~* '^https?://'
     or length(p_submission->>'source') > 2048
     or length(coalesce(p_submission->>'sourceLocator', '')) > 300
     or length(coalesce(p_submission->>'connections', '')) > 1500
     or length(coalesce(p_submission->>'contributor', '')) > 160 then
    raise exception 'Required submission fields are missing or exceed their limits';
  end if;
  if image_url is not null and (
       image_url !~* '^https?://'
       or length(image_url) > 2048
       or nullif(btrim(p_submission->>'imageCredit'), '') is null
       or length(p_submission->>'imageCredit') > 180
       or lower(coalesce(p_submission->>'imagePermission', '')) not in ('on', 'true')
     ) then
    raise exception 'Image link, credit and reuse permission are required';
  end if;

  clean_payload := jsonb_build_object(
    'name', btrim(p_submission->>'name'),
    'category', p_submission->>'category',
    'details', btrim(p_submission->>'details'),
    'location', btrim(p_submission->>'location'),
    'state', nullif(btrim(p_submission->>'state'), ''),
    'year', nullif(btrim(p_submission->>'year'), ''),
    'yearMeaning', nullif(btrim(p_submission->>'yearMeaning'), ''),
    'source', btrim(p_submission->>'source'),
    'sourceLocator', nullif(btrim(p_submission->>'sourceLocator'), ''),
    'connections', nullif(btrim(p_submission->>'connections'), ''),
    'image', image_url,
    'imageCredit', nullif(btrim(p_submission->>'imageCredit'), ''),
    'imagePermission', image_url is not null,
    'contributor', nullif(btrim(p_submission->>'contributor'), '')
  );

  insert into poetics.atlas_submissions as inserted(payload)
  values (clean_payload)
  returning inserted.submission_id into submission_id;
  return submission_id;
end;
$$;
revoke all on function public.submit_poetics_atlas_record(jsonb) from public, anon, authenticated, service_role;

-- Approved public interface: snapshot read plus submission into pending review.
-- Direct table SELECT/INSERT remain revoked; these RPCs cannot publish records.
grant execute on function public.read_poetics_atlas_snapshot() to anon;
grant execute on function public.submit_poetics_atlas_record(jsonb) to anon;

commit;
