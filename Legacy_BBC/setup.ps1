param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================"
Write-Host "  BBC v8.6 - One-Command Setup (PowerShell)"
Write-Host "============================================"
Write-Host ""

$python = $null
foreach ($candidate in @("python", "py")) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) {
        $python = $candidate
        break
    }
}

if (-not $python) {
    Write-Host "[ERROR] Python not found. Please install Python 3.10+ first."
    Write-Host "        https://www.python.org/downloads/"
    exit 1
}

$bbcDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $bbcDir

Write-Host "[BBC] BBC directory:     $bbcDir"
Write-Host "[BBC] Project directory: $projectDir"
Write-Host ""

$requirements = Join-Path $bbcDir "requirements.txt"
if (Test-Path $requirements) {
    Write-Host "[BBC] Step 1/2: Installing dependencies..."
    & $python -m pip install -r $requirements -q
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARN] Some dependencies may have failed. Continuing..."
    } else {
        Write-Host "[BBC] Step 1/2: Dependencies installed."
    }
}

Write-Host ""
Write-Host "[BBC] Step 2/2: Starting BBC on project..."
$bbcPy = Join-Path $bbcDir "bbc.py"
if ($Force) {
    & $python $bbcPy start $projectDir --force
} else {
    & $python $bbcPy start $projectDir
}

Write-Host ""
Write-Host "[BBC] Setup complete."
