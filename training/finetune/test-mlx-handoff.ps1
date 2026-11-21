param([string]$Python)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
if(-not $Python){$Python=Join-Path $root '.venv/export/Scripts/python.exe'}
& $Python -m unittest discover -s "$PSScriptRoot/mlx_tests" -p 'test_*.py' -v
if($LASTEXITCODE -ne 0){throw 'MLX handoff software checks failed'}
Write-Output 'MLX_HANDOFF_SOFTWARE=PASS; ACTUAL_APPLE_EXECUTION=NOT_RUN; OWNER_TRANSITION=NOT_CONFIRMED; ACTUAL_TRAINING_RETURN=NOT_COMPLETE'
