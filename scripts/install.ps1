$ErrorActionPreference = 'Stop'

# Resolve repository root and venv paths
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$venvPath = Join-Path $repoRoot '.venv'
$venvScripts = Join-Path $venvPath 'Scripts'

# Python version check
$pyVersionStr = (& python --version 2>&1).Split()[1]
if ([version]$pyVersionStr -lt [version]'3.8') {
    Write-Error "Python 3.8+ is required (found $pyVersionStr)."
}

# Create virtual environment if needed
if (-not (Test-Path $venvPath)) {
    Write-Host 'Creating virtual environment (.venv)...'
    & python -m venv $venvPath
} else {
    Write-Host "Virtual environment already exists at $venvPath."
}

# Install project
$pip = Join-Path $venvScripts 'pip.exe'
Write-Host 'Installing project dependencies (pip install -e .)...'
& $pip install -e $repoRoot

# Verify executables
$executables = @('ghostlink', 'ghostlink-decode', 'ghostlink-web')
foreach ($exe in $executables) {
    $exePath = Join-Path $venvScripts ("$exe.exe")
    Write-Host "Verifying $exe..."
    & $exePath --help > $null
}

Write-Host "Activate the virtual environment with:"
Write-Host "  .\\.venv\\Scripts\\Activate.ps1"
Write-Host "(cmd.exe users: .\\.venv\\Scripts\\activate.bat)"
Write-Host "After activation, the 'ghostlink' commands will be on your PATH."
Write-Host 'Installation complete.'
