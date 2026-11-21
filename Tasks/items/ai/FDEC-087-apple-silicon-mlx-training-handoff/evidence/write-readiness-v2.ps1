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
$record=$records['FDEC-087'];$parent=$records[$record.parent]
$effective=Get-EffectiveCriteria $root $task
$paths=@(foreach($id in @($record.dependencies)+@($parent.dependencies)){foreach($path in $records[$id].state_paths){$path.Substring($root.Length+1).Replace('\','/')}})
$scopes=@('training/finetune','training/config','training/scripts','docs/training')
$rules=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json')+@($record.dependency_rule_paths)
foreach($scope in $scopes){$rules+=@(Get-ChildItem (Join-Path $root $scope) -Recurse -File|Where-Object Name -In 'AGENTS.md','DEVELOPMENT.md'|ForEach-Object{$_.FullName.Substring($root.Length+1).Replace('\','/')})}
$ready=[ordered]@{
    semantic_review='accepted';task_sha256=(Get-IdentityHash "$task/TASK.md");policy_sha256=(Get-Content "$root/Tasks/policy/adoption-5.6.json" -Raw|ConvertFrom-Json).policy_sha256
    source_sha=(git -C $root rev-parse HEAD);source_state_algorithm='fdec-source-state/v1';source_state_sha256=(Get-SourceState $root 'FDEC-087')
    mlx_runtime_observation=(Bind "$relative/evidence/mlx-runtime-observations-v1.json");mlx_api_supplement=(Bind "$relative/evidence/mlx-api-supplement-v1.json")
    atomicity=@{outcomes=@('Provide a reproducible, operator-confirmed training round trip from the primary development environment to MacBook Air M4 and back, without losing source state or private training artifacts.');packets=@('Implement compatible MLX engine, portable full-state checkpoint and owner-gated private handoff/verified return');independent_acceptance=$false;boundary_reason='One end-to-end training and handoff outcome; no Apple execution or completed real round trip inferred from software simulations'}
    allowed_paths=$scopes
    rule_sources=@($rules|Sort-Object -Unique|ForEach-Object{Bind $_})
    dependency_revisions=@($paths|Sort-Object -Unique|ForEach-Object{Bind $_})
    epic_state_evidence=@(foreach($epic in $records.Values|Where-Object epic){foreach($path in $epic.state_paths){Bind $path.Substring($root.Length+1).Replace('\','/')}})
    migration_revisions=@(foreach($file in Get-ChildItem "$root/Tasks/migrations" -Filter '*.json'){foreach($path in Get-MigrationPaths $root $file.FullName){Bind $path}})
    criteria_revisions=$effective.revisions
    matrix=@(foreach($criterion in $effective.rows){@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;scenario=$criterion.criterion;level='Local backend, full-state checkpoint, source/owner/rights and return boundary checks';command='powershell -NoProfile -File training/finetune/test-mlx-handoff.ps1; existing trainer checks; owner-confirmed Apple numeric smoke/resume when ready';environment='Primary Windows workstation with software-only numerical/protocol fixtures; real MacBook Air M4 only after explicit owner transition';expected='Verify original backend/handoff/return criteria without weakening existing data rights or CUDA obligations. Actual Apple smoke/resume and owner-confirmed verified return remain required; no fake Apple/model/training/license claims from simulations.'}})
    verification=@()
}
if($Closing){$ready.verification=@('verification-v1.md','result-v1.json','test-output-v1.txt'|ForEach-Object{Bind "$relative/evidence/$_"})}
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness is append-only'}
$ready|ConvertTo-Json -Depth 45|Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
$action=if($Closing){'close'}else{'execute'}
& "$root/scripts/validate_tasks/admission.ps1" -Root $root -TaskId FDEC-087 -Action $action -ReadinessFile "evidence/$Name"
