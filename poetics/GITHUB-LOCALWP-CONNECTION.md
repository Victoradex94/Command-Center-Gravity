# GitHub main to LocalWP staging

GitHub main is authoritative. The connector fetches current main into an isolated Git worktree, rebuilds the assets, runs all eleven app checks, rejects build drift and unsafe files, then copies verified files to the local staging poetics folder. It never runs SQL or changes Supabase settings. Atlas reads and the existing review queue continue using the browser publishable key; privileged credentials remain outside the repository.

Manual update, from poetics:

    .\scripts\sync-localwp.ps1 -FromGitHub

A Windows scheduled task named Poetics-GitHub-to-LocalWP runs the same command every five minutes while your Windows session is logged on. LocalWP must be running for the staging website to respond. The task updates app files even when the site is stopped; it does not start WordPress or LocalWP. GitHub changes are available after the next successful check, not immediately after every keystroke.

The task uses a dedicated checkout alongside the working repository. Its last result is visible in Windows Task Scheduler. The last run log is poetics-sync.log beside the dedicated checkout. On fetch, build or test failure, staging is not updated. Replaced files are backed up beside that checkout under poetics-sync-backups with a timestamp. Entry assets are copied before index.html; old files and .env.local are retained. This is a local staging connection, not live-site hosting.

To inspect or stop the connector in PowerShell:

    Get-ScheduledTaskInfo -TaskName Poetics-GitHub-to-LocalWP
    Disable-ScheduledTask -TaskName Poetics-GitHub-to-LocalWP

To import a specific staging source change, first create a clean review branch. Name only the readable files you reviewed:

    .\scripts\sync-localwp.ps1 -ToGitHub -ImportFiles directory.js,vicadex-theme.css

Imports build and test in isolation, then apply only the resulting app/source changes to that review branch. They do not commit, push or merge. Blanket imports, generated asset imports, hidden files, private keys, SQL files, path escapes and symlinks/junctions are rejected. Existing research and archive files are not replaced.

CI rebuilds assets, runs the app and sync-safety checks, and fails on either tracked differences or untracked generated files. Regenerate and commit the readable sources plus their delivery assets before merging.
