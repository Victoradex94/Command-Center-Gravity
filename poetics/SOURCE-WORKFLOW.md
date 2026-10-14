# Poetics source and publication workflow

## Primary source
Repository: Victoradex94/Command-Center-Gravity
Folder: poetics/
Primary branch: main
Working branch: poetics-staging (rebase onto current main before edits).

GitHub main is the primary app/data/source version. Sites is a restricted publication mirror. Do not edit a stale Sites checkout and overwrite newer GitHub work.

## Editing from ChatGPT
1. Read the CURRENT canonical Drive ledger:
https://drive.google.com/file/d/13qDg2XVdUM5ZAbplLoeNT5X6hB89cnSq/view
2. Read current GitHub main and relevant actual data, then inspect Sites latest source/publication. Record commits and any divergence.
3. Make scoped changes on a branch in poetics/. Run Python fingerprint-assets and appropriate Node checks. Commit to GitHub; reconcile/merge approved work to main without overwriting newer contributions.
4. To update the visible preview, retrieve the GitHub version and fresh Sites source with the supported helper. Reconcile both, copy the reviewed application source into the Sites checkout, check/build, push via Sites helper, save and publish to the SAME restricted audience.
5. Record GitHub commit, Sites source commit/version, data counts and verification limits in the ledger; read back ledger updates.

GitHub pushes do not automatically publish Sites. There is no configured bidirectional sync or GitHub-to-Sites deployment integration. Available Sites tools do not expose rebinding the source repository to this external GitHub repository. The preview rendered in ChatGPT remains hosted on Sites; this workflow makes its reviewed source come from GitHub.

## Preserved artifacts
Editable current files and supporting research are directly in this folder. archives/sites-v45-retained-artifacts.tar.gz preserves all 38 omitted legacy fingerprint bundles/WordPress packaging files from the migration baseline. Extract only when needed; this is an archive, not a deployment.
Original Sites source/history remains intact. No live WordPress deployment, no public hosting or domain/access changes.
The Drive Markdown ledger remains the single current working task tracker, not a second GitHub ledger.

## Local preview
From this folder with Python 3:
python -m http.server 4173 --directory dist
Open http://localhost:4173/#/atlas
See LOCAL-STAGING.md for checks.
