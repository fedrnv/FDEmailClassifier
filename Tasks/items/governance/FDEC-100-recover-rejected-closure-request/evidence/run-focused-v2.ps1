param(
    [Parameter(Mandatory=$true)][string]$ExpectedSource,
    [Parameter(Mandatory=$true)][ValidateSet('test-source-readiness.ps1','test-readiness-events.ps1','test-acceptance-matrix.ps1','test-identity.ps1','test-plan-sync.ps1','test-reopened-requests.ps1','repository.ps1')][string]$Stage
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
. "$root/scripts/validate_tasks/source-state.ps1"
Set-Location $root
$head=git -C $root rev-parse HEAD
if($LASTEXITCODE -ne 0 -or $head -cne $ExpectedSource){throw 'Wrong focused verification source'}
# The first three passing stages retain their actual original source attribution.
# Their implementation must be unchanged, rather than silently counted as reruns.
$previous='6cab0e941f63b00457715f55a1109415a113fbc5'
git -C $root diff --quiet $previous HEAD -- scripts/validate_tasks/request-recovery.ps1 scripts/validate_tasks/repository.ps1 scripts/validate_tasks/fixture-matrix.ps1 scripts/validate_tasks/test-request-recovery.ps1 scripts/validate_tasks/check-adoption.ps1 scripts/validate_tasks/test-validation.ps1
if($LASTEXITCODE -ne 0){throw 'Prior passing implementation changed; affected evidence must be rerun'}
$state=Get-SourceState $root 'FDEC-100'
$requestHash=(Get-FileHash "$root/Tasks/version-requests/FDEC-099.json" -Algorithm SHA256).Hash
Write-Output "STAGE: $Stage; SOURCE: $ExpectedSource"
& powershell -NoProfile -File (Join-Path $root "scripts/validate_tasks/$Stage")
if($LASTEXITCODE -ne 0){throw "Stage failed: $Stage"}
$head=git -C $root rev-parse HEAD
if($LASTEXITCODE -ne 0 -or $head -cne $ExpectedSource -or (Get-SourceState $root 'FDEC-100') -cne $state -or (Get-FileHash "$root/Tasks/version-requests/FDEC-099.json" -Algorithm SHA256).Hash -cne $requestHash){throw 'Source or original request changed during focused verification'}
[ordered]@{schema='fdec-focused-process-verification/v1';task_id='FDEC-100';result='PASS';source_sha=$ExpectedSource;source_state_sha256=$state;stage=$Stage;prior_component_evidence_source=$previous;original_request_raw_sha256=$requestHash.ToLowerInvariant();allocated=$false;published=$false}|ConvertTo-Json -Depth 8
