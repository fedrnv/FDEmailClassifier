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
$record=$records['FDEC-014'];$parent=$records[$record.parent]
$paths=@(foreach($id in @($record.dependencies)+@($parent.dependencies)){foreach($path in $records[$id].state_paths){$path.Substring($root.Length+1).Replace('\','/')}})
$migrations=@(foreach($file in Get-ChildItem "$root/Tasks/migrations" -Filter '*.json'){Get-MigrationPaths $root $file.FullName})
$ready=[ordered]@{
    semantic_review='accepted';task_sha256=(Get-IdentityHash "$task/TASK.md");policy_sha256=(Get-Content "$root/Tasks/policy/adoption-5.6.json" -Raw | ConvertFrom-Json).policy_sha256
    source_sha=(git -C $root rev-parse HEAD);source_state_algorithm='fdec-source-state/v1';source_state_sha256=(Get-SourceState $root 'FDEC-014')
    review_candidate_sha='94f9669920b1ff105f6d29f1e5e98064f10ca583';review_candidate_tree='6b7af50ea1fdbb1a6ad12cdad5dd445cf491560c'
    review_request=(Bind 'Tasks/epics/FDEC-EPIC-D002/reviews/R002/REQUEST.md')
    gate_result=(Bind 'Tasks/items/quality/FDEC-013-targeted-integration-gate/evidence/result-v2.json')
    atomicity=@{outcomes=@('Independently review the exact D002 passing candidate and reconcile its evidence');packets=@('Request a separate fresh reviewer, verify focused evidence and record one round decision');independent_acceptance=$false;boundary_reason='One independent acceptance round; no candidate implementation changes, data/model grant or unrelated Epic work'}
    allowed_paths=@('Tasks/epics/FDEC-EPIC-D002/reviews','docs/verification')
    rule_sources=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json' | ForEach-Object {Bind $_})
    dependency_revisions=@($paths | Select-Object -Unique | ForEach-Object {Bind $_})
    epic_state_evidence=@(foreach($epic in $records.Values){if($epic.epic){foreach($path in $epic.state_paths){Bind $path.Substring($root.Length+1).Replace('\','/')}}})
    migration_revisions=@($migrations | Select-Object -Unique | ForEach-Object {Bind $_})
    criteria_revisions=$effective.revisions
    matrix=@(foreach($criterion in $effective.rows){@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;scenario=$criterion.criterion;level='Independent source/evidence acceptance and focused negative verification';command='Fresh independent reviewer follows D002 reviews/R002/REQUEST.md; executor validates exact review/gate bindings and reconciliation';environment='Separate model session without author history; detached exact candidate; approved cached local tooling and synthetic software fixtures';expected='Accepted independent result only if requirements and actual proofs pass; invalid/missing input or unresolved blocker yields ChangesRequired without source mutation or publication'}})
    verification=@()
}
if($Closing){$ready.verification=@('verification-v2.md','reconciliation-v2.json' | ForEach-Object {Bind "$relative/evidence/$_"})}
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness evidence is append-only'}
$ready | ConvertTo-Json -Depth 45 | Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
$action=if($Closing){'close'}else{'execute'}
& "$root/scripts/validate_tasks/admission.ps1" -Root $root -TaskId FDEC-014 -Action $action -ReadinessFile "evidence/$Name"
