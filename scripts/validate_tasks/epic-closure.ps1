# Mechanical closure provenance; semantic review remains the executor's duty.
# Loaded by repository.ps1, using its Envelope/IdList helpers.
function Epic-GitOutput([string]$Root,[string[]]$Arguments) {
    $output=@(& git -C $Root -c core.quotepath=false @Arguments)
    if($LASTEXITCODE -ne 0){throw "Cannot inspect current Epic source: git $($Arguments -join ' ')"}
    return $output
}
function Epic-CurrentSourcePaths([string]$Root,[string]$GitHead) {
    $index=@(Epic-GitOutput $Root @('ls-files','--stage'))
    foreach($entry in $index){
        if($entry -cnotmatch '^(100644|100755) [a-f0-9]{40} 0\t[^\x00-\x1f"]+$'){throw 'Unsupported or unmerged Epic index entry'}
    }
    # These flags can hide actual working changes from Git diff. This closure
    # envelope does not support sparse/assume-unchanged source checkouts.
    $flags=@(Epic-GitOutput $Root @('ls-files','-v'))
    if(@($flags|Where-Object {$_ -cnotmatch '^H '}).Count){throw 'Unsupported Epic index flags'}
    $staged=@(Epic-GitOutput $Root @('diff','--cached','--no-ext-diff','--no-renames','--name-only',$GitHead))
    $stagedHistory=@(Epic-GitOutput $Root @('diff','--cached','--no-ext-diff','--no-renames','--name-status',$GitHead,'--','Tasks'))
    if(@($stagedHistory|Where-Object {$_ -cnotmatch '^A\t'}).Count){throw 'Immutable candidate ledger changed in index'}
    $working=@(Epic-GitOutput $Root @('diff','--no-ext-diff','--no-renames','--name-only',$GitHead))
    $indexToWorking=@(Epic-GitOutput $Root @('diff','--no-ext-diff','--no-renames','--name-only'))
    # A staged completion file must be the same file whose working bytes were
    # inspected above; a second version in the index is not verified evidence.
    foreach($path in $staged){if($indexToWorking -ccontains $path){throw "Git index differs from current closure evidence: $path"}}
    $other=@(Epic-GitOutput $Root @('ls-files','--others','--exclude-standard'))
    return @($staged)+@($working)+@($other)
}
function Epic-Field([string]$Text,[string]$Key) {
    $fields=[regex]::Matches($Text,"(?m)^$([regex]::Escape($Key)): ([^\r\n]+)")
    if($fields.Count -ne 1){throw "Missing or ambiguous Epic field: $Key"}
    return $fields[0].Groups[1].Value.Trim().Trim('"')
}
function Epic-Snapshot($Record,[DateTimeOffset]$Cutoff,[string]$Exclude='') {
    $snapshot=@{id=$Record.id;status=(Epic-Field $Record.front 'initial_status');members=@();dependencies=@(IdList (Epic-Field $Record.front 'initial_dependencies'));paths=@($Record.path);done=$null}
    if($Record.epic){$snapshot.members=@([regex]::Matches($Record.text,'(?m)^- (FDEC-[0-9]{3})\r?$')|ForEach-Object {$_.Groups[1].Value})}
    $events=@($Record.state_paths|Where-Object {$_ -ne $Record.path -and $_ -ne $Exclude}|ForEach-Object {$e=Envelope $_;$e.date=[DateTimeOffset]::Parse((Epic-Field $e.front 'created_at'));if($e.date -le $Cutoff){$e}})
    foreach($event in $events|Sort-Object {$_['date'].UtcTicks},{if((Epic-Field $_['front'] 'event_type') -eq 'work-started'){0}else{1}},{$_['path']}){
        $snapshot.paths+=$event.path
        $kind=Epic-Field $event.front 'event_type'
        if($kind -in 'status-changed','work-started'){
            $m=[regex]::Match($event.text,'\b(Planned|Active|InProgress|Done|Blocked|Cancelled) -> (Planned|Active|InProgress|Done|Blocked|Cancelled)\b')
            $snapshot.status=$m.Groups[2].Value
            if($snapshot.status -eq 'Done'){$snapshot.done=$event}
        }
        if($kind -in 'membership-added','dependency-added'){
            $id=[regex]::Match($event.text,'(?m)^Add (?:\*{1,2}|`)?(FDEC-[0-9]{3})\b').Groups[1].Value
            $key=if($kind -eq 'membership-added'){'members'}else{'dependencies'};$snapshot[$key]+=$id
        }
        if($kind -in 'membership-replaced','dependency-replaced'){
            $old=Epic-Field $event.front 'old_task_id';$new=Epic-Field $event.front 'new_task_id'
            $key=if($kind -eq 'membership-replaced'){'members'}else{'dependencies'}
            $snapshot[$key]=@($snapshot[$key]|ForEach-Object {if($_ -eq $old){$new}else{$_}})
        }
    }
    return $snapshot
}
function Epic-AssertBindings([string]$Root,$Bindings,$Paths) {
    $expected=@($Paths|ForEach-Object {$_.Substring($Root.Length+1).Replace('\','/')})
    if(@($Bindings).Count -ne $expected.Count){throw 'Incomplete Epic closure state'}
    $seen=@{}
    foreach($entry in $Bindings){
        if(!$entry.path -or $seen.ContainsKey($entry.path) -or $expected -cnotcontains $entry.path -or !(Test-IdentityBinding $Root $entry.path $entry.sha256)){throw 'Invalid Epic closure state binding'}
        $seen[$entry.path]=$true
    }
}
function Epic-ReadBound([string]$Root,$Binding,[string]$Directory) {
    if(!$Binding.path){throw 'Missing Epic closure artifact'}
    $path=[IO.Path]::GetFullPath((Join-Path $Root $Binding.path))
    if(!$path.StartsWith($Directory+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or !(Test-IdentityBinding $Root $Binding.path $Binding.sha256)){throw 'Invalid Epic closure artifact binding'}
    return $path
}
function Epic-TaskProof([string]$Root,$Record,$Snapshot) {
    if($Snapshot.status -ne 'Done' -or !$Snapshot.done){throw 'Epic member is not Done at closure'}
    $directory=Join-Path (Split-Path $Record.path) 'evidence'
    $relative=Epic-Field $Snapshot.done.front 'closure_proof'
    $proofPath=[IO.Path]::GetFullPath((Join-Path (Split-Path $Record.path) $relative))
    $binding=@{path=$proofPath.Substring($Root.Length+1).Replace('\','/');sha256=(Epic-Field $Snapshot.done.front 'closure_proof_sha256')}
    $null=Epic-ReadBound $Root $binding $directory
    $proof=Get-Content $proofPath -Raw|ConvertFrom-Json
    if(!(Test-IdentityBinding $Root $Record.path.Substring($Root.Length+1) $proof.task_sha256) -or !$proof.verification){throw 'Invalid gate/review closure proof'}
    foreach($entry in $proof.verification){$null=Epic-ReadBound $Root $entry $directory}
    return $proof
}
function Assert-EpicClosure([string]$Root,$Records,$Request,[string]$GitHead,[bool]$Accepted,$ItemRequests) {
    $id=$Request.epic_id
    if($id -cnotmatch '^FDEC-EPIC-D[0-9]{3}$' -or $Request.work_item_id -cne $id -or !$Records.ContainsKey($id) -or !$Records[$id].epic -or !$Records[$id].closure_history.Count){throw 'Invalid development Epic closure request'}
    $record=$Records[$id]
    $first=$true
    foreach($closure in $record.closure_history){
        $relative=$closure.path.Substring($Root.Length+1).Replace('\','/')
        $eventAccepted=@(git -C $Root ls-tree --name-only $GitHead -- $relative)
        if($LASTEXITCODE -ne 0){throw 'Cannot resolve Epic closure event baseline'}
        $historical=[bool]$eventAccepted.Count
        if($first -and !$Accepted){$historical=$false}
        Assert-EpicClosureEvent $Root $Records $Request $GitHead $historical $ItemRequests $closure $first
        $first=$false
    }
}
function Assert-EpicClosureEvent([string]$Root,$Records,$Request,[string]$GitHead,[bool]$Accepted,$ItemRequests,$Closure,[bool]$First) {
    $id=$Request.epic_id;$record=$Records[$id]
    $closure=$Closure
    $cutoff=[DateTimeOffset]::Parse((Epic-Field $closure.front 'created_at'))
    $directory=Join-Path (Split-Path $record.path) 'evidence'
    $proofPath=[IO.Path]::GetFullPath((Join-Path (Split-Path $record.path) (Epic-Field $closure.front 'closure_proof')))
    $binding=@{path=$proofPath.Substring($Root.Length+1).Replace('\','/');sha256=(Epic-Field $closure.front 'closure_proof_sha256')}
    $null=Epic-ReadBound $Root $binding $directory
    $proof=Get-Content $proofPath -Raw|ConvertFrom-Json
    if($proof.schema -ne 'fdec-epic-closure/v1' -or $proof.epic_id -cne $id -or $proof.source_sha -cnotmatch '^[a-f0-9]{40}$' -or $proof.candidate_sha -cnotmatch '^[a-f0-9]{40}$' -or $proof.candidate_tree -cnotmatch '^[a-f0-9]{40}$'){throw 'Invalid Epic closure proof'}
    if(!$Accepted -and $proof.source_sha -ne $GitHead){throw 'Stale Epic closure source'}
    $snapshot=Epic-Snapshot $record $cutoff $closure.path
    Epic-AssertBindings $Root $proof.epic_state $snapshot.paths
    if(!$snapshot.members.Count -or @($snapshot.members|Select-Object -Unique).Count -ne $snapshot.members.Count -or @($proof.members).Count -ne $snapshot.members.Count){throw 'Incomplete Epic closure membership'}
    $states=@{};$seen=@{}
    foreach($member in $proof.members){
        if(!$member.id -or $seen.ContainsKey($member.id) -or $snapshot.members -cnotcontains $member.id){throw 'Invalid Epic closure member'}
        $seen[$member.id]=$true;$state=Epic-Snapshot $Records[$member.id] $cutoff
        if($state.status -ne 'Done'){throw 'Epic member is not Done at closure'}
        if(@($ItemRequests|Where-Object {$_.work_item_id -ceq $member.id -and $_.epic_id -ceq $id -and $_.type -in 'task_closed','bug_closed','correction_closed'}).Count -ne 1){throw 'Epic member lacks its first-closure request'}
        Epic-AssertBindings $Root $member.state $state.paths
        $states[$member.id]=$state
    }
    foreach($dependency in $snapshot.dependencies){if((Epic-Snapshot $Records[$dependency] $cutoff).status -ne 'Done'){throw 'Epic dependency is not Done at closure'}}
    $gate=$proof.gate_task_id;$review=$proof.review_task_id
    if(!$gate -or !$review -or $gate -eq $review -or !$states.ContainsKey($gate) -or !$states.ContainsKey($review) -or $states[$review].dependencies -notcontains $gate -or $states[$gate].dependencies -contains $review){throw 'Invalid Epic gate/review topology'}
    foreach($member in $snapshot.members|Where-Object {$_ -notin $gate,$review}){if($states[$gate].dependencies -notcontains $member){throw 'Gate does not depend on complete Epic implementation'}}
    foreach($dependency in @($states[$gate].dependencies)+@($states[$review].dependencies)){if((Epic-Snapshot $Records[$dependency] $cutoff).status -ne 'Done'){throw 'Gate/review dependency is not Done at closure'}}
    $gateProof=Epic-TaskProof $Root $Records[$gate] $states[$gate]
    $reviewProof=Epic-TaskProof $Root $Records[$review] $states[$review]
    if($gateProof.source_sha -cne $proof.candidate_sha -or $states[$gate].done.date -gt $states[$review].done.date){throw 'Gate/review source or order mismatch'}
    $gateDirectory=Join-Path (Split-Path $Records[$gate].path) 'evidence'
    $gatePath=Epic-ReadBound $Root $proof.gate_result $gateDirectory
    if(@($gateProof.verification|Where-Object {$_.path -ceq $proof.gate_result.path -and $_.sha256 -eq $proof.gate_result.sha256}).Count -ne 1){throw 'Gate result is not the latest Done evidence'}
    $gateResult=Get-Content $gatePath -Raw|ConvertFrom-Json
    $pin=Get-Content "$Root/Tasks/policy/adoption-5.6.json" -Raw|ConvertFrom-Json
    if($gateResult.schema -ne 'fdec-gate-result/v1' -or $gateResult.task_id -cne $gate -or $gateResult.epic_id -cne $id -or $gateResult.result -ne 'PASS' -or $gateResult.exit_code -ne 0 -or $null -eq $gateResult.exit_code -or $gateResult.candidate_sha -cne $proof.candidate_sha -or $gateResult.candidate_tree -cne $proof.candidate_tree -or $gateResult.policy_sha256 -cne $proof.policy_sha256 -or $proof.policy_sha256 -cne $pin.policy_sha256 -or !(Test-IdentityBinding $Root 'Tasks/policy/upstream-5.6.md' $proof.policy_sha256)){throw 'Invalid or mismatched passing gate'}
    $reviewDirectory=Join-Path (Split-Path $record.path) 'reviews'
    $reviewPath=Epic-ReadBound $Root $proof.review_result $reviewDirectory
    $reviewRelative=$reviewPath.Substring($Root.Length+1).Replace('\','/')
    $prefix=$reviewDirectory.Substring($Root.Length+1).Replace('\','/')
    $paths=if($Accepted){@(git -C $Root ls-tree -r --name-only $proof.source_sha -- $prefix)}else{@(Get-ChildItem $reviewDirectory -Recurse -File|ForEach-Object {$_.FullName.Substring($Root.Length+1).Replace('\','/')})}
    $rounds=@($paths|Where-Object {$_ -cmatch ('^'+[regex]::Escape($prefix)+'/R[0-9]{3,}/REQUEST\.md$')}|Sort-Object {[int]([regex]::Match($_,'/R([0-9]+)/REQUEST\.md$').Groups[1].Value)})
    if(!$rounds.Count -or $reviewRelative -cne $rounds[-1].Replace('/REQUEST.md','/RESULT.md')){throw 'Review is not the latest requested round'}
    $result=Envelope $reviewPath;$reviewRequest=Envelope (Join-Path (Split-Path $reviewPath) 'REQUEST.md')
    if((Epic-Field $result.front 'schema') -cne 'fdec-independent-review-result/v1' -or (Epic-Field $reviewRequest.front 'schema') -cne 'fdec-independent-review-request/v1'){throw 'Invalid independent review schema'}
    $null=Epic-Field $result.front 'reviewer'
    foreach($front in @($result.front,$reviewRequest.front)){
        foreach($pair in @(@('review_task_id',$review),@('epic_id',$id),@('candidate_sha',$proof.candidate_sha),@('candidate_tree',$proof.candidate_tree),@('policy_sha256',$proof.policy_sha256),@('gate_result_sha256',$proof.gate_result.sha256))){if((Epic-Field $front $pair[0]) -cne $pair[1]){throw 'Mismatched independent review identity'}}
    }
    if((Epic-Field $result.front 'result') -cne 'Accepted' -or (Epic-Field $result.front 'review_id') -cne (Epic-Field $reviewRequest.front 'review_id')){throw 'Independent review is not Accepted'}
    $bound=$false
    foreach($entry in $reviewProof.verification){
        $artifact=Get-Content (Join-Path $Root $entry.path) -Raw
        if($entry.path.EndsWith('.json')){
            $reconciliation=$artifact|ConvertFrom-Json
            if($reconciliation.schema -eq 'fdec-review-reconciliation/v1' -and $reconciliation.task_id -ceq $review -and $reconciliation.result -ceq 'Accepted' -and $reconciliation.candidate_sha -ceq $proof.candidate_sha -and @($reconciliation.artifacts|Where-Object {$_.path -ceq $proof.review_result.path -and $_.sha256 -eq $proof.review_result.sha256}).Count -eq 1){$bound=$true}
        }
    }
    if(!$bound){throw 'Review result is not the latest Done evidence'}
    $tree=git -C $Root rev-parse "$($proof.candidate_sha)^{tree}"
    if($LASTEXITCODE -ne 0 -or $tree -cne $proof.candidate_tree){throw 'Candidate tree mismatch'}
    git -C $Root merge-base --is-ancestor $proof.candidate_sha $proof.source_sha
    if($LASTEXITCODE -ne 0){throw 'Closure source does not descend from candidate'}
    # Never let rename/copy detection hide removal of an implementation path
    # behind an allowed completion destination. Inspect both sides independently.
    $changed=@(Epic-GitOutput $Root @('diff','--no-ext-diff','--no-renames','--name-only',$proof.candidate_sha,$proof.source_sha))
    $history=@(Epic-GitOutput $Root @('diff','--no-ext-diff','--no-renames','--name-status',$proof.candidate_sha,$proof.source_sha,'--','Tasks'))
    if(@($history|Where-Object {$_ -cnotmatch '^A\t'}).Count){throw 'Immutable candidate ledger changed'}
    if(!$Accepted){$changed+=@(Epic-CurrentSourcePaths $Root $GitHead)}
    $memberPattern=(@($snapshot.members|ForEach-Object {[regex]::Escape($_)}) -join '|')
    foreach($path in $changed){
        if(!$Accepted -and $path -match '^\.idea/(workspace\.xml|vcs\.xml|modules\.xml|misc\.xml|\.gitignore|[^/]+\.iml|inspectionProfiles/[^/]+\.xml)$'){
            $tracked=@(Epic-GitOutput $Root @('ls-files','--',$path))
            if(!$tracked.Count){continue}
        }
        if($path -cmatch ('^Tasks/items/[^/]+/('+$memberPattern+')-[^/]+/(events|evidence)/') -or $path -cmatch ('^Tasks/version-requests/('+$memberPattern+'|'+[regex]::Escape($id)+')\.json$') -or $path -cmatch ('^Tasks/epics/'+[regex]::Escape($id)+'/(events|evidence|reviews)/')){continue}
        throw "Implementation differs from passing candidate: $path"
    }
    if(!$proof.verification){throw 'Missing Epic verification'}
    foreach($entry in $proof.verification){$null=Epic-ReadBound $Root $entry $directory}
    foreach($path in $(if($First){$Request.verification}else{@()})){
        $entries=@($proof.verification|Where-Object path -CEQ $path)
        if($entries.Count -ne 1){throw 'Unverified Epic closure evidence'}
        $null=Epic-ReadBound $Root $entries[0] $directory
    }
}
