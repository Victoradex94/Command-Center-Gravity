@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if not errorlevel 1 (
  node scripts\serve-local.cjs
  goto done
)
set "POETICS_NODE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if exist "%POETICS_NODE%" (
  "%POETICS_NODE%" scripts\serve-local.cjs
  goto done
)
echo Node.js is required. Install it from https://nodejs.org or use the Python instructions in README.md.
:done
pause
