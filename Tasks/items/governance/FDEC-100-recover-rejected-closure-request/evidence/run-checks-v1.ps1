param([Parameter(Mandatory=$true)][string]$ExpectedSource)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
. "$root/scripts/validate_tasks/source-state.ps1"
Set-Location $root
$state=Get-SourceState $root 'FDEC-100'
function Frozen {
    $head=git -C $root rev-parse HEAD
    if($LASTEXITCODE -ne 0 -or $head -cne $ExpectedSource -or (Get-SourceState $root 'FDEC-100') -cne $state){throw 'FDEC-100 source changed during verification'}
}
$stages=@('test-request-recovery.ps1','check-adoption.ps1','test-validation.ps1','test-source-readiness.ps1','test-readiness-events.ps1','test-acceptance-matrix.ps1','test-identity.ps1','test-plan-sync.ps1','test-reopened-requests.ps1','repository.ps1')
foreach($stage in $stages){
    Frozen
    Write-Output "STAGE: $stage"
    & powershell -NoProfile -File (Join-Path $root "scripts/validate_tasks/$stage")
    if($LASTEXITCODE -ne 0){throw "Stage failed: $stage"}
    Frozen
}
[ordered]@{schema='fdec-process-verification/v1';task_id='FDEC-100';result='PASS';source_sha=$ExpectedSource;source_state_sha256=$state;stages=$stages;stage_count=$stages.Count;original_request_unchanged=$true;actual_training_performed=$false;allocated=$false;published=$false}|ConvertTo-Json -Depth 8
