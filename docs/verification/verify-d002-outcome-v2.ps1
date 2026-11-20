param([switch]$TestNegatives)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$root/scripts/validate_tasks/identity.ps1"
. "$root/scripts/validate_tasks/request-recovery.ps1"
$relative='Tasks/epics/FDEC-EPIC-D002/evidence/outcome-continuity-v1.json'
$originalSource='0bcd4c4f377af86ee8b83d1d0bf770f0eb448ad8'
$historicalSource='16e293aadc15f8dd50fac44720a7949e788c9eff'
$processSource='406e0121fae75e6c0623bf331d11e8e4d8aeccd1'
function Outcome-Git([string[]]$Arguments){$output=@(& git -C $root @Arguments);if($LASTEXITCODE -ne 0){throw 'Cannot inspect outcome continuity source'};return $output}
function Same-OutcomeSet($Actual,$Expected,[string]$Reason){
    $actualValues=@($Actual);$expectedValues=@($Expected)
    if($actualValues.Count -ne $expectedValues.Count -or @($actualValues|Select-Object -Unique).Count -ne $actualValues.Count -or @(Compare-Object $actualValues $expectedValues -CaseSensitive).Count){throw $Reason}
}
function Bound-Outcome($Entry,[string]$Path){if(!$Entry -or $Entry.path -cne $Path -or !(Test-IdentityBinding $root $Path $Entry.sha256)){throw "Invalid continuity binding: $Path"}}
function Same-OutcomeSource([string]$Source,[string]$Path){
    $expected=@(Outcome-Git @('rev-parse',"${Source}:$Path"))[0]
    $actual=@(Outcome-Git @('hash-object',"--path=$Path",(Join-Path $root $Path)))[0]
    if($actual -cne $expected){throw "Outcome source changed: $Path"}
}
$paths=@('M|scripts/validate_tasks/check-adoption.ps1','M|scripts/validate_tasks/fixture-matrix.ps1','M|scripts/validate_tasks/repository.ps1','A|scripts/validate_tasks/request-recovery.ps1','M|scripts/validate_tasks/test-acceptance-matrix.ps1','M|scripts/validate_tasks/test-identity.ps1','M|scripts/validate_tasks/test-plan-sync.ps1','M|scripts/validate_tasks/test-readiness-events.ps1','M|scripts/validate_tasks/test-reopened-requests.ps1','A|scripts/validate_tasks/test-request-recovery.ps1','M|scripts/validate_tasks/test-source-readiness.ps1','M|scripts/validate_tasks/test-validation.ps1')
$actualDelta=@(Outcome-Git @('diff','--no-renames','--name-status',$originalSource,$processSource,'--','training','scripts','schemas','.gitattributes','.gitignore'))
Same-OutcomeSet @($actualDelta|ForEach-Object {$_.Replace("`t",'|')}) $paths 'Unexpected accepted process delta'
$expectedRows=@{}
foreach($line in $actualDelta){
    $status,$path=$line.Split("`t")
    $expectedRows[$path]=@{status=$status;original_blob=$(if($status -eq 'M'){@(Outcome-Git @('rev-parse',"${originalSource}:$path"))[0]}else{$null});accepted_blob=@(Outcome-Git @('rev-parse',"${processSource}:$path"))[0]}
}
$state=& {
    param($directory)
    $records=. "$directory/scripts/validate_tasks/repository.ps1" -Root $directory -AsObject
    $files=@(Get-ChildItem "$directory/Tasks/version-requests" -Filter '*.json')
    @{records=$records;requests=@(Get-ResolvedClosureRequests $directory $records $files (git -C $directory rev-parse HEAD))}
} $root
$process=$state.records['FDEC-100']
if($process.status -cne 'Done' -or $process.parent -cne 'FDEC-EPIC-S001' -or !$process.closure_history.Count){throw 'FDEC-100 must be verified Done'}
$latestDone=$process.closure_history[-1]
$doneRelative=$latestDone.path.Substring($root.Length+1).Replace('\','/')
$proofRelative='Tasks/items/governance/FDEC-100-recover-rejected-closure-request/evidence/closure-readiness-v1.json'
$processProof=Read-RequestJson (Join-Path $root $proofRelative)
if($processProof.source_sha -cne $processSource -or [regex]::Matches($latestDone.front,'(?m)^closure_proof: evidence/closure-readiness-v1.json\r?$').Count -ne 1 -or !(Test-IdentityBinding $root $proofRelative ([regex]::Match($latestDone.front,'(?m)^closure_proof_sha256: ([a-f0-9]{64})\r?$').Groups[1].Value))){throw 'Invalid accepted process closure proof'}
foreach($entry in $processProof.verification){Bound-Outcome $entry $entry.path}
$processResult=Read-RequestJson (Join-Path $root 'Tasks/items/governance/FDEC-100-recover-rejected-closure-request/evidence/result-v1.json')
if($processResult.result -cne 'PASS' -or $processResult.source_sha -cne $processSource -or $processResult.task_id -cne 'FDEC-100'){throw 'Process result does not identify tested source'}
$expectedBindings=@{
    original_outcome='Tasks/epics/FDEC-EPIC-D002/evidence/effective-outcome-v1.json'
    authority='Tasks/epics/FDEC-EPIC-D002/evidence/outcome-authority-v1.md'
    historical_verification='Tasks/items/quality/FDEC-099-reconcile-d002-effective-outcome/evidence/result-v1.json'
    process_spec='Tasks/items/governance/FDEC-100-recover-rejected-closure-request/TASK.md'
    process_done=$doneRelative
    process_proof=$proofRelative
    process_result='Tasks/items/governance/FDEC-100-recover-rejected-closure-request/evidence/result-v1.json'
    request_recovery='Tasks/request-recoveries/FDEC-099-R001.json'
    original_request='Tasks/version-requests/FDEC-099.json'
}
function Assert-Continuity($Value){
    $keys=@('schema','epic_id','correction_id','historical_source','original_source','process_source','allowed_process_changes','actual_data_admitted','source_rights_changed','original_request_rewritten','full_project_objective_preserved','reason')+@($expectedBindings.Keys)
    Same-OutcomeSet @($Value.PSObject.Properties.Name) $keys 'Unsupported continuity fields'
    if($Value.schema -cne 'fdec-outcome-continuity/v1' -or $Value.epic_id -cne 'FDEC-EPIC-D002' -or $Value.correction_id -cne 'FDEC-099'){throw 'Invalid continuity identity'}
    if($Value.historical_source -cne $historicalSource -or $Value.original_source -cne $originalSource -or $Value.process_source -cne $processSource){throw 'Substituted continuity source'}
    if(!$Value.reason -or $Value.full_project_objective_preserved -isnot [bool] -or !$Value.full_project_objective_preserved){throw 'Missing preserved project objective'}
    foreach($key in 'actual_data_admitted','source_rights_changed','original_request_rewritten'){if($Value.$key -isnot [bool] -or $Value.$key -ne $false){throw "Unsupported continuity claim: $key"}}
    foreach($key in $expectedBindings.Keys){Bound-Outcome $Value.$key $expectedBindings[$key]}
    Same-OutcomeSet @($Value.allowed_process_changes|ForEach-Object {"$($_.status)|$($_.path)"}) $paths 'Missing or unsupported process change'
    foreach($entry in $Value.allowed_process_changes){
        Same-OutcomeSet @($entry.PSObject.Properties.Name) @('status','path','original_blob','accepted_blob','sha256') 'Unsupported process-change fields'
        $expected=$expectedRows[$entry.path]
        if($entry.original_blob -cne $expected.original_blob -or $entry.accepted_blob -cne $expected.accepted_blob){throw 'Substituted accepted process blob'}
        Bound-Outcome $entry $entry.path
    }
}
$value=Read-RequestJson (Join-Path $root $relative)
Assert-Continuity $value
$events=@(Get-ChildItem "$root/Tasks/epics/FDEC-EPIC-D002/events" -Filter '*.md'|Where-Object {(Get-Content $_.FullName -Raw) -match '(?m)^continuity_file: evidence/outcome-continuity-v1.json\r?$'})
if($events.Count -ne 1){throw 'Missing or ambiguous continuity adoption'}
$event=Get-Content $events[0].FullName -Raw
foreach($line in @('schema: fdtasks-event/v3','task_id: FDEC-EPIC-D002','event_type: scope-amended','correction_id: FDEC-099',('continuity_sha256: '+(Get-IdentityHash (Join-Path $root $relative))))){if([regex]::Matches($event,('(?m)^'+[regex]::Escape($line)+'\r?$')).Count -ne 1){throw 'Invalid continuity adoption binding'}}
# Historical facts remain bound to their original source; they are not silently
# regenerated or represented as proof of new source/data availability.
$original=Read-RequestJson (Join-Path $root $expectedBindings.original_outcome)
foreach($path in @($expectedBindings.original_outcome,$expectedBindings.authority,'docs/verification/verify-d002-outcome.ps1')){Same-OutcomeSource $historicalSource $path}
foreach($binding in @($original.original_epic,$original.authority)+@($original.downstream_task_specs)+@($original.evidence)){Bound-Outcome $binding $binding.path}
$historical=Read-RequestJson (Join-Path $root $expectedBindings.historical_verification)
if($historical.source_sha -cne $historicalSource -or $historical.result -cne 'PASS'){throw 'Invalid historical software verification'}
foreach($entry in $historical.artifacts){Bound-Outcome $entry $entry.path}
$protected=@(Outcome-Git @('ls-tree','-r','--name-only',$processSource,'--','training','scripts','schemas','.gitattributes','.gitignore'))
$pins=@{}
foreach($line in @(Outcome-Git @('ls-tree','-r',$processSource,'--','training','scripts','schemas','.gitattributes','.gitignore'))){
    if($line -cnotmatch '^(100644|100755) blob ([a-f0-9]{40})\t(.+)$'){throw 'Unsupported protected source tree'}
    $pins[$matches[3]]=@{mode=$matches[1];blob=$matches[2]}
}
function Assert-OutcomeIndex($Entries){
    $seen=@()
    foreach($line in $Entries){
        if($line -cnotmatch '^(100644|100755) ([a-f0-9]{40}) 0\t(.+)$'){throw 'Unsupported protected index entry'}
        $mode=$matches[1];$blob=$matches[2];$path=$matches[3]
        if(!$pins.ContainsKey($path) -or $pins[$path].mode -cne $mode -or $pins[$path].blob -cne $blob){throw 'Protected index source changed'}
        $seen+=@($path)
    }
    Same-OutcomeSet $seen $protected 'Protected index inventory changed'
}
$index=@(Outcome-Git @('ls-files','--stage','--','training','scripts','schemas','.gitattributes','.gitignore'))
Assert-OutcomeIndex $index
$current=@(Outcome-Git @('ls-files','--','training','scripts','schemas','.gitattributes','.gitignore'))
Same-OutcomeSet $current $protected 'Protected source inventory changed'
if(@(Outcome-Git @('ls-files','--others','--exclude-standard','--','training','scripts','schemas')).Count){throw 'Untracked protected source'}
foreach($path in $protected){Same-OutcomeSource $processSource $path}
$resolved=@($state.requests|Where-Object {$_.request.work_item_id -ceq 'FDEC-099'})
if($resolved.Count -ne 1 -or $resolved[0].request.type -cne 'correction_closed' -or (Get-IdentityHash (Join-Path $root $expectedBindings.original_request)) -cne 'fb50e63332b571b04e1ad7635ea013a7d8076ab77913a7de93cdd1ffa740ef0c'){throw 'Original request continuity failed'}
$negatives=0
if($TestNegatives){
    function Reject-Continuity([scriptblock]$Change,[string]$Expected){
        $copy=$value|ConvertTo-Json -Depth 25|ConvertFrom-Json
        & $Change $copy
        try {Assert-Continuity $copy} catch {if($_.Exception.Message -notlike $Expected){throw "Unexpected negative result: $($_.Exception.Message)"};$script:negatives++;return}
        throw 'Invalid continuity accepted'
    }
    Reject-Continuity {$args[0].authority=$null} 'Invalid continuity binding:*'
    Reject-Continuity {$args[0].authority.sha256='0'*64} 'Invalid continuity binding:*'
    Reject-Continuity {$args[0].original_outcome.sha256='0'*64} 'Invalid continuity binding:*'
    Reject-Continuity {$args[0].process_done.sha256='0'*64} 'Invalid continuity binding:*'
    Reject-Continuity {$args[0].process_proof=$null} 'Invalid continuity binding:*'
    Reject-Continuity {$args[0].process_result.sha256='0'*64} 'Invalid continuity binding:*'
    Reject-Continuity {$args[0].request_recovery.sha256='0'*64} 'Invalid continuity binding:*'
    Reject-Continuity {$args[0].historical_verification.sha256='0'*64} 'Invalid continuity binding:*'
    Reject-Continuity {$args[0].schema='unsupported/v2'} 'Invalid continuity identity'
    Reject-Continuity {$args[0].process_source=$originalSource} 'Substituted continuity source'
    Reject-Continuity {$args[0].historical_source=$processSource} 'Substituted continuity source'
    Reject-Continuity {$args[0].actual_data_admitted=$true} 'Unsupported continuity claim:*'
    Reject-Continuity {$args[0].source_rights_changed=$true} 'Unsupported continuity claim:*'
    Reject-Continuity {$args[0].original_request_rewritten=$true} 'Unsupported continuity claim:*'
    Reject-Continuity {$args[0].full_project_objective_preserved=$false} 'Missing preserved project objective'
    Reject-Continuity {$args[0]|Add-Member noteproperty effective_outcome 'Training corpus ready'} 'Unsupported continuity fields'
    Reject-Continuity {$args[0].allowed_process_changes=@($args[0].allowed_process_changes|Select-Object -Skip 1)} 'Missing or unsupported process change'
    Reject-Continuity {$args[0].allowed_process_changes[0].path='training/scripts/ingest_dataset.py'} 'Missing or unsupported process change'
    Reject-Continuity {$args[0].allowed_process_changes[0].accepted_blob='0'*40} 'Substituted accepted process blob'
    Reject-Continuity {$args[0].allowed_process_changes[0].sha256='0'*64} 'Invalid continuity binding:*'
    $badIndex=@($index);$badIndex[0]=$badIndex[0] -replace ' [a-f0-9]{40} 0\t',(' '+('0'*40)+" 0`t")
    try {Assert-OutcomeIndex $badIndex;throw 'Changed index accepted'} catch {if($_.Exception.Message -cne 'Protected index source changed'){throw};$negatives++}
    $badIndex=@($index);$badIndex[0]=$badIndex[0].Replace(" 0`t"," 1`t")
    try {Assert-OutcomeIndex $badIndex;throw 'Unmerged index accepted'} catch {if($_.Exception.Message -cne 'Unsupported protected index entry'){throw};$negatives++}
    try {Assert-OutcomeIndex (@($index)+@($index[0]));throw 'Duplicate index accepted'} catch {if($_.Exception.Message -cne 'Protected index inventory changed'){throw};$negatives++}
}
# Reproduce the original verifier against the real immutable source in an owned
# disposable worktree. No source-root override or code patch is used.
$snapshot=Join-Path ([IO.Path]::GetTempPath()) ('fdec-d002-outcome-'+[guid]::NewGuid())
function Assert-OutcomeSnapshot {
    $absolute=[IO.Path]::GetFullPath($snapshot);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
    if(!$absolute.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $absolute -Leaf).StartsWith('fdec-d002-outcome-') -or $absolute -eq $root){throw 'Unsafe historical worktree target'}
}
$registered=$false
try {
    Assert-OutcomeSnapshot
    $null=Outcome-Git @('-c','core.autocrlf=false','worktree','add','--detach','--',$snapshot,$historicalSource)
    $registered=$true
    $command=Join-Path $snapshot 'docs/verification/verify-d002-outcome.ps1'
    $output=if($TestNegatives){& powershell -NoProfile -File $command -TestNegatives}else{& powershell -NoProfile -File $command}
    if($LASTEXITCODE -ne 0){throw 'Historical outcome verifier failed'}
    $replay=($output -join "`n")|ConvertFrom-Json
    if($replay.result -cne 'PASS' -or $replay.preserved_files -ne 100 -or ($TestNegatives -and $replay.negative_checks -ne 14)){throw 'Invalid historical verifier result'}
} finally {
    if($registered){Assert-OutcomeSnapshot;$null=Outcome-Git @('worktree','remove','--force','--',$snapshot)}
}
if(Test-Path -LiteralPath $snapshot){throw 'Historical outcome worktree cleanup incomplete'}
[ordered]@{schema='fdec-outcome-verification/v2';task_id='FDEC-099';result='PASS';current_protected_files=$protected.Count;accepted_process_changes=$paths.Count;continuity_negative_checks=$negatives;historical_replay_source=$historicalSource;historical_replay=$replay;historical_worktree_removed=(!(Test-Path -LiteralPath $snapshot));original_request_unchanged=$true;actual_data_admitted=$false;independent_review_required=$true}|ConvertTo-Json -Depth 8
