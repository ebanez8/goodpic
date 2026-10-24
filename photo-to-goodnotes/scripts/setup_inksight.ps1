$ErrorActionPreference = "Stop"
$repo = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'external/inksight'
if (-not (Test-Path (Join-Path $repo 'uv.lock'))) { throw "Clone https://github.com/google-research/inksight to $repo first." }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Install uv first: https://docs.astral.sh/uv/' }
Push-Location $repo
try {
    uv sync --locked
    if ($LASTEXITCODE -ne 0) { throw 'InkSight uv sync failed.' }
} finally { Pop-Location }
