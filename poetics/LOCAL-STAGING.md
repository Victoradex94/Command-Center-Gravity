# Poetics — local staging

Private source copy of the Vic’Adex Sites prototype, Version 45.

## Run locally

Clone this repository, switch to `poetics-staging`, and open the `poetics` folder in your editor. With Python 3 installed, run:

    python -m http.server 4173 --directory dist

Open http://localhost:4173/#/atlas . Do not open index.html directly: local HTTP is needed for data files. Stop with Ctrl+C.

## Edit and check

Edit the original non-fingerprinted files in dist. After edits, run from this folder:

    python scripts/fingerprint-assets.py
    node test-hourly-first-check.cjs
    node test-directory.cjs
    node test-map-first.cjs
    node test-states-and-prizes.cjs

Node.js is required for checks. Regenerate the entrypoint fingerprints before committing.

## Preview and editing from ChatGPT

Restricted Sites preview: https://poetics-vicadex-lab.vicadexconcepts.chatgpt.site/#/atlas
Sites project: appgprj_6acce9493e8c81919635a9e7438b820c
Source checkpoint: 03bb00a7998fe1113f2d78a2aab4607f8161fa6d
Baseline:449 entries/664 relationships.

ChatGPT can continue editing this folder through the connected GitHub repository. GitHub commits do not automatically update Sites. When publishing is requested, read the current GitHub branch and Sites source, reconcile both, run checks, then use the supported Sites save/publish workflow with the existing restricted audience. Never overwrite newer work.

The canonical working task ledger remains https://drive.google.com/file/d/13qDg2XVdUM5ZAbplLoeNT5X6hB89cnSq/view . Read it fresh before research/task changes; research/ contains supporting artifacts, not a replacement ledger.

## Boundaries

No GitHub Pages deployment or domain/sharing change configured. No live WordPress edits. Existing production WordPress plugin packaging remains in the original Sites source; superseded generated fingerprint bundles are omitted here. Original app/data/research are preserved, with current fingerprint assets for index.html. Old editions/plans/source uncertainty must remain qualified. No city outline implementation yet.
