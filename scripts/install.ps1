$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw "Python 3.12+ is required. Install Python and enable PATH, then retry." }
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.12+ is required." }

if (-not (Test-Path ".venv")) { python -m venv .venv }
& ".\.venv\Scripts\python.exe" "scripts\bootstrap.py" @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Environment ready. Activate with: .\.venv\Scripts\Activate.ps1"
