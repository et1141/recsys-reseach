param([ValidateSet('recbole', 'torch', 'lightning')][string]$Framework = 'recbole')
$ErrorActionPreference = 'Stop'
function Check-Native { if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" } }
Get-Command uv -ErrorAction Stop | Out-Null
Push-Location (Join-Path $PSScriptRoot '..')
try {
    if (-not (Test-Path uv.lock)) {
        uv lock
        Check-Native
    }
    uv sync --frozen --extra $Framework
    Check-Native
    uv run --frozen --extra $Framework ruff check scripts setup tests
    Check-Native
    uv run --frozen --extra $Framework pytest
    Check-Native
    Write-Host 'Commit uv.lock and the experiment configuration. Scientific runs require reviewer approval.'
} finally { Pop-Location }
