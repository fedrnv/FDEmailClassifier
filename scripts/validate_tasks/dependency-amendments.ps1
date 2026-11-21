# Explicit adopted prior->new dependency sets; no accepted-spec mutation.
# Loaded after the shared strict JSON/identity helpers and envelope functions.
function Dependency-NoLinks([string]$Root,[string]$Path) {
    $rootFull=[IO.Path]::GetFullPath($Root).TrimEnd('\','/')
    $current=[IO.Path]::GetFullPath($Path)
    if(!$current.StartsWith($rootFull+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Dependency artifact escapes repository'}
    while($current.Length -gt $rootFull.Length){
        if((Test-Path -LiteralPath $current) -and ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked dependency artifact unsupported'}
        $current=Split-Path $current
    }
}
function Dependency-Bound([string]$Root,$Binding) {
    $path=Request-Bound $Root $Binding
    Dependency-NoLinks $Root $path
    return $path
}
function Dependency-Ids($Ids) {
    if($Ids -isnot [array]){throw 'Dependency amendment requires explicit arrays'}
    $seen=@{}
    foreach($id in $Ids){
        if($id -isnot [string] -or $id -cnotmatch '^FDEC-[0-9]{3}$' -or $seen.ContainsKey($id)){throw 'Invalid or duplicate amended dependency'}
        $seen[$id]=$true
    }
    return @($Ids|Sort-Object -CaseSensitive)
}
function Resolve-DependencyAmendment([string]$Root,$Target,$Event,$Used) {
    $relative=Field $Event.front 'dependency_file'
    if($relative -cnotmatch '^Tasks/dependency-amendments/(FDEC-[0-9]{3})-D[0-9]{3}\.json$' -or $matches[1] -cne $Target.id -or $Used.ContainsKey($relative)){throw 'Invalid or duplicate dependency amendment reference'}
    $hash=Field $Event.front 'dependency_sha256'
    $path=Dependency-Bound $Root ([pscustomobject]@{path=$relative;sha256=$hash})
    $change=Read-RequestJson $path
    Request-ExactKeys $change @('schema','target_id','correction_id','source_sha','target_spec','governing_spec','contract','adoption_event','previous_dependencies','new_dependencies','reason')
    if($change.schema -cne 'fdec-dependency-amendment/v1' -or $change.target_id -cne $Target.id -or $Target.epic -or (Field $Target.front 'type') -cne 'Task' -or $Target.status -in 'Done','Cancelled' -or $change.correction_id -cnotmatch '^FDEC-[0-9]{3}$' -or $change.correction_id -ceq $Target.id -or $change.reason -isnot [string] -or !$change.reason.Trim()){throw 'Unsupported dependency amendment target or authority'}
    $null=Dependency-Bound $Root $change.target_spec
    if([IO.Path]::GetFullPath((Join-Path $Root $change.target_spec.path)) -cne $Target.path){throw 'Amended target specification mismatch'}
    if($change.source_sha -cnotmatch '^[a-f0-9]{40}$'){throw 'Invalid dependency source identity'}
    $ancestors=@(Request-Git $Root @('rev-list','HEAD'))
    if($ancestors -cnotcontains $change.source_sha){throw 'Dependency source is not an ancestor'}
    Request-SameSource $Root $change.source_sha $change.target_spec.path
    $prior=@(Dependency-Ids $change.previous_dependencies)
    $next=@(Dependency-Ids $change.new_dependencies)
    if(($prior -join ',') -cne (@($Target.dependencies|Sort-Object -CaseSensitive) -join ',') -or ($prior -join ',') -ceq ($next -join ',') -or $next -ccontains $Target.id -or $next -cnotcontains $change.correction_id){throw 'Stale, empty or self-authorizing dependency amendment'}
    $governing=Dependency-Bound $Root $change.governing_spec
    $governance=Envelope $governing
    if((Field $governance.front 'id') -cne $change.correction_id -or (Field $governance.front 'type') -cne 'Correction' -or (Field $governance.front 'epic_id') -cne 'FDEC-EPIC-S001'){throw 'Dependency amendment requires separate S001 Correction'}
    if($change.contract.path -cne 'Tasks/policy/dependency-amendment-1.0.md'){throw 'Unsupported dependency amendment contract'}
    $null=Dependency-Bound $Root $change.contract
    if($change.adoption_event -isnot [string] -or $change.adoption_event -cnotmatch '^Tasks/epics/FDEC-EPIC-S001/events/[A-Za-z0-9_-]+\.md$'){throw 'Invalid dependency adoption path'}
    Dependency-NoLinks $Root (Join-Path $Root $change.adoption_event)
    $adoption=Envelope (Join-Path $Root $change.adoption_event)
    if((Field $adoption.front 'task_id') -cne 'FDEC-EPIC-S001' -or (Field $adoption.front 'event_type') -cne 'scope-amended' -or (Field $adoption.front 'correction_id') -cne $change.correction_id -or (Field $adoption.front 'dependency_file') -cne $relative -or (Field $adoption.front 'dependency_sha256') -cne $hash -or (Field $adoption.front 'dependency_contract') -cne $change.contract.path -or (Field $adoption.front 'dependency_contract_sha256') -cne $change.contract.sha256){throw 'Missing or changed explicit dependency adoption'}
    $Target.dependencies=@($next)
    $Target.dependency_rule_paths=@($Target.dependency_rule_paths)+@($change.contract.path)
    $bindings=@($path,(Join-Path $Root $change.contract.path),(Join-Path $Root $change.adoption_event),$governing)
    $Target.state_paths+=$bindings
    if(!$Target.ContainsKey('dependency_amendment_nodes')){$Target.dependency_amendment_nodes=@{}}
    $Target.dependency_amendment_nodes[$Event.path]=@{dependencies=@($next);bindings=$bindings}
    $Used[$relative]=[pscustomobject]@{correction_id=$change.correction_id;governing_path=$governing}
}
function Assert-DependencyAmendments([string]$Root,$Records,$Used) {
    $directory=Join-Path $Root 'Tasks/dependency-amendments'
    if(Test-Path -LiteralPath $directory){
        foreach($file in Get-ChildItem -LiteralPath $directory -File){
            $relative='Tasks/dependency-amendments/'+$file.Name
            if($file.Extension -cne '.json' -or !$Used.ContainsKey($relative)){throw 'Unsupported or orphan dependency amendment record'}
        }
    }
    foreach($entry in $Used.Values){
        $governing=$Records[$entry.correction_id]
        if(!$governing -or $governing.path -cne $entry.governing_path -or $governing.parent -cne 'FDEC-EPIC-S001' -or $governing.status -notin 'InProgress','Done' -or $Records['FDEC-EPIC-S001'].status -cne 'Active'){throw 'Inactive dependency amendment governance'}
    }
}
