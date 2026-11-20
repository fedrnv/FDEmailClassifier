param([string]$Source)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
$python=Join-Path $root '.venv/ingestion/Scripts/python.exe'
if(!(Test-Path -LiteralPath $python -PathType Leaf)){throw 'Create the pinned ingestion environment before Sinabis checks'}
Push-Location $root
try{
    & $python -m unittest discover -s training/augmentation -p test_sinabis.py -v
    if($LASTEXITCODE -ne 0){throw 'Sinabis reviewed-source/preparation software checks failed'}
    if($Source){
        & $python training/augmentation/sinabis_source.py --source $Source --opt-in
        if($LASTEXITCODE -ne 0){throw 'Pinned private Sinabis source preparation failed'}
    }
    Write-Output 'PASS: Sinabis exact source review, origin quarantine, untrusted mapping, language extension, duplicate and split protections; no actual training or release'
}finally{Pop-Location}
