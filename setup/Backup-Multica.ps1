param([string]$Repo = (Join-Path $PSScriptRoot '../../multica'))
$ErrorActionPreference = 'Stop'
function Check-Native { if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" } }
$destination = Join-Path $PSScriptRoot ('../.local/backups/' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$destination = (Resolve-Path $destination).Path
Push-Location $Repo
try {
    # Dump inside the container to avoid binary corruption from PowerShell redirection.
    docker compose -f docker-compose.selfhost.yml exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/recsys-backup.dump'
    Check-Native
    docker compose -f docker-compose.selfhost.yml exec -T postgres pg_restore --list /tmp/recsys-backup.dump
    Check-Native
    docker compose -f docker-compose.selfhost.yml cp postgres:/tmp/recsys-backup.dump (Join-Path $destination 'postgres.dump')
    Check-Native
    docker compose -f docker-compose.selfhost.yml cp backend:/app/data/uploads (Join-Path $destination 'uploads')
    Check-Native
    Copy-Item -LiteralPath '.env' -Destination (Join-Path $destination '.env')
    Write-Host "Backup saved to $destination. It contains secrets; keep it private. Test restoration before upgrades."
} finally { Pop-Location }
