# Poetics - local setup and staging

Current working source: Release 103, in `main` at `Victoradex94/Command-Center-Gravity/poetics/`.

## 1. Get a local copy

Sign in to GitHub and clone the private repository. In Windows PowerShell:

    git clone https://github.com/Victoradex94/Command-Center-Gravity.git
    cd Command-Center-Gravity/poetics

On macOS/Linux, use the same commands. Start from `main`.

## 2. Open the local Atlas

Requirements: Node.js (or Python 3) and a modern browser. From the `poetics/` folder, run:

    node scripts/serve-local.cjs

Or run `START-POETICS.cmd` on Windows.
Open http://localhost:4173/#/atlas in your browser.

## 3. Make and verify an edit

Edit readable, non-fingerprinted source files in `dist/`. Regenerate their fingerprinted delivery copies after editing:

    python -X utf8 scripts/fingerprint-assets.py

From `poetics/`, run the relevant tests:

    node test-atlas-navigation.cjs
    node test-state-urban-integration.cjs
    node test-directory.cjs
    node test-delivery.cjs
    node test-engine.cjs
    node test-contribute.cjs
    node test-nigeria-gis.cjs

## 4. Save your work

Create a branch from current `main`, commit and push it:

    git switch -c poetics-work
    git status
    git add .
    git commit -m "Describe the Poetics change"
    git push -u origin poetics-work

Do not edit directly on a stale checkout or overwrite newer commits.

## 5. Staging and Environments

- GitHub `main` is authoritative.
- LocalWP staging is synchronized directly from GitHub `main`.
- Fictional game events and player state remain separate from historical records.
- Live submission routes to Supabase; `.env.local` must remain local and never committed.
