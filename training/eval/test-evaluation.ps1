param([string]$Python)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
if(-not $Python){$Python=Join-Path $root '.venv/ingestion/Scripts/python.exe'}
& $Python -m unittest discover -s "$PSScriptRoot/tests" -p 'test_*.py' -v
if($LASTEXITCODE -ne 0){throw 'Evaluation acceptance checks failed'}
Write-Output 'EVALUATION_SUITE_ACCEPTANCE=PASS; ACTUAL_MODEL_QUALITY=NOT_MEASURED'
