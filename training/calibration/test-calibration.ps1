param([string]$Python)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
if(-not $Python){$Python=Join-Path $root '.venv/ingestion/Scripts/python.exe'}
& $Python -m unittest discover -s "$PSScriptRoot/tests" -p 'test_*.py' -v
if($LASTEXITCODE -ne 0){throw 'Calibration Python checks failed'}
Push-Location $root
try {
    cargo test --offline -p fdemailclassifier-core schema::
    if($LASTEXITCODE -ne 0){throw 'Calibration/core-schema Rust checks failed'}
} finally {Pop-Location}
Write-Output 'CALIBRATION_ACCEPTANCE=PASS; ACTUAL_MODEL_CALIBRATION=NOT_MEASURED; PROBABILITIES=NOT_ESTIMATED'
