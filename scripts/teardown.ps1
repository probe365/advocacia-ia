Param(
  [switch]$RemoveVenv,
  [switch]$Docker,
  [switch]$PurgeData
)

$ErrorActionPreference = 'Stop'

Write-Host '==> Teardown starting'

if ($Docker) {
  if (Test-Path docker-compose.yml) {
    Write-Host '==> Stopping Docker Compose stack'
    docker compose down $(if ($PurgeData) { '--volumes --remove-orphans' })
  } else {
    Write-Warning 'docker-compose.yml not found; skipping Docker teardown.'
  }
}

if ($RemoveVenv -and (Test-Path .venv)) {
  Write-Host '==> Removing virtual environment (.venv)'
  Remove-Item -Recurse -Force .venv
}

if ($PurgeData) {
  Write-Host '==> Purging local Chroma embeddings directory (.chroma) if exists'
  if (Test-Path .chroma) { Remove-Item -Recurse -Force .chroma }
  Write-Host '==> Purging Postgres data volume (if Docker)'
  try { docker volume rm $(docker volume ls -q | Select-String 'pgdata') 2>$null } catch {}
}

Write-Host '==> Teardown complete'
