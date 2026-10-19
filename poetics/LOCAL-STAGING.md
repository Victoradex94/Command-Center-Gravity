# Poetics — local setup and staging

Current working source: LocalWP release 103 reconciled from GitHub Version 76 at `Victoradex94/Command-Center-Gravity/poetics/`. The GitHub version is separate from the restricted Sites preview; GitHub pushes do not deploy it.

## 1. Get a local copy

Sign in to GitHub and clone the private repository. In Windows PowerShell:

    git clone https://github.com/Victoradex94/Command-Center-Gravity.git
    cd Command-Center-Gravity/poetics

On macOS/Linux, use the same commands. If you do not use Git, download the repository ZIP from GitHub, extract it, and open its `poetics/` folder.

Start from `main`. The existing `poetics-staging` branch is an older Version 45 snapshot.

## 2. Open the local Atlas

Requirements: Python 3 and a modern browser. From the `poetics/` folder, run:

    py -3 -m http.server 4173 --directory dist

On macOS/Linux, use `python3 -m http.server 4173 --directory dist`.

Open http://localhost:4173/#/atlas . Keep the terminal open; stop the server with Ctrl+C. Use a local HTTP server rather than opening `dist/index.html` directly.

## 3. Make and verify an edit

Use any code editor. Edit the readable, non-fingerprinted source files in `dist/`; regenerate their fingerprinted delivery copies after editing:

    python -X utf8 scripts/fingerprint-assets.py

Node.js is required for checks; there is no npm install. From `poetics/`, run the relevant tests:

    node test-atlas-navigation.cjs
    node test-state-urban-integration.cjs
    node test-directory.cjs
    node test-delivery.cjs
    node test-engine.cjs
    node test-contribute.cjs
    node test-nigeria-gis.cjs

## 4. Save your own work

Create a branch from current `main`, then commit and push it:

    git switch -c poetics-work
    git status
    git add .
    git commit -m "Describe the Poetics change"
    git push -u origin poetics-work

Do not edit directly on a stale checkout or overwrite newer commits. The latest checked baseline contains 453 Atlas records and 667 source-linked relationships.

## 5. Know what remains separate

- Research/task authority: read the latest shared Markdown ledger before research changes: https://drive.google.com/file/d/13qDg2XVdUM5ZAbplLoeNT5X6hB89cnSq/view . Files in `research/` support it; they do not replace it.
- Restricted preview: https://poetics-vicadex-lab.vicadexconcepts.chatgpt.site/#/atlas . It is hosted separately by ChatGPT Sites and is not synchronized with GitHub.
- Hosting: no GitHub Pages or independent static host is configured. To host independently, configure a static host with `poetics/dist` as its published directory. No production hosting/domain changes are part of this guide.
- WordPress: the folder `wordpress/poetics-preview/` is source packaging only. Do not deploy it to live Vic’Adex WordPress.
- App behavior: game saves are browser-local; Submit sends to the existing review queue; local drafts and downloads remain available.
- Map data: Nigerian state outlines are available nationally. Prepared urban layers are not universal city/legal boundaries; absent or failed detailed layers fall back to state outlines.

Full project and source workflow: see [README.md](README.md) and [SOURCE-WORKFLOW.md](SOURCE-WORKFLOW.md).

## LocalWP release 103 reconciliation (19 October 2026)

Started from current main `0988b3197f00ade4ed6e1ee55503b6a09ddbbf1c` and compared the local staging build `2026-10-18-release-103`. Readable sources live in `dist/`; fingerprinted files and `research/release-assets.json` are generated with the existing script. GitHub lookup indexes, filter-count caches and packed startup data remain; indexes rebuild after snapshot replacement. Research, archives and historical snapshots are preserved.

The Atlas now reads the existing Supabase snapshot and displays an error/retry when unavailable. The bundled 453-record/667-relationship snapshot remains historical source and test input; it is not the current runtime authority. Submission sends to the existing review queue, with local draft/download support retained. Tests mock submission and create no database records. No migrations or project settings were changed, and no SQL files were imported.

The browser client contains only the existing browser publishable key, which is designed for client distribution. Never copy `.env.local`, secret/service-role keys, database exports or credentials. Hero portraits and logo used from WordPress are packaged in `dist/media/`; Commons portraits and Google fonts still require network access.

Validation: the seven documented core checks plus snapshot replacement, category performance, fast startup and lazy game routes pass. Entry assets and CSS local URLs resolve. Live Supabase read could not be verified from this command environment (network fetch failed); no database write was attempted. These are Node/VM checks, not a claim of desktop/mobile visual QA. GitHub pushes do not deploy Sites or WordPress.
