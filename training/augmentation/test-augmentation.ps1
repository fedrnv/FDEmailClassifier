$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Push-Location $root
try {
    & py -3.14 -m unittest discover -s training/augmentation -p test_augmentation.py -v
    if($LASTEXITCODE -ne 0){throw 'Augmentation software fixture verification failed'}
    Write-Output 'PASS: quota/translation software fixtures, provenance, rights denial, privacy and transactional recovery'
    Write-Output 'Fixture rows remain prohibited for actual training/evaluation; independent data admission is checked by test-native.ps1'
} finally { Pop-Location }
