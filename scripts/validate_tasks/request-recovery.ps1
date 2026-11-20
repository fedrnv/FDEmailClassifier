# Read-only interpretation of explicitly rejected, unallocated request metadata.
# repository.ps1 loads the common identity/envelope helpers before this module.
function Read-RequestJson([string]$Path) {
    $text=[IO.File]::ReadAllText($Path)
    # ConvertFrom-Json otherwise silently keeps the last identical key on PS5.
    # Scan string tokens before conversion; escaped quotes/braces are content.
    $stack=[Collections.Generic.List[object]]::new()
    for($i=0;$i -lt $text.Length;$i++){
        $char=$text[$i]
        if($char -eq '{'){$stack.Add([Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal));continue}
        if($char -eq '['){$stack.Add($null);continue}
        if($char -eq '}' -or $char -eq ']'){if(!$stack.Count){throw 'Malformed request JSON'};$stack.RemoveAt($stack.Count-1);continue}
        if($char -ne '"'){continue}
        $start=$i;$i++
        while($i -lt $text.Length){
            if($text[$i] -eq '\'){$i+=2;continue}
            if($text[$i] -eq '"'){break}
            $i++
        }
        if($i -ge $text.Length){throw 'Malformed request JSON'}
        $next=$i+1
        while($next -lt $text.Length -and [char]::IsWhiteSpace($text[$next])){$next++}
        if($next -lt $text.Length -and $text[$next] -eq ':'){
            $key=$text.Substring($start,$i-$start+1)|ConvertFrom-Json
            if(!$stack.Count -or $null -eq $stack[$stack.Count-1] -or !$stack[$stack.Count-1].Add($key)){throw 'Duplicate or invalid request JSON key'}
        }
    }
    return $text|ConvertFrom-Json
}
function Request-Git([string]$Root,[string[]]$Arguments) {
    $output=@(& git -C $Root @Arguments)
    if($LASTEXITCODE -ne 0){throw 'Cannot inspect rejected-request history'}
    return $output
}
function Request-ExactKeys($Object,[string[]]$Keys) {
    $actual=@($Object.PSObject.Properties.Name)
    if($actual.Count -ne $Keys.Count -or @(Compare-Object $actual $Keys -CaseSensitive).Count){throw 'Unsupported recovery fields'}
}
function Request-Bound([string]$Root,$Entry) {
    if(!$Entry){throw 'Missing recovery binding'}
    Request-ExactKeys $Entry @('path','sha256')
    if($Entry.path -cnotmatch '^Tasks/[A-Za-z0-9_./-]+$' -or $Entry.path -match '(^|/)\.{1,2}(/|$)' -or !(Test-IdentityBinding $Root $Entry.path $Entry.sha256)){throw 'Invalid recovery artifact binding'}
    return Join-Path $Root $Entry.path
}
function Request-SameSource([string]$Root,[string]$Source,[string]$Path) {
    $blob=@(Request-Git $Root @('rev-parse',"${Source}:$Path"))[0]
    $working=@(Request-Git $Root @('hash-object',"--path=$Path",(Join-Path $Root $Path)))[0]
    if($blob -cne $working){throw 'Rejected request source bytes changed'}
}
function Request-ExpectedType($Record) {
    switch -CaseSensitive (Field $Record.front 'type') {
        'Task' {return 'task_closed'}
        'Bug' {return 'bug_closed'}
        'Correction' {return 'correction_closed'}
        default {throw 'Unsupported recovery work-item kind'}
    }
}
function Get-ResolvedClosureRequests([string]$Root,$Records,$Files,[string]$Head) {
    $rootPath=[IO.Path]::GetFullPath($Root).TrimEnd('\','/')
    $entries=@(foreach($file in $Files){
        @{path=$file.FullName.Substring($rootPath.Length+1).Replace('\','/');file=$file;request=(Read-RequestJson $file.FullName)}
    })
    # Identity checks apply to original requests BEFORE any interpretation.
    if(@($entries|Group-Object {$_.request.request_id}|Where-Object Count -GT 1).Count){throw 'Invalid or duplicate version request'}
    if(@($entries|Group-Object {$_.request.work_item_id}|Where-Object Count -GT 1).Count){throw 'Invalid closed item request'}
    $directory=Join-Path $rootPath 'Tasks/request-recoveries'
    if(!(Test-Path -LiteralPath $directory)){return $entries}
    $recovered=@{}
    foreach($file in Get-ChildItem -LiteralPath $directory -File){
        if($file.Extension -cne '.json'){throw 'Unsupported recovery record file'}
        $r=Read-RequestJson $file.FullName
        Request-ExactKeys $r @('schema','recovery_id','correction_id','request','spec','first_closure','closure_proof','rejection','governing_spec','contract','adoption_event','source_sha','expected_type','reason')
        if($r.schema -cne 'fdec-rejected-request-recovery/v1' -or $r.recovery_id -cnotmatch '^FDEC-[0-9]{3}-R[0-9]{3}$' -or $file.BaseName -cne $r.recovery_id -or !$r.reason){throw 'Invalid recovery identity'}
        $requestPath=Request-Bound $rootPath $r.request
        $matches=@($entries|Where-Object {$_.path -ceq $r.request.path})
        if($matches.Count -ne 1 -or $recovered.ContainsKey($r.request.path)){throw 'Missing or duplicate recovered request'}
        $entry=$matches[0];$original=$entry.request
        if($original.schema -cne 'fdtasks-version-request/v1' -or $original.type -cnotin @('task_closed','bug_closed','correction_closed') -or !$Records.ContainsKey($original.work_item_id)){throw 'Unsupported rejected request'}
        $target=$Records[$original.work_item_id]
        if($target.epic -or $r.request.path -cne "Tasks/version-requests/$($target.id).json"){throw 'Unsupported rejected request target'}
        $expected=Request-ExpectedType $target
        if($original.type -ceq $expected -or $r.expected_type -cne $expected){throw 'Recovery cannot rewrite a valid request or invent its type'}
        $null=Request-Bound $rootPath $r.spec
        if((Join-Path $rootPath $r.spec.path) -cne $target.path){throw 'Recovery specification does not match request'}
        if(!$target.closure_history.Count){throw 'Recovered request has no first closure'}
        $first=$target.closure_history[0]
        $null=Request-Bound $rootPath $r.first_closure
        $null=Request-Bound $rootPath $r.closure_proof
        if((Join-Path $rootPath $r.first_closure.path) -cne $first.path){throw 'Recovery does not bind first closure'}
        $proofPath=[IO.Path]::GetFullPath((Join-Path (Split-Path $target.path) (Field $first.front 'closure_proof')))
        if((Join-Path $rootPath $r.closure_proof.path) -cne $proofPath -or $r.closure_proof.sha256 -cne (Field $first.front 'closure_proof_sha256')){throw 'Recovery does not bind first closure proof'}
        $proof=Get-Content -LiteralPath $proofPath -Raw|ConvertFrom-Json
        if(!(Test-IdentityBinding $rootPath $r.spec.path $proof.task_sha256)){throw 'Recovered closure proof does not match specification'}
        if($r.source_sha -cnotmatch '^[a-f0-9]{40}$'){throw 'Invalid rejected source identity'}
        # Require an actual ancestor commit and unchanged original request/spec/
        # first proof bytes. Hash-object reads working bytes even under Git flags.
        $ancestors=@(Request-Git $rootPath @('rev-list',$Head))
        if($ancestors -cnotcontains $r.source_sha){throw 'Rejected source is not an ancestor'}
        $created=@(Request-Git $rootPath @('log','--reverse','--format=%H','--diff-filter=A','--no-renames',$Head,'--',$r.request.path))
        if($created.Count -ne 1 -or $created[0] -cne $r.source_sha){throw 'Recovery must bind the original request creation commit'}
        foreach($path in @($r.request.path,$r.spec.path,$r.first_closure.path,$r.closure_proof.path)){Request-SameSource $rootPath $r.source_sha $path}
        if(@(Request-Git $rootPath @('ls-tree','-r','--name-only',$r.source_sha,'--','Tasks/version.json','Tasks/VERSION_HISTORY.md')).Count){throw 'Recovery cannot attest an unallocated source with allocated state'}
        $null=Request-Bound $rootPath $r.rejection
        $rejection=Get-Content -LiteralPath (Join-Path $rootPath $r.rejection.path) -Raw|ConvertFrom-Json
        if($rejection.schema -cne 'fdec-local-verification/v1' -or $rejection.result -cne 'FAIL' -or $rejection.exit_code -ne 1 -or $rejection.reason -cne 'Closure request type does not match item' -or $rejection.actual_type -cne $original.type -or $rejection.required_type -cne $expected -or $rejection.correction -cne $r.correction_id -or $rejection.request.path -cne $r.request.path -or $rejection.request.sha256 -cne $r.request.sha256){throw 'Invalid rejected-request evidence'}
        foreach($key in 'allocated','published','acceptance_claimed'){if($rejection.$key -isnot [bool] -or $rejection.$key -ne $false){throw 'Recovery requires explicitly rejected unallocated input'}}
        if(@(Request-Git $rootPath @('rev-parse',"$($rejection.source_sha)^{commit}"))[0] -cne $r.source_sha){throw 'Rejection does not identify original source'}
        if($r.correction_id -ceq $target.id -or !$Records.ContainsKey($r.correction_id)){throw 'Missing independent governing process Correction'}
        $governing=$Records[$r.correction_id]
        $null=Request-Bound $rootPath $r.governing_spec
        if($governing.parent -cne 'FDEC-EPIC-S001' -or (Field $governing.front 'type') -cne 'Correction' -or $governing.status -notin @('InProgress','Done') -or (Join-Path $rootPath $r.governing_spec.path) -cne $governing.path){throw 'Invalid governing process Correction'}
        $null=Request-Bound $rootPath $r.contract
        if($r.contract.path -cne 'Tasks/policy/rejected-request-recovery-1.0.md'){throw 'Unsupported recovery contract'}
        if($r.adoption_event -cnotmatch '^Tasks/epics/FDEC-EPIC-S001/events/[A-Za-z0-9_-]+\.md$' -or $Records['FDEC-EPIC-S001'].state_paths -cnotcontains (Join-Path $rootPath $r.adoption_event)){throw 'Missing recovery adoption event'}
        $adoption=Envelope (Join-Path $rootPath $r.adoption_event)
        $relative=$file.FullName.Substring($rootPath.Length+1).Replace('\','/')
        foreach($pair in @(@('schema','fdtasks-event/v3'),@('task_id','FDEC-EPIC-S001'),@('event_type','scope-amended'),@('correction_id',$r.correction_id),@('recovery_file',$relative),@('recovery_sha256',(Get-IdentityHash $file.FullName)),@('recovery_contract',$r.contract.path),@('recovery_contract_sha256',$r.contract.sha256))){
            if([regex]::Matches($adoption.front,('(?m)^'+[regex]::Escape($pair[0])+': '+[regex]::Escape($pair[1])+'\r?$')).Count -ne 1){throw 'Invalid recovery adoption binding'}
        }
        # Only this locally derived value changes in a detached in-memory copy.
        # Every other field and every subsequent repository/closure check survives.
        $effective=$original|ConvertTo-Json -Depth 30|ConvertFrom-Json
        $effective.type=$expected
        $entry.request=$effective
        $recovered[$r.request.path]=$true
    }
    return $entries
}
