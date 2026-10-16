# Poetics — local setup and staging

Current working source: Version 76, in `main` at `Victoradex94/Command-Center-Gravity/poetics/`. The GitHub version is separate from the restricted Sites preview; GitHub pushes do not deploy it.

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

    python scripts/fingerprint-assets.py

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
- App behavior: game saves are browser-local; Submit downloads/stores a draft locally and does not send it to an editorial backend.
- Map data: Nigerian state outlines are available nationally. Prepared urban layers are not universal city/legal boundaries; absent or failed detailed layers fall back to state outlines.

Full project and source workflow: see [README.md](README.md) and [SOURCE-WORKFLOW.md](SOURCE-WORKFLOW.md).
