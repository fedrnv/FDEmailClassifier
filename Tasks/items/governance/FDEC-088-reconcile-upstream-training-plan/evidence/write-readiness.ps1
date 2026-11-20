param([Parameter(Mandatory=$true)][string]$Name,[switch]$Closing)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
$task=Split-Path $PSScriptRoot
$relative=$task.Substring($root.Length+1).Replace('\','/')
. "$root/scripts/validate_tasks/identity.ps1"
. "$root/scripts/validate_tasks/source-state.ps1"
. "$root/scripts/validate_tasks/acceptance-matrix.ps1"
. "$root/scripts/validate_tasks/readiness-events.ps1"
function Bind($path){@{path=$path;sha256=(Get-IdentityHash (Join-Path $root $path))}}
$records=& "$root/scripts/validate_tasks/repository.ps1" -Root $root -AsObject
$effective=Get-EffectiveCriteria $root $task
$rules=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json')
foreach($scope in 'Tasks','scripts/validate_tasks','docs','training/augmentation'){
    $rules+=@(Get-ChildItem (Join-Path $root $scope) -Recurse -File | Where-Object Name -In 'AGENTS.md','DEVELOPMENT.md' | ForEach-Object {$_.FullName.Substring($root.Length+1).Replace('\','/')})
}
$migrationPaths=@(foreach($file in Get-ChildItem "$root/Tasks/migrations" -Filter '*.json'){
    $m=Get-Content $file.FullName -Raw | ConvertFrom-Json
    $file.FullName.Substring($root.Length+1).Replace('\','/')
    $m.retired.path;$m.retained.path;$m.replacement.path;$m.retirement_event.path
    foreach($pair in $m.planning_history){$pair.original.path;$pair.replay.path}
})
$ready=[ordered]@{
    semantic_review='accepted';task_sha256=(Get-IdentityHash "$task/TASK.md");policy_sha256=(Get-Content "$root/Tasks/policy/adoption-5.6.json" -Raw | ConvertFrom-Json).policy_sha256
    source_sha=(git -C $root rev-parse HEAD);source_state_algorithm='fdec-source-state/v1';source_state_sha256=(Get-SourceState $root 'FDEC-088')
    upstream_sha='0ea1e407e32eb2671226ab9f8430e54e4207d6b7'
    atomicity=@{outcomes=@('Integrate the owner plan without losing immutable task identities or acceptance requirements');packets=@('Reconcile pinned plan, exact identity migrations and relationship events with focused local verification');independent_acceptance=$false;boundary_reason='One coherent synchronization cannot be accepted with discarded history, duplicate IDs or invalid dependency/admission behavior'}
    allowed_paths=@('Tasks','scripts/validate_tasks','README.md','docs','training/augmentation')
    rule_sources=@($rules | Select-Object -Unique | ForEach-Object {Bind $_})
    dependency_revisions=@((Bind 'Tasks/epics/FDEC-EPIC-S001/EPIC.md'))
    epic_state_evidence=@(foreach($record in $records.Values){if($record.epic){foreach($path in $record.state_paths){Bind $path.Substring($root.Length+1).Replace('\','/')}}})
    migration_revisions=@($migrationPaths | Select-Object -Unique | ForEach-Object {Bind $_})
    criteria_revisions=$effective.revisions
    matrix=@(foreach($criterion in $effective.rows){@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;scenario=$criterion.criterion;level='Local graph/integrity integration and negative admission tests';command='powershell -NoProfile -File scripts/validate_tasks/test-plan-sync.ps1; powershell -NoProfile -File scripts/validate_tasks/test-identity.ps1; powershell -NoProfile -File scripts/validate_tasks/test-validation.ps1';environment='Windows PowerShell, owned metadata-only Git fixtures and pinned owner plan';expected='Unique effective identities, exact preserved source requirements, correct Mac/optional-Epic dependencies; incomplete or forged migrations explicitly rejected'}})
    verification=@()
}
if($Closing){$ready.verification=@('verification.md','result.json','test-output.txt' | ForEach-Object {Bind "$relative/evidence/$_"})}
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness evidence is append-only'}
$ready | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
$action=if($Closing){'close'}else{'execute'}
& "$root/scripts/validate_tasks/admission.ps1" -Root $root -TaskId FDEC-088 -Action $action -ReadinessFile "evidence/$Name"
