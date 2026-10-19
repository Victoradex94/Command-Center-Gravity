# Poetics source and publication workflow

## Current source of truth

- Repository: `Victoradex94/Command-Center-Gravity`, folder `poetics/`.
- Current branch: `main`; start new work branches from its latest commit.
- Current code snapshot: Release 103, authoritative and maintained in GitHub `main`.
- The `poetics-staging` branch is an older Version 45 snapshot. Do not use it as the base for new work.

GitHub `main` is the sole authoritative application source. LocalWP is a synchronized staging copy; changes there must be reconciled through a GitHub branch and review before they become authoritative.

## Before research or data changes

1. Read the latest canonical Drive Markdown ledger: https://drive.google.com/file/d/13qDg2XVdUM5ZAbplLoeNT5X6hB89cnSq/view . Do not use an old download as authority.
2. Fetch current GitHub `main` and record its commit. Inspect LocalWP only when explicitly importing changes from local staging.
3. Preserve newer work from either source. Use `research/` artifacts as supporting evidence, not as a replacement task ledger.

## GitHub development

1. Clone the private repository and work under `poetics/`.
2. Create a new working branch from current `main`, for example `poetics-work`; do not start from the stale `poetics-staging` branch.
3. Edit readable, non-fingerprinted files. After source edits, run `python -X utf8 scripts/fingerprint-assets.py` from `poetics/`.
4. Run the relevant Node checks. A core set is `test-atlas-navigation.cjs`, `test-state-urban-integration.cjs`, `test-directory.cjs`, `test-delivery.cjs`, `test-engine.cjs`, `test-contribute.cjs`, and `test-nigeria-gis.cjs`.
5. Commit and push the branch. Merge to `main` only after reviewing the diff and confirming it does not overwrite newer work.

## Data and product boundaries

- Historical bundled Atlas tests verify 453 records and 667 source-linked relationships; runtime data comes from Supabase. Preserve source attribution, date precision, name variants, uncertainty and planned-versus-completed distinctions.
- Fictional game events and player state remain separate from historical records. Game saves currently use localStorage; no account/cloud save is configured.
- The Submit flow sends records to the existing Supabase review queue and retains a local draft option.
- State boundaries and prepared urban extents are different geographic products. Urban footprints are not legal city limits; missing detailed layers must not be described as zero cultural activity.
- `wordpress/poetics-preview/` is package source only. Do not deploy or alter live WordPress.

## GitHub-first operation

Run `node scripts/serve-local.cjs` from `poetics/` or use `START-POETICS.cmd` on Windows. This serves only `dist/` on `127.0.0.1:4173`; no WordPress or LocalWP service is needed. Python remains an alternative. Edit readable source in a new branch from current main, regenerate delivery files, run checks, and merge reviewed changes. Pull main into any staging copy.

For website delivery, the intended flow is GitHub main -> an approved build/deployment process -> the website serving `poetics/dist/` -> browser requests to the existing Supabase API. Visitors load code from the website host; GitHub remains its source. A private GitHub repository does not make browser-delivered JavaScript secret; browser code must contain only public configuration.

## Verified GitHub-to-LocalWP connector

See [GITHUB-LOCALWP-CONNECTION.md](GITHUB-LOCALWP-CONNECTION.md) for the isolated build/test sync helper, explicit source imports, recovery copies, CI drift gate and the local staging connector. Runtime Atlas data continues to come from the existing Supabase API. No live Vic’Adex deployment is part of this connection.
