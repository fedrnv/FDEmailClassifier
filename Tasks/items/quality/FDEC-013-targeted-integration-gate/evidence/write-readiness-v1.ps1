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
$record=$records['FDEC-013'];$parent=$records[$record.parent]
$paths=@(foreach($id in @($record.dependencies)+@($parent.dependencies)){foreach($path in $records[$id].state_paths){$path.Substring($root.Length+1).Replace('\','/')}})
$migrationPaths=@(foreach($file in Get-ChildItem "$root/Tasks/migrations" -Filter '*.json'){Get-MigrationPaths $root $file.FullName})
$rules=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json')
foreach($scope in 'tests','scripts','docs/verification'){
    if(Test-Path (Join-Path $root $scope)){$rules+=@(Get-ChildItem (Join-Path $root $scope) -Recurse -File | Where-Object Name -In 'AGENTS.md','DEVELOPMENT.md' | ForEach-Object {$_.FullName.Substring($root.Length+1).Replace('\','/')})}
}
$ready=[ordered]@{
    semantic_review='accepted';task_sha256=(Get-IdentityHash "$task/TASK.md");policy_sha256=(Get-Content "$root/Tasks/policy/adoption-5.6.json" -Raw | ConvertFrom-Json).policy_sha256
    source_sha=(git -C $root rev-parse HEAD);source_state_algorithm='fdec-source-state/v1';source_state_sha256=(Get-SourceState $root 'FDEC-013')
    atomicity=@{outcomes=@('Verify D002 changed interfaces and direct interactions on one frozen local candidate');packets=@('Build and run focused offline component and end-to-end integration with source/integrity negative checks');independent_acceptance=$false;boundary_reason='One Epic-specific gate; no data/model rights expansion, training or independent review implementation'}
    allowed_paths=@('tests','scripts','docs/verification')
    rule_sources=@($rules | Select-Object -Unique | ForEach-Object {Bind $_})
    dependency_revisions=@($paths | Select-Object -Unique | ForEach-Object {Bind $_})
    epic_state_evidence=@(foreach($epic in $records.Values){if($epic.epic){foreach($path in $epic.state_paths){Bind $path.Substring($root.Length+1).Replace('\','/')}}})
    migration_revisions=@($migrationPaths | Select-Object -Unique | ForEach-Object {Bind $_})
    criteria_revisions=$effective.revisions
    matrix=@(foreach($criterion in $effective.rows){@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;scenario=$criterion.criterion;level='Frozen local D002 integration and negative boundary';command='powershell -NoProfile -File scripts/verification/D002.ps1 -ExpectedSource <exact frozen commit>';environment='Windows PowerShell, CPython 3.14.5/PyArrow 26.0.1, cached AJV/Rust dependencies; generated software-only fixtures';expected='PASS on exact candidate; wrong/dirty/hidden/untracked source, unapproved data, changed provenance or consent and unsafe outputs reject; no actual training or publication claim'}})
    verification=@()
}
if($Closing){$ready.verification=@('verification-v1.md','result-v1.json','test-output-v1.txt' | ForEach-Object {Bind "$relative/evidence/$_"})}
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness evidence is append-only'}
$ready | ConvertTo-Json -Depth 45 | Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
$action=if($Closing){'close'}else{'execute'}
& "$root/scripts/validate_tasks/admission.ps1" -Root $root -TaskId FDEC-013 -Action $action -ReadinessFile "evidence/$Name"
