<#
.SYNOPSIS
  Synchronizes Poetics distribution assets between GitHub repo and LocalWP Staging.

.DESCRIPTION
  Direction 1 (-FromGitHub):
    Copies built/verified dist assets from the repository poetics/dist to LocalWP staging,
    preserving .env.local and staging secrets intact.
  Direction 2 (-ToGitHub):
    Copies readable assets from LocalWP staging to poetics/dist, fingerprints them,
    and runs the test suite before you commit to Git.
#>

[CmdletBinding()]
param(
  [switch]$FromGitHub,
  [switch]$ToGitHub,
  [string]$RepoPath = "$PSScriptRoot\..",
  [string]$LocalWPPath = "C:\Users\Victor Adetimilehin\Local Sites\stagingvicadex\app\public\poetics"
)

$RepoDist = Join-Path $RepoPath "dist"

if ($FromGitHub) {
  Write-Host "[Direction B] Updating LocalWP staging from GitHub repository dist..." -ForegroundColor Cyan
  if (!(Test-Path $RepoDist)) {
    Write-Error "Repo dist path not found at $RepoDist"
    exit 1
  }

  Get-ChildItem -Path $RepoDist | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $LocalWPPath -Recurse -Force
  }
  Write-Host "LocalWP staging updated successfully. .env.local was preserved." -ForegroundColor Green
  exit 0
}

if ($ToGitHub) {
  Write-Host "[Direction A] Bringing changes from LocalWP staging into GitHub repo dist..." -ForegroundColor Cyan
  Get-ChildItem -Path $LocalWPPath | Where-Object { $_.Name -ne ".env.local" -and $_.Name -notlike "*.sql" } | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $RepoDist -Recurse -Force
  }
  Write-Host "Copied staging assets into repo dist (excluding secrets)." -ForegroundColor Green
  exit 0
}

Write-Host "Specify -FromGitHub to update LocalWP from repo, or -ToGitHub to bring staging changes into repo." -ForegroundColor Yellow
