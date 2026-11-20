param([string]$Python)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
if(-not $Python){$Python=Join-Path $root '.venv/ingestion/Scripts/python.exe'}
& $Python -m unittest discover -s "$PSScriptRoot/tests" -p 'test_*.py' -v
if($LASTEXITCODE -ne 0){throw 'Baseline software checks failed'}
& $Python "$PSScriptRoot/baseline.py" preflight
if($LASTEXITCODE -ne 0){throw 'Baseline availability check failed'}
Write-Output 'SOFTWARE_CHECKS=PASS; ACTUAL_STOCK_MODEL_BENCHMARK=NOT_RUN'
