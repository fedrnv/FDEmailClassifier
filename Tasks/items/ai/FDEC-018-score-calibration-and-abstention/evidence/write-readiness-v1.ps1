param([Parameter(Mandatory=$true)][string]$Name,[switch]$Closing)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
$task=Split-Path $PSScriptRoot
$relative=$task.Substring($root.Length+1).Replace('\','/')
. "$root/scripts/validate_tasks/identity.ps1"
. "$root/scripts/validate_tasks/source-state.ps1"
. "$root/scripts/validate_tasks/acceptance-matrix.ps1"
. "$root/scripts/validate_tasks/readiness-events.ps1"
. "$root/scripts/validate_tasks/identity-migrations.ps1"
function Bind($path){@{path=$path;sha256=(Get-IdentityHash (Join-Path $root $path))}}
$records=& "$root/scripts/validate_tasks/repository.ps1" -Root $root -AsObject
$effective=Get-EffectiveCriteria $root $task
$record=$records['FDEC-018'];$parent=$records[$record.parent]
$paths=@(foreach($id in @($record.dependencies)+@($parent.dependencies)){foreach($path in $records[$id].state_paths){$path.Substring($root.Length+1).Replace('\','/')}})
$migrationPaths=@(foreach($file in Get-ChildItem "$root/Tasks/migrations" -Filter '*.json'){Get-MigrationPaths $root $file.FullName})
$rules=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json')
foreach($scope in 'training/calibration','crates/core/src/schema'){
    if(Test-Path (Join-Path $root $scope)){$rules+=@(Get-ChildItem (Join-Path $root $scope) -Recurse -File | Where-Object Name -In 'AGENTS.md','DEVELOPMENT.md' | ForEach-Object {$_.FullName.Substring($root.Length+1).Replace('\','/')})}
}
$ready=[ordered]@{
    semantic_review='accepted';task_sha256=(Get-IdentityHash "$task/TASK.md");policy_sha256=(Get-Content "$root/Tasks/policy/adoption-5.6.json" -Raw | ConvertFrom-Json).policy_sha256
    source_sha=(git -C $root rev-parse HEAD);source_state_algorithm='fdec-source-state/v1';source_state_sha256=(Get-SourceState $root 'FDEC-018')
    outcome_inputs=@('Tasks/epics/FDEC-EPIC-D002/evidence/outcome-continuity-v1.json','docs/verification/verify-d002-outcome-v2.ps1','Tasks/items/quality/FDEC-099-reconcile-d002-effective-outcome/evidence/result-v2.json','Tasks/items/governance/FDEC-100-recover-rejected-closure-request/evidence/closure-readiness-v1.json'|ForEach-Object {Bind $_})
    model_observation=(Bind 'Tasks/items/ai/FDEC-015-zero-shot-baseline/evidence/qwen-observations-v1.json')
    atomicity=@{outcomes=@('Calibrate per-label thresholds and uncertainty; document unsupported or low-confidence cases without fabricated probabilities.');packets=@('Implement validation-only per-label margin thresholds, uncertainty bands, Rust abstention and held-out numeric fixture checks');independent_acceptance=$false;boundary_reason='One calibration/abstention outcome; numeric technical fixtures establish mechanics without probabilities or actual model calibration claims'}
    allowed_paths=@('training/calibration','crates/core/src/schema')
    rule_sources=@($rules | Select-Object -Unique | ForEach-Object {Bind $_})
    dependency_revisions=@($paths | Select-Object -Unique | ForEach-Object {Bind $_})
    epic_state_evidence=@(foreach($epic in $records.Values){if($epic.epic){foreach($path in $epic.state_paths){Bind $path.Substring($root.Length+1).Replace('\','/')}}})
    migration_revisions=@($migrationPaths | Select-Object -Unique | ForEach-Object {Bind $_})
    criteria_revisions=$effective.revisions
    matrix=@(foreach($criterion in $effective.rows){@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;scenario=$criterion.criterion;level='Held-out numerical calibration and Rust threshold boundary acceptance';command='powershell -NoProfile -File training/calibration/test-calibration.ps1';environment='Windows PowerShell, CPython 3.14.5/PyArrow 26.0.1, cached AJV/Rust dependencies; generated software-only fixtures';expected='Fit thresholds only on validation observations; hold out independent test groups, verify boundaries, support/missing-score abstention, stability and Rust parity. No fabricated probabilities or actual model quality claim; current source rights, consent and signed score/label review remain mandatory for actual calibration.'}})
    verification=@()
}
if($Closing){$ready.verification=@('verification-v1.md','result-v1.json','test-output-v1.txt','fixture-report-v1.json','fixture-receipt-v1.json','fixture-run-v1.txt' | ForEach-Object {Bind "$relative/evidence/$_"})}
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness evidence is append-only'}
$ready | ConvertTo-Json -Depth 45 | Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
$action=if($Closing){'close'}else{'execute'}
& "$root/scripts/validate_tasks/admission.ps1" -Root $root -TaskId FDEC-018 -Action $action -ReadinessFile "evidence/$Name"
