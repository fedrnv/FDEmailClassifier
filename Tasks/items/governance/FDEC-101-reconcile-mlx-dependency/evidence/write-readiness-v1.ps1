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
$record=$records['FDEC-101'];$parent=$records[$record.parent]
$paths=@(foreach($id in @($record.dependencies)+@($parent.dependencies)){foreach($path in $records[$id].state_paths){$path.Substring($root.Length+1).Replace('\','/')}})
if(!$paths.Count){$paths=@($parent.path.Substring($root.Length+1).Replace('\','/'))}
$migrations=@(foreach($file in Get-ChildItem "$root/Tasks/migrations" -Filter '*.json'){Get-MigrationPaths $root $file.FullName})
$ready=[ordered]@{
    semantic_review='accepted';task_sha256=(Get-IdentityHash "$task/TASK.md");policy_sha256=(Get-Content "$root/Tasks/policy/adoption-5.6.json" -Raw | ConvertFrom-Json).policy_sha256
    source_sha=(git -C $root rev-parse HEAD);source_state_algorithm='fdec-source-state/v1';source_state_sha256=(Get-SourceState $root 'FDEC-101')
    planning_inputs=@('Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/TASK.md','Tasks/items/ai/FDEC-016-lora-qlora-trainer/TASK.md','Tasks/items/ai/FDEC-016-lora-qlora-trainer/evidence/result-v2.json'|ForEach-Object {Bind param([Parameter(Mandatory=$true)][string]$Name,[switch]$Closing)
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
$record=$records['FDEC-101'];$parent=$records[$record.parent]
$paths=@(foreach($id in @($record.dependencies)+@($parent.dependencies)){foreach($path in $records[$id].state_paths){$path.Substring($root.Length+1).Replace('\','/')}})
if(!$paths.Count){$paths=@($parent.path.Substring($root.Length+1).Replace('\','/'))}
$migrations=@(foreach($file in Get-ChildItem "$root/Tasks/migrations" -Filter '*.json'){Get-MigrationPaths $root $file.FullName})
$ready=[ordered]@{
    semantic_review='accepted';task_sha256=(Get-IdentityHash "$task/TASK.md");policy_sha256=(Get-Content "$root/Tasks/policy/adoption-5.6.json" -Raw | ConvertFrom-Json).policy_sha256
    source_sha=(git -C $root rev-parse HEAD);source_state_algorithm='fdec-source-state/v1';source_state_sha256=(Get-SourceState $root 'FDEC-101')
    recovery_inputs=@('Tasks/request-recoveries/FDEC-099-R001.json','Tasks/policy/rejected-request-recovery-1.0.md','Tasks/version-requests/FDEC-099.json','Tasks/items/quality/FDEC-099-reconcile-d002-effective-outcome/evidence/closure-readiness-v1.json','Tasks/items/quality/FDEC-099-reconcile-d002-effective-outcome/evidence/post-closure-rejection-v1.json'|ForEach-Object {Bind $_})
    atomicity=@{outcomes=@('Reconcile MLX dependency with preserved CUDA and Epic acceptance');packets=@('Implement and verify one explicit adopted dependency amendment and shared admission boundaries');independent_acceptance=$false;boundary_reason='One contradictory MLX dependency; no acceptance reduction, rights waiver or device switch'}
    allowed_paths=@('scripts/validate_tasks','Tasks/dependency-amendments','Tasks/policy/dependency-amendment-1.0.md','Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/events','Tasks/epics/FDEC-EPIC-S001/events','docs/training/MACBOOK_M4_HANDOFF.md')
    rule_sources=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json' | ForEach-Object {Bind $_})
    dependency_revisions=@($paths | Select-Object -Unique | ForEach-Object {Bind $_})
    epic_state_evidence=@(foreach($epic in $records.Values){if($epic.epic){foreach($path in $epic.state_paths){Bind $path.Substring($root.Length+1).Replace('\','/')}}})
    migration_revisions=@($migrations | Select-Object -Unique | ForEach-Object {Bind $_})
    criteria_revisions=$effective.revisions
    matrix=@(foreach($criterion in $effective.rows){@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;scenario=$criterion.criterion;level='Focused dependency amendment, graph and shared admission verification';command='powershell -NoProfile -File scripts/validate_tasks/test-dependency-amendments.ps1; direct readiness/relationship suites';environment='Owned metadata Git fixtures and current repository; no training or external service';expected='Only explicit adopted exact prior/new dependency set resolves, governing Correction remains a prerequisite; invalid records and premature admission reject, old criteria/GPU/gate/rights remain intact'}})
    verification=@()
}
if($Closing){$ready.verification=@('verification-v1.md','result-v1.json','test-output-v1.txt' | ForEach-Object {Bind "$relative/evidence/$_"})}
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness evidence is append-only'}
$ready | ConvertTo-Json -Depth 45 | Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
$action=if($Closing){'close'}else{'execute'}
& "$root/scripts/validate_tasks/admission.ps1" -Root $root -TaskId FDEC-101 -Action $action -ReadinessFile "evidence/$Name"
})
    atomicity=@{outcomes=@('Reconcile MLX dependency with preserved CUDA and Epic acceptance');packets=@('Implement and verify one explicit adopted dependency amendment and shared admission boundaries');independent_acceptance=$false;boundary_reason='One contradictory MLX dependency; no acceptance reduction, rights waiver or device switch'}
    allowed_paths=@('scripts/validate_tasks','Tasks/dependency-amendments','Tasks/policy/dependency-amendment-1.0.md','Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/events','Tasks/epics/FDEC-EPIC-S001/events','docs/training/MACBOOK_M4_HANDOFF.md')
    rule_sources=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json' | ForEach-Object {Bind $_})
    dependency_revisions=@($paths | Select-Object -Unique | ForEach-Object {Bind $_})
    epic_state_evidence=@(foreach($epic in $records.Values){if($epic.epic){foreach($path in $epic.state_paths){Bind $path.Substring($root.Length+1).Replace('\','/')}}})
    migration_revisions=@($migrations | Select-Object -Unique | ForEach-Object {Bind $_})
    criteria_revisions=$effective.revisions
    matrix=@(foreach($criterion in $effective.rows){@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;scenario=$criterion.criterion;level='Focused dependency amendment, graph and shared admission verification';command='powershell -NoProfile -File scripts/validate_tasks/test-dependency-amendments.ps1; direct readiness/relationship suites';environment='Owned metadata Git fixtures and current repository; no training or external service';expected='Only explicit adopted exact prior/new dependency set resolves, governing Correction remains a prerequisite; invalid records and premature admission reject, old criteria/GPU/gate/rights remain intact'}})
    verification=@()
}
if($Closing){$ready.verification=@('verification-v1.md','result-v1.json','test-output-v1.txt' | ForEach-Object {Bind "$relative/evidence/$_"})}
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness evidence is append-only'}
$ready | ConvertTo-Json -Depth 45 | Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
$action=if($Closing){'close'}else{'execute'}
& "$root/scripts/validate_tasks/admission.ps1" -Root $root -TaskId FDEC-101 -Action $action -ReadinessFile "evidence/$Name"
