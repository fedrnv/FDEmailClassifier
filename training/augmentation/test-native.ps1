$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Push-Location $root
try {
    & py -3.14 -m unittest discover -s training/augmentation -p test_augmentation.py -v
    if($LASTEXITCODE -ne 0){throw 'Existing augmentation regression failed'}
    & py -3.14 -m unittest discover -s training/augmentation -p test_native.py -v
    if($LASTEXITCODE -ne 0){throw 'Native software quality or rights-boundary verification failed'}
    $python=Join-Path $root '.venv/ingestion/Scripts/python.exe'
    if(!(Test-Path -LiteralPath $python -PathType Leaf)){throw 'Create the pinned ingestion environment for independent-source decoder checks'}
    & $python -m unittest discover -s training/augmentation -p test_training_boundary.py -v
    if($LASTEXITCODE -ne 0){throw 'Independent training-source integrity verification failed'}
    Write-Output 'PASS: original native grammar software, variation, synthetic identities, multilingual capacity, duplicate/lineage checks and unchanged fixture denial'
    Write-Output 'PASS: clarified software acceptance; Codex texts/labels remain fixture-only and actual training requires independently audited input, consent and safe splits'
} finally { Pop-Location }
