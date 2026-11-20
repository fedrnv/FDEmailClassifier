$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Push-Location $root
try {
    & py -3.14 -m unittest discover -s training/augmentation -p test_augmentation.py -v
    if($LASTEXITCODE -ne 0){throw 'Existing augmentation regression failed'}
    & py -3.14 -m unittest discover -s training/augmentation -p test_native.py -v
    if($LASTEXITCODE -ne 0){throw 'Native software quality or rights-boundary verification failed'}
    Write-Output 'PASS: original native grammar software, variation, synthetic identities, multilingual capacity, duplicate/lineage checks and unchanged fixture denial'
    Write-Output 'INCOMPLETE: native commercial_training admission lacks documented applicable provider/source rights; this is not AC-04 acceptance or task closure'
} finally { Pop-Location }
