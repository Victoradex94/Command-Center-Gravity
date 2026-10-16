# Poetics source and publication workflow

## Current source of truth

- Repository: `Victoradex94/Command-Center-Gravity`, folder `poetics/`.
- Current branch: `main`; start new work branches from its latest commit.
- Current code snapshot: Version 76. Read current main for the exact GitHub commit; its matching Sites source checkpoint is listed below.
- The `poetics-staging` branch is an older Version 45 snapshot. Do not use it as the base for new work.
- Sites project: `appgprj_6acce9493e8c81919635a9e7438b820c`; current restricted publication Version 76; its separately managed Sites source checkpoint is `e22287464f447cfec4f664c3b9ddf7be7b870b2e`.

GitHub is the editable source mirror. The Sites app uses its own managed source repository. GitHub and Sites do not synchronize automatically, and a GitHub commit does not change the preview.

## Before research or data changes

1. Read the latest canonical Drive Markdown ledger: https://drive.google.com/file/d/13qDg2XVdUM5ZAbplLoeNT5X6hB89cnSq/view . Do not use an old download as authority.
2. Fetch current GitHub `main` and the current Sites source/version; record their commit/version identifiers and inspect for divergence.
3. Preserve newer work from either source. Use `research/` artifacts as supporting evidence, not as a replacement task ledger.

## GitHub development

1. Clone the private repository and work under `poetics/`.
2. Create a new working branch from current `main`, for example `poetics-work`; do not start from the stale `poetics-staging` branch.
3. Edit readable, non-fingerprinted files. After source edits, run `python scripts/fingerprint-assets.py` from `poetics/`.
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

- Current Atlas tests verify 453 records and 667 source-linked relationships. Preserve source attribution, date precision, name variants, uncertainty and planned-versus-completed distinctions.
- Fictional game events and player state remain separate from historical records. Game saves currently use localStorage; no account/cloud save is configured.
- The Submit flow produces a local draft; it is not an editorial intake backend.
- State boundaries and prepared urban extents are different geographic products. Urban footprints are not legal city limits; missing detailed layers must not be described as zero cultural activity.
- `wordpress/poetics-preview/` is package source only. Do not deploy or alter live WordPress.

