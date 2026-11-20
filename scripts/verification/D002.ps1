param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{40}$')][string]$ExpectedSource)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/d002-source.ps1"
$script:frozen=$null
$stages=[Collections.Generic.List[object]]::new()
function Frozen {
    $current=Assert-D002Source $root $ExpectedSource $script:frozen
    if(!$script:frozen){$script:frozen=$current}
}
function Stage([string]$Name,[string]$Command,[scriptblock]$Run) {
    Frozen
    Write-Output "STAGE: $Name"
    & $Run
    if($LASTEXITCODE -ne 0){throw "D002 stage failed: $Name"}
    Frozen
    $stages.Add(@{name=$Name;command=$Command;result='PASS'})
}
Push-Location $root
try{
    Frozen
    $python=Join-Path $root '.venv/ingestion/Scripts/python.exe'
    if(!(Test-Path -LiteralPath $python -PathType Leaf)){throw 'D002 pinned ingestion environment missing'}
    Stage 'source freeze negatives' 'powershell -NoProfile -File scripts/verification/test-d002-source.ps1' {& powershell -NoProfile -File scripts/verification/test-d002-source.ps1}
    Stage 'rights and verified ingestion' 'powershell -NoProfile -File training/datasets/test-ingestion.ps1' {& powershell -NoProfile -File training/datasets/test-ingestion.ps1}
    Stage 'annotation and classification schemas' 'powershell -NoProfile -File training/labels/test-mapping.ps1' {& powershell -NoProfile -File training/labels/test-mapping.ps1}
    Stage 'fixture generation and independent-input boundary' 'powershell -NoProfile -File training/augmentation/test-native.ps1' {& powershell -NoProfile -File training/augmentation/test-native.ps1}
    Stage 'Sinabis reviewed-source preparation contract' 'powershell -NoProfile -File training/augmentation/test-sinabis.ps1' {& powershell -NoProfile -File training/augmentation/test-sinabis.ps1}
    Stage 'current consent and split protection' 'powershell -NoProfile -File training/splits/test-splits.ps1' {& powershell -NoProfile -File training/splits/test-splits.ps1}
    Stage 'cross-component data pipeline' '.venv/ingestion/Scripts/python.exe -m unittest discover -s tests/d002 -p test_pipeline.py -v' {& $python -m unittest discover -s tests/d002 -p test_pipeline.py -v}
    Stage 'unchanged Rust classification contract' 'cargo test --locked --offline -p fdemailclassifier-core schema' {& cargo test --locked --offline -p fdemailclassifier-core schema}
    Frozen
    $tree=@(D002-Git $root @('rev-parse',($ExpectedSource+'^{tree}')))[0]
    $pin=Get-Content Tasks/policy/adoption-5.6.json -Raw | ConvertFrom-Json
    $result=[ordered]@{schema='fdec-gate-result/v1';task_id='FDEC-013';epic_id='FDEC-EPIC-D002';candidate_sha=$ExpectedSource;candidate_tree=$tree;policy_sha256=$pin.policy_sha256;result='PASS';exit_code=0;source_state_sha256=$script:frozen;stages=$stages.ToArray();scope='D002 software integration with isolated technical fixtures and pinned public rights metadata';actual_training_performed=$false;actual_dataset_train_test_admission='not_verified_by_this_gate';model_release_approved=$false}
    Write-Output 'GATE_RESULT_BEGIN'
    $result | ConvertTo-Json -Depth 12
    Write-Output 'GATE_RESULT_END'
    Write-Output "PASS: D002 changed-area integration on $ExpectedSource"
}finally{Pop-Location}
