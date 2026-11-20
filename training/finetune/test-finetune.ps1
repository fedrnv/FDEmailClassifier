param([string]$Python)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
if(-not $Python){$Python=Join-Path $root '.venv/ingestion/Scripts/python.exe'}
& $Python -m unittest discover -s "$PSScriptRoot/tests" -p 'test_*.py' -v
if($LASTEXITCODE -ne 0){throw 'Trainer software checks failed'}
& $Python "$PSScriptRoot/train.py" preflight
if($LASTEXITCODE -ne 0){throw 'Trainer availability check failed'}
Write-Output 'SOFTWARE_CHECKS=PASS; SUPPORTED_GPU_ACCEPTANCE=NOT_RUN'
