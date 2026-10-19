<# Fetch and test GitHub main before staging. Imports require named readable files. #>
[CmdletBinding(DefaultParameterSetName='Publish')]
param(
 [Parameter(Mandatory,ParameterSetName='Publish')][switch]$FromGitHub,
 [Parameter(Mandatory,ParameterSetName='Import')][switch]$ToGitHub,
 [Parameter(Mandatory,ParameterSetName='Import')][string[]]$ImportFiles,
 [string]$RepoPath = "$PSScriptRoot\..",
 [string]$LocalWPPath = "C:\Users\Victor Adetimilehin\Local Sites\stagingvicadex\app\public\poetics"
)
$ErrorActionPreference = 'Stop'
$runtime = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies'
$python = Get-Command python -ErrorAction SilentlyContinue
$pythonPath = Join-Path $runtime 'python\python.exe'
if (!(Test-Path -LiteralPath $pythonPath) -and $python) { $pythonPath = $python.Source }
$node = Get-Command node -ErrorAction SilentlyContinue
$nodePath = Join-Path $runtime 'node\bin\node.exe'
if (!(Test-Path -LiteralPath $nodePath) -and $node) { $nodePath = $node.Source }
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Python 3 is required.' }
if (!(Test-Path -LiteralPath $nodePath)) { throw 'Node.js is required.' }
$mode = if ($FromGitHub) { '--from-github' } else { '--to-github' }
$arguments = @('-X','utf8',"$PSScriptRoot\sync-localwp.py",$mode,'--repo-path',$RepoPath,'--localwp-path',$LocalWPPath,'--node',$nodePath)
if ($ToGitHub) { $arguments += '--import-files'; $arguments += $ImportFiles }
$logPath = Join-Path (Split-Path (Split-Path (Resolve-Path -LiteralPath $RepoPath).Path -Parent) -Parent) 'poetics-sync.log'
$arguments += @('--log-file',$logPath)
& $pythonPath @arguments
$syncExit = $LASTEXITCODE
Get-Content -LiteralPath $logPath -Tail 1
if ($syncExit -ne 0) { throw "Poetics sync failed (exit $syncExit). See $logPath" }
