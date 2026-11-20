param([switch]$PrepareSource)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
Push-Location $root
try{
    & powershell -NoProfile -File training/augmentation/test-native.ps1
    if($LASTEXITCODE -ne 0){throw 'Existing fixture and independent-source regression failed'}
    $arguments=@('-NoProfile','-File','training/augmentation/test-sinabis.ps1')
    if($PrepareSource){$arguments+=@('-Source','training/data/sinabis-audit-20261120/source.parquet')}
    & powershell @arguments
    if($LASTEXITCODE -ne 0){throw 'Sinabis component verification failed'}
    Write-Output 'PASS: FDEC-011 selected component checks complete; no model training'
}finally{Pop-Location}
