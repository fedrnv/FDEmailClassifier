$ErrorActionPreference='Stop'
$closureRoot=(Resolve-Path "$PSScriptRoot/../../../..").Path
Set-Location $closureRoot
. "$closureRoot/scripts/validate_tasks/identity.ps1"
function Closure-Bind([string]$Path){@{path=$Path;sha256=(Get-IdentityHash (Join-Path $closureRoot $Path))}}
function Closure-State($Paths){@($Paths|ForEach-Object {Closure-Bind $_.Substring($closureRoot.Length+1).Replace('\','/')})}
foreach($file in 'closure-R002.json','closure-audit-R002.json'){if(Test-Path (Join-Path $PSScriptRoot $file)){throw 'Epic proof is append-only'}}
if(Test-Path "$closureRoot/Tasks/version-requests/FDEC-EPIC-D002.json"){throw 'Epic already has a first request'}
$context=& {
    param($directory)
    $records=. "$directory/scripts/validate_tasks/repository.ps1" -Root $directory -AsObject
    . "$directory/scripts/validate_tasks/acceptance-matrix.ps1"
    $now=[DateTimeOffset]::UtcNow;$epic=Epic-Snapshot $records['FDEC-EPIC-D002'] $now
    if($epic.status -cne 'Active' -or $records['FDEC-EPIC-D001'].status -cne 'Done' -or $records['FDEC-100'].status -cne 'Done'){throw 'Epic closure dependencies are not ready'}
    $files=@(Get-ChildItem "$directory/Tasks/version-requests" -Filter '*.json')
    $requests=@(Get-ResolvedClosureRequests $directory $records $files (git -C $directory rev-parse HEAD))
    $members=@();$details=@();$criteria=0
    foreach($id in $epic.members){
        $record=$records[$id];$state=Epic-Snapshot $record $now
        $proof=Epic-TaskProof $directory $record $state
        Assert-AcceptanceMatrix $directory (Split-Path $record.path) $proof
        $request=@($requests|Where-Object {$_.request.work_item_id -ceq $id})
        if($request.Count -ne 1 -or $request[0].request.epic_id -cne 'FDEC-EPIC-D002'){throw 'Missing unique effective member request'}
        $members+=@{id=$id;state=(Closure-State $state.paths)}
        $criteria+=@($proof.matrix).Count
        $details+=@{id=$id;status=$state.status;latest_done=(Closure-Bind $state.done.path.Substring($directory.Length+1).Replace('\','/'));source_sha=$proof.source_sha;criteria_count=@($proof.matrix).Count;verification=$proof.verification;request=(Closure-Bind $request[0].path);effective_request_type=$request[0].request.type}
    }
    $process=Epic-Snapshot $records['FDEC-100'] $now
    $null=Epic-TaskProof $directory $records['FDEC-100'] $process
    @{epic_state=(Closure-State $epic.paths);members=$members;member_details=$details;criteria=$criteria;dependency_state=(Closure-State (Epic-Snapshot $records['FDEC-EPIC-D001'] $now).paths);process_state=(Closure-State $process.paths);source_delta=@(Epic-GitOutput $directory @('diff','--no-renames','--name-status','94f9669920b1ff105f6d29f1e5e98064f10ca583','HEAD'))}
} $closureRoot
if($context.members.Count -ne 8 -or $context.criteria -ne 23 -or @($context.source_delta|Where-Object {$_ -cnotmatch '^A\t'}).Count){throw 'Incomplete membership/criteria or changed historical source'}
$gate=Closure-Bind 'Tasks/items/quality/FDEC-013-targeted-integration-gate/evidence/result-v2.json'
$review=Closure-Bind 'Tasks/epics/FDEC-EPIC-D002/reviews/R002/RESULT.md'
if($gate.sha256 -cne 'b296cd4acf6267a82f829d1e37c09992640435485ccdd993e12112ee3bb0988b' -or $review.sha256 -cne '23df020d138e486e8da8e419f05d600567291713dd17b8fdf6fbd7f62ebb2c64'){throw 'Wrong tested gate or accepted reviewer result'}
$source=git rev-parse HEAD
$audit=[ordered]@{schema='fdec-epic-closure-audit/v1';epic_id='FDEC-EPIC-D002';source_sha=$source;result='PASS: current member proofs and effective matrices verified; pending Epic event/request still require normal closure validation';member_count=8;criteria_count=23;member_details=$context.member_details;dependency_epic_state=$context.dependency_state;process_FDEC100_state=$context.process_state;source_delta=$context.source_delta;gate_result=$gate;review_result=$review;effective_outcome=(Closure-Bind 'Tasks/epics/FDEC-EPIC-D002/evidence/effective-outcome-v1.json');source_continuity=(Closure-Bind 'Tasks/epics/FDEC-EPIC-D002/evidence/outcome-continuity-v1.json');actual_training_data_admitted=$false;actual_training_performed=$false;model_release_approved=$false;allocated=$false;published=$false}
$audit|ConvertTo-Json -Depth 35|Set-Content -LiteralPath "$PSScriptRoot/closure-audit-R002.json" -Encoding UTF8
$relative='Tasks/epics/FDEC-EPIC-D002/evidence'
[ordered]@{schema='fdec-epic-closure/v1';epic_id='FDEC-EPIC-D002';source_sha=$source;candidate_sha='94f9669920b1ff105f6d29f1e5e98064f10ca583';candidate_tree='6b7af50ea1fdbb1a6ad12cdad5dd445cf491560c';policy_sha256=(Get-Content Tasks/policy/adoption-5.6.json -Raw|ConvertFrom-Json).policy_sha256;epic_state=$context.epic_state;members=$context.members;gate_task_id='FDEC-013';review_task_id='FDEC-014';gate_result=$gate;review_result=$review;verification=@('closure-R002.md','closure-audit-R002.json'|ForEach-Object {Closure-Bind "$relative/$_"})}|ConvertTo-Json -Depth 40|Set-Content -LiteralPath "$PSScriptRoot/closure-R002.json" -Encoding UTF8
Write-Output 'PASS: eight Done members, 23 current criteria, all latest proofs, exact passing gate and Accepted R002 bound; validate pending Epic closure before commit'
