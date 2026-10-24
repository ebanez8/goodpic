param([string]$Python = "")
$ErrorActionPreference = "Stop"
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$venv = Join-Path $project '.venv'
if (-not $Python) {
    $localPython = Join-Path $env:LOCALAPPDATA 'Programs/Python/Python311/python.exe'
    if (Test-Path $localPython) {
        $Python = $localPython
    } elseif (Get-Command python3.11 -ErrorAction SilentlyContinue) {
        $Python = 'python3.11'
    } else {
        throw 'Python 3.11 not found. Install it, or pass -Python with its executable path.'
    }
}
$version = & $Python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
if ($LASTEXITCODE -ne 0 -or $version -ne '3.11') { throw "Expected Python 3.11; found $version" }
if (-not (Test-Path (Join-Path $venv 'Scripts/python.exe'))) {
    & $Python -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
$pythonExe = Join-Path $venv 'Scripts/python.exe'
& $pythonExe -m pip install -e "$project[dev]"
if ($LASTEXITCODE -ne 0) { throw 'Package installation failed.' }
& $pythonExe (Join-Path $project 'scripts/check_environment.py')
