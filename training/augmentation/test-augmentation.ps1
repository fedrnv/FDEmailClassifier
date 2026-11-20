$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Push-Location $root
try {
    & py -3.14 -m unittest discover -s training/augmentation -p test_augmentation.py -v
    if($LASTEXITCODE -ne 0){throw 'Augmentation software fixture verification failed'}
    Write-Output 'PASS: quota/translation software fixtures, provenance, rights denial, privacy and transactional recovery'
    Write-Output 'INCOMPLETE: fixture pack is not approved training/evaluation data; FDEC-011 remains open for suitable source rights'
} finally { Pop-Location }
