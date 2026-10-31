param([string]$Repo = (Join-Path $PSScriptRoot '../../multica'))
$ErrorActionPreference = 'Stop'
$repoPath = (Resolve-Path -LiteralPath $Repo).Path
$git = (Get-Command git -ErrorAction SilentlyContinue).Source
if (-not $git) { $git = 'C:/Program Files/Git/cmd/git.exe' }
function Check-Native { if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" } }
Get-Command docker -ErrorAction Stop | Out-Null
docker info | Out-Null
Check-Native
$revision = & $git -c "safe.directory=$repoPath" -C $repoPath rev-parse HEAD
Check-Native
if ($revision -ne 'e8ae72c9dfc1b4474b61a9087f51b33cbee6a048') {
    throw 'Checkout differs from inspected revision; review the new Compose and CLI before deployment.'
}
$dirty = & $git -c "safe.directory=$repoPath" -C $repoPath status --porcelain
Check-Native
if ($dirty) { throw 'Multica checkout has changes; preserve and review them before building.' }
function Random-Secret([int]$Length, [bool]$Base64 = $false) {
    $bytes = New-Object byte[] $Length
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    if ($Base64) { return [Convert]::ToBase64String($bytes) }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}
$envFile = Join-Path $repoPath '.env'
if (-not (Test-Path -LiteralPath $envFile)) {
    $content = Get-Content (Join-Path $repoPath '.env.example') -Raw
    $password = Random-Secret 24
    $content = $content -replace '(?m)^JWT_SECRET=.*$', ('JWT_SECRET=' + (Random-Secret 32))
    $content = $content -replace '(?m)^POSTGRES_PASSWORD=.*$', ('POSTGRES_PASSWORD=' + $password)
    $content = $content -replace '(?m)^(DATABASE_URL=postgres://[^:]+:)[^@]*', ('${1}' + $password)
    $content = $content -replace '(?m)^MULTICA_VCS_SECRET_KEY=.*$', ('MULTICA_VCS_SECRET_KEY=' + (Random-Secret 32 $true))
    $content = $content -replace '(?m)^MULTICA_SLACK_SECRET_KEY=.*$', ('MULTICA_SLACK_SECRET_KEY=' + (Random-Secret 32 $true))
    [IO.File]::WriteAllText($envFile, $content, (New-Object Text.UTF8Encoding $false))
}
Push-Location $repoPath
try {
    $env:COMMIT = $revision
    docker compose -f docker-compose.selfhost.yml -f docker-compose.selfhost.build.yml up -d --build
    Check-Native
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $health = Invoke-RestMethod 'http://localhost:8080/readyz'
            if ($health.status -eq 'ok') { $ready = $true; break }
        } catch { }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw 'Readiness failed. Inspect docker compose logs; setup is incomplete.' }
    Write-Host 'Multica ready: http://localhost:3000. Create your workspace, then connect the daemon.'
} finally { Pop-Location }
