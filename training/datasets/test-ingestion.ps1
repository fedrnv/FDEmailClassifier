$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
$python=Join-Path $root '.venv/ingestion/Scripts/python.exe'
if(!(Test-Path -LiteralPath $python -PathType Leaf)){throw 'Create the pinned training ingestion environment as documented in INGESTION.md'}
& $python -m unittest discover -s "$root/training/scripts" -p test_ingestion.py -v
if($LASTEXITCODE -ne 0){throw 'Synthetic ingestion acceptance failed'}
& "$PSScriptRoot/test-allowlist.ps1"
& $python -m pip check
if($LASTEXITCODE -ne 0){throw 'Training dependency consistency failed'}
Write-Output 'PASS: opt-in verified private ingestion, MIME/body normalization, dedup provenance, negative recovery and audited inclusion regression'
