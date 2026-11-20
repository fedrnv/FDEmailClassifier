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
$record=$records['FDEC-099'];$parent=$records[$record.parent]
$paths=@(foreach($id in @($record.dependencies)+@($parent.dependencies)){foreach($path in $records[$id].state_paths){$path.Substring($root.Length+1).Replace('\','/')}})
$migrations=@(foreach($file in Get-ChildItem "$root/Tasks/migrations" -Filter '*.json'){Get-MigrationPaths $root $file.FullName})
$ready=[ordered]@{
    semantic_review='accepted';task_sha256=(Get-IdentityHash "$task/TASK.md");policy_sha256=(Get-Content "$root/Tasks/policy/adoption-5.6.json" -Raw | ConvertFrom-Json).policy_sha256
    source_sha=(git -C $root rev-parse HEAD);source_state_algorithm='fdec-source-state/v1';source_state_sha256=(Get-SourceState $root 'FDEC-099')
    review_candidate_sha='0bcd4c4f377af86ee8b83d1d0bf770f0eb448ad8';review_candidate_tree='558697de3b18fd1bea8358a144bae90a90231c76'
    review_request=(Bind 'Tasks/epics/FDEC-EPIC-D002/reviews/R001/REQUEST.md')
    gate_result=(Bind 'Tasks/items/quality/FDEC-013-targeted-integration-gate/evidence/result-v1.json')
    atomicity=@{outcomes=@('Explicitly reconcile the authorized D002 outcome and demonstrated evidence');packets=@('Record and verify one append-only outcome reconciliation with retained actual-data gates');independent_acceptance=$false;boundary_reason='One bounded review finding; no source promotion, implementation or normative-policy change'}
    allowed_paths=@('Tasks/epics/FDEC-EPIC-D002/events','Tasks/epics/FDEC-EPIC-D002/evidence','docs/verification')
    rule_sources=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json' | ForEach-Object {Bind $_})
    dependency_revisions=@($paths | Select-Object -Unique | ForEach-Object {Bind $_})
    epic_state_evidence=@(foreach($epic in $records.Values){if($epic.epic){foreach($path in $epic.state_paths){Bind $path.Substring($root.Length+1).Replace('\','/')}}})
    migration_revisions=@($migrations | Select-Object -Unique | ForEach-Object {Bind $_})
    criteria_revisions=$effective.revisions
    matrix=@(foreach($criterion in $effective.rows){@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;scenario=$criterion.criterion;level='Local effective-outcome and authority/proof boundary verification';command='powershell -NoProfile -File docs/verification/verify-d002-outcome.ps1 -TestNegatives';environment='Local pinned repository, owner instructions and existing public metadata; isolated metadata mutations only';expected='Explicit outcome with bound authority and preserved actual-data requirements; missing authority, invalid identities or contradictions reject without mutation'}})
    verification=@()
}
if($Closing){$ready.verification=@('verification-v1.md','result-v1.json','test-output-v1.txt' | ForEach-Object {Bind "$relative/evidence/$_"})}
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness evidence is append-only'}
$ready | ConvertTo-Json -Depth 45 | Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
$action=if($Closing){'close'}else{'execute'}
& "$root/scripts/validate_tasks/admission.ps1" -Root $root -TaskId FDEC-099 -Action $action -ReadinessFile "evidence/$Name"
