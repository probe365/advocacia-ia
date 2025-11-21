Param(
  [switch]$ForceRecreate
)

$ErrorActionPreference = 'Stop'

Write-Host '==> Checking Python version'
python --version

if (-Not (Test-Path .venv) -or $ForceRecreate) {
  if (Test-Path .venv -and $ForceRecreate) { Write-Host '==> Removing existing venv'; Remove-Item -Recurse -Force .venv }
  Write-Host '==> Creating virtual environment'
  python -m venv .venv
}

Write-Host '==> Activating virtual environment'
. .\.venv\Scripts\Activate.ps1

Write-Host '==> Upgrading pip'
pip install --upgrade pip > $null

Write-Host '==> Installing dependencies'
pip install -r requirements.txt -r requirements-dev.txt

if (-Not (Test-Path .env)) {
  Write-Host '==> Copying .env.example to .env (edit values as needed)'
  Copy-Item .env.example .env
}

Write-Host '==> Applying migrations'
$env:FLASK_APP = 'manage.py'
flask db upgrade

Write-Host '==> Launching Flask dev server (CTRL+C to stop)'
flask run -p 5001
