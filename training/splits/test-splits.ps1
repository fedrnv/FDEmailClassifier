$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Push-Location $root
try {
    & py -3.14 -m unittest discover -s training/splits -p test_splits.py -v
    if($LASTEXITCODE -ne 0){throw 'Split leakage/provenance/consent verification failed'}
    Write-Output 'PASS: grouped splits, immutable provenance, current signed consent, rights admission and contamination rejection'
} finally { Pop-Location }
