# Source reconciliation — completed comparison; database apply pending

Private working branch: `codex/poetics-reconciliation`, based on the existing SQL migration branch `codex/poetics-supabase-migrations` at `5bb2cea52aa049044592379a91e887c1ef637fb0`. The separate GPT Action code remains on `codex/poetics-read-action`. No changes to main, migrations branch, Sites or WordPress.

Fresh source comparison: current main `fa7ff494bb29a193bd8965afadc1890786bbbfbd` versus the migration branch's inherited graph. Eleven actual JS composition/alias layers fetched at each fixed commit (22 files), composed independently. Existing rows matched by stable ID and recursively key-sorted JSON; connections matched as a content multiset, preserving duplicate multiplicity. Canonical Drive ledger was freshly read (178539 characters at start) and remains authoritative for research/history.

| Scope | Prior source | Current source | Result |
| --- | ---: | ---: | --- |
| Nodes | 449 | 453 | Four new YOPAFEST nodes; all 449 older payloads unchanged |
| Connections | 664 | 667 | Three new role links; all 664 older payloads preserved |
| Normalized search aliases | 31 | 31 | Exact same pairs; nameVariants remain in original record JSON |
| Source URLs | 187 | 188 | One new MCN source; none removed |

New IDs: `yopafest-2021`, `yobe-arts-council`, `yobe-youth-sports-ministry`, `mcn-programme`. New links: event organised by Council, co-organised by Ministry, supported by MCN. Source-qualified occurrence/date range22–24June2021; one primary support-programme family. Formal ministry name, exact room, independent corroboration and current activity remain unresolved; no HQ/residence inference. Claim normalization conservatively uses **attributed**, not independently verified.

## Critical identity issue

New links appear at zero-based positions429–431, ahead of generated city associations. Consequently235 older edge positions shifted by+3 (old429→new432 through old663→new666). They are not new or changed relationships. Never zip arrays or rebuild old database IDs from current ordinal positions. Preserve every old connection/claim ID and old source wrapper. New keys in007 use PostgreSQL JSONB-content SHA256; these keys are not the Node canonical-JSON fingerprint algorithm in the report. Full current capture positions are stored only as provenance.

## Durable reviewed capture

[Current graph capture in Drive](https://drive.google.com/file/d/1Pi4jBRlOVEGEnPrVPcdbXAuHSAwyTvd4/view): `Poetics-Graph-fa7ff494-20261014.json`,1270967bytes,SHA256`2ec44ef41b6536526882453738394ceda398448e559342649e79040d67d5c5ae`. Uploaded into existing VIC’ADEX OPERATING SYSTEM folder, then downloaded and SHA256/size verified exact. It is a supporting immutable graph capture, not another task ledger. No artifact payload/ledger dump is committed to GitHub.

The original database artifact has a different serialization/byte hash. A reconstructed older graph is structurally compared here; do not equate its bytes with the original imported artifact. Original manifest31009691… remains a separate guard. Actual database rows and artifact bytes have not been queried in this runtime.

## Owner apply sequence — no access widening

1. Run existing003/005/006 audits and008 against live private staging. README-reported449/664 is not a fresh SQL result. Any newer work stops automatic apply.
2. Through the existing approved owner importer, register the downloaded capture as `github-main-fa7ff494-graph-20261014-reconcile`, revision/sourcecommitfa7ff494…, preserving rawUTF8 bytes, byteSHA256 and decoded_text exactly. Do not overwrite older artifacts or re-run bootstrap001.007 requires this explicit, byte-verified artifact and adds no payload import mechanism or credentials.
3. Review007, then execute in one transaction only if all guards pass. It locks touched tables/captures, checks449/664/664claims/664claim-source links/187sources/31aliases, exact unchanged node payloads and content-multiset preservation, permits only four named new IDs/three role links, and rolls back mismatches. It inserts4nodes/3claims/3connections/3claim-source links/1source and one truthful execution audit event. Existing nodes/edges/claims/aliases are not updated or deleted. No grants/policies/schema exposure changed.
4. Re-run008 and historical005 node/edge/claim/alias checks. Global source coverage is now old187+one intentional new source; the old global-count check is no longer an equal-total assertion. Expected post-state453/667/667claims/667claim-source links/188sources/31aliases, provenance and uncertainty preserved. A second007 execution intentionally aborts rather than reimporting.
5. Live database and history reconciliation remains pending until readback. Current Drive history is newer than the reported11:56 database ledger captures. Do not label either captured ledger as latest or auto-replace/normalize decisions from it. Capture/reconcile latest original Drive bytes and provider revision separately, preserving all existing sections/runs/query attribution.

This does not activate the GPT Action or make the preview SQL-backed. SQL reader authorization/server secrets/deployment/Builder checks remain pending. Merge only reconciliation scripts/docs into the database workflow after review; do not copy this branch's inherited older app files over main/Sites.

## Validation and limits

`test-reconciliation.mjs` passes comparison counts/unchanged IDs, multiset/duplicate fixtures,235-position detection, no destructive/permission statements and current capture hash/size. All22 source blob IDs are in the ledger; report includes full per-edge move fingerprints. SQL is prepared, **not executed or database-parsed** here: no authenticated Supabase/SQL connection, psql/Deno/runtime database access or PostgreSQL parser is available. Stop on any live divergence; do not force counts to match.
