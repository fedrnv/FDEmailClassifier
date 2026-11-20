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
$record=$records['FDEC-011'];$parent=$records[$record.parent]
$dependencyPaths=@(foreach($id in @($record.dependencies)+@($parent.dependencies)){foreach($path in $records[$id].state_paths){$path.Substring($root.Length+1).Replace('\','/')}})
$migrationPaths=@(foreach($file in Get-ChildItem "$root/Tasks/migrations" -Filter '*.json'){Get-MigrationPaths $root $file.FullName})
$rules=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json')
foreach($scope in 'training/augmentation','training/config'){
    $rules+=@(Get-ChildItem (Join-Path $root $scope) -Recurse -File | Where-Object Name -In 'AGENTS.md','DEVELOPMENT.md' | ForEach-Object {$_.FullName.Substring($root.Length+1).Replace('\','/')})
}
$ready=[ordered]@{
    semantic_review='accepted';task_sha256=(Get-IdentityHash "$task/TASK.md");policy_sha256=(Get-Content "$root/Tasks/policy/adoption-5.6.json" -Raw | ConvertFrom-Json).policy_sha256
    source_sha=(git -C $root rev-parse HEAD);source_state_algorithm='fdec-source-state/v1';source_state_sha256=(Get-SourceState $root 'FDEC-011')
    atomicity=@{outcomes=@('Verified multilingual generator and independent-source preparation with truthful rights, labels and leakage boundaries');packets=@('Verify fixture-only native software and an exact reviewed Sinabis preparation profile without training or publication');independent_acceptance=$false;boundary_reason='One augmentation/input-provenance outcome under owner amendments; no accepted split-policy change, training run or later task execution'}
    allowed_paths=@('training/augmentation','training/config')
    rule_sources=@($rules | Select-Object -Unique | ForEach-Object {Bind $_})
    dependency_revisions=@($dependencyPaths | Select-Object -Unique | ForEach-Object {Bind $_})
    epic_state_evidence=@(foreach($epic in $records.Values){if($epic.epic){foreach($path in $epic.state_paths){Bind $path.Substring($root.Length+1).Replace('\','/')}}})
    migration_revisions=@($migrationPaths | Select-Object -Unique | ForEach-Object {Bind $_})
    criteria_revisions=$effective.revisions
    matrix=@(foreach($criterion in $effective.rows){@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;scenario=$criterion.criterion;level='Local generator, source-rights/integrity and preparation-boundary verification';command='powershell -NoProfile -File training/augmentation/test-native.ps1; powershell -NoProfile -File training/augmentation/test-sinabis.ps1';environment='Windows CPython 3.14.5/PyArrow 26.0.1, permitted technical fixtures, pinned independent public-source bytes in private storage';expected='PASS with Codex denials, exact reviewed source rights, untrusted canonical mapping, whole-thread/family and duplicate protection; no real training or release claim'}})
    verification=@()
}
if($Closing){$ready.verification=@('verification.md','result.json','test-output.txt' | ForEach-Object {Bind "$relative/evidence/$_"})}
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness evidence is append-only'}
$ready | ConvertTo-Json -Depth 45 | Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
$action=if($Closing){'close'}else{'execute'}
& "$root/scripts/validate_tasks/admission.ps1" -Root $root -TaskId FDEC-011 -Action $action -ReadinessFile "evidence/$Name"
