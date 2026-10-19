# Poetics source and publication workflow

## Current source of truth

- Repository: `Victoradex94/Command-Center-Gravity`, folder `poetics/`.
- Current branch: `main`; start new work branches from its latest commit.
- Current code snapshot: Release 103, reconciled from LocalWP and merged into main. Read current main for its exact commit. The Sites checkpoint below describes a separate historical preview, not this release.
- The `poetics-staging` branch is an older Version 45 snapshot. Do not use it as the base for new work.
- Sites project: `appgprj_6acce9493e8c81919635a9e7438b820c`; current restricted publication Version 76; its separately managed Sites source checkpoint is `e22287464f447cfec4f664c3b9ddf7be7b870b2e`.

GitHub main is the authoritative application source. LocalWP is an optional staging copy; changes there must be reconciled through a GitHub branch and review before they become authoritative. The Sites app uses its own managed source repository. GitHub and Sites do not synchronize automatically, and a GitHub commit does not change the preview.

## Before research or data changes

1. Read the latest canonical Drive Markdown ledger: https://drive.google.com/file/d/13qDg2XVdUM5ZAbplLoeNT5X6hB89cnSq/view . Do not use an old download as authority.
2. Fetch current GitHub `main` and record its commit. Inspect LocalWP or Sites only when explicitly importing changes from those separate copies.
3. Preserve newer work from either source. Use `research/` artifacts as supporting evidence, not as a replacement task ledger.

## GitHub development

1. Clone the private repository and work under `poetics/`.
2. Create a new working branch from current `main`, for example `poetics-work`; do not start from the stale `poetics-staging` branch.
3. Edit readable, non-fingerprinted files. After source edits, run `python -X utf8 scripts/fingerprint-assets.py` from `poetics/`.
4. Run the relevant Node checks. A core set is `test-atlas-navigation.cjs`, `test-state-urban-integration.cjs`, `test-directory.cjs`, `test-delivery.cjs`, `test-engine.cjs`, `test-contribute.cjs`, and `test-nigeria-gis.cjs`.
5. Commit and push the branch. Merge to `main` only after reviewing the diff and confirming it does not overwrite newer work.

## Updating the restricted Sites preview

A GitHub update does not publish the Sites preview. When the user requests a preview update:

1. Re-read GitHub `main`; retrieve fresh Sites source with the supported Sites source helper and inspect the latest published version.
2. Reconcile both copies before editing. Never overwrite a newer human or assistant contribution.
3. Apply the reviewed source to the Sites checkout; run checks and build/package through the supported helper.
4. Push the exact source state to the Site’s managed repository. Save and deploy that source as a new Sites version, preserving the existing custom-access audience.
5. Verify the native deployment result, source commit, version, data counts and any requested browser-visible behavior. Do not claim visual/mobile QA from bundle checks alone.

The restricted preview URL is https://poetics-vicadex-lab.vicadexconcepts.chatgpt.site/#/atlas . No GitHub Pages or separate public hosting target is configured. Do not change the Site’s audience, domain, hosting configuration or live WordPress as part of this workflow.

## Data and product boundaries

- Historical bundled Atlas tests verify 453 records and 667 source-linked relationships; runtime data comes from Supabase. Preserve source attribution, date precision, name variants, uncertainty and planned-versus-completed distinctions.
- Fictional game events and player state remain separate from historical records. Game saves currently use localStorage; no account/cloud save is configured.
- The Submit flow sends records to the existing Supabase review queue and retains a local draft option.
- State boundaries and prepared urban extents are different geographic products. Urban footprints are not legal city limits; missing detailed layers must not be described as zero cultural activity.
- `wordpress/poetics-preview/` is package source only. Do not deploy or alter live WordPress.


## LocalWP release 103 reconciliation (19 October 2026)

Started from current main `0988b3197f00ade4ed6e1ee55503b6a09ddbbf1c` and compared the local staging build `2026-10-18-release-103`. Readable sources live in `dist/`; fingerprinted files and `research/release-assets.json` are generated with the existing script. GitHub lookup indexes, filter-count caches and packed startup data remain; indexes rebuild after snapshot replacement. Research, archives and historical snapshots are preserved.

The Atlas now reads the existing Supabase snapshot and displays an error/retry when unavailable. The bundled 453-record/667-relationship snapshot remains historical source and test input; it is not the current runtime authority. Submission sends to the existing review queue, with local draft/download support retained. Tests mock submission and create no database records. No migrations or project settings were changed, and no SQL files were imported.

The browser client contains only the existing browser publishable key, which is designed for client distribution. Never copy `.env.local`, secret/service-role keys, database exports or credentials. Hero portraits and logo used from WordPress are packaged in `dist/media/`; Commons portraits and Google fonts still require network access.

Validation: the seven documented core checks plus snapshot replacement, category performance, fast startup and lazy game routes pass. Entry assets and CSS local URLs resolve. Live Supabase read could not be verified from this command environment (network fetch failed); no database write was attempted. These are Node/VM checks, not a claim of desktop/mobile visual QA. GitHub pushes do not deploy Sites or WordPress.

## GitHub-first operation

Run `node scripts/serve-local.cjs` from `poetics/` or use `START-POETICS.cmd` on Windows. This serves only `dist/` on `127.0.0.1:4173`; no WordPress or LocalWP service is needed. Python remains an alternative. Edit readable source in a new branch from current main, regenerate delivery files, run checks, and merge reviewed changes. Pull main into any optional staging copy.

For website delivery, the intended flow is GitHub main -> an approved build/deployment process -> the website serving `poetics/dist/` -> browser requests to the existing Supabase API. Visitors load code from the website host; GitHub remains its source. No website deployment, public host connection, database migration or Supabase setting change was performed by this merge. A private GitHub repository does not make browser-delivered JavaScript secret; browser code must contain only public configuration.
