# Versioned planning-only identity replay. Accepted v1 migrations remain strict.
. "$PSScriptRoot/identity.ps1"
function Get-MigrationPaths([string]$Root,[string]$Manifest) {
    $rootFull=[IO.Path]::GetFullPath($Root).TrimEnd('\','/')
    $file=[IO.Path]::GetFullPath($Manifest)
    if(!$file.StartsWith($rootFull+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Migration escapes repository'}
    $migration=Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
    $paths=@($file.Substring($rootFull.Length+1).Replace('\','/'),$migration.retired.path,$migration.retained.path,$migration.replacement.path,$migration.retirement_event.path)
    if($migration.schema -eq 'fdec-identity-resolution/v2'){
        foreach($pair in $migration.planning_history){$paths+=@($pair.original.path,$pair.replay.path)}
    } elseif($migration.schema -ne 'fdec-identity-resolution/v1'){throw 'Unsupported identity migration'}
    return @($paths | Select-Object -Unique)
}
function Convert-PlanningIdentity([string]$Text,$Map) {
    $lookup=@{}
    foreach($pair in $Map){$lookup[$pair.old_id]=$pair.new_id}
    return [regex]::Replace($Text.Replace("`r`n","`n"),'\bFDEC-[0-9]{3}\b',{
        param($match)
        if($lookup.ContainsKey($match.Value)){$lookup[$match.Value]}else{$match.Value}
    })
}
function Assert-PlanningMigration([string]$Root,$Resolution,$Old,$New,$Retirement) {
    $keys=@('schema','correction_id','retired','retained','replacement','retirement_event','source_revision','id_map','planning_history')
    if(@($Resolution.PSObject.Properties.Name | Where-Object {$_ -notin $keys}).Count -or @($keys | Where-Object {$Resolution.PSObject.Properties.Name -notcontains $_}).Count -or $Resolution.source_revision -cnotmatch '^[a-f0-9]{40}$' -or $Resolution.id_map -isnot [array] -or !$Resolution.id_map.Count -or $Resolution.planning_history -isnot [array]){throw 'Invalid planning migration envelope'}
    $seenOld=@{};$seenNew=@{}
    foreach($pair in $Resolution.id_map){
        if(@($pair.PSObject.Properties.Name | Sort-Object) -join ',' -ne 'new_id,old_id' -or $pair.old_id -cnotmatch '^FDEC-[0-9]{3}$' -or $pair.new_id -cnotmatch '^FDEC-[0-9]{3}$' -or $pair.old_id -eq $pair.new_id -or $seenOld.ContainsKey($pair.old_id) -or $seenNew.ContainsKey($pair.new_id)){throw 'Invalid planning identity map'}
        $seenOld[$pair.old_id]=$true;$seenNew[$pair.new_id]=$true
    }
    if(@($seenOld.Keys | Where-Object {$seenNew.ContainsKey($_)}).Count){throw 'Chained planning identity map forbidden'}
    $oldId=Field $Old.front 'id';$newId=Field $New.front 'id'
    if(@($Resolution.id_map | Where-Object {$_.old_id -eq $oldId -and $_.new_id -eq $newId}).Count -ne 1 -or (Field $Old.front 'schema') -ne 'fdtasks-spec/v3' -or !(Split-Path (Split-Path $Old.path) -Leaf).StartsWith($oldId)){throw 'Invalid planning source identity'}
    if((Convert-PlanningIdentity $Old.text $Resolution.id_map) -cne $New.text.Replace("`r`n","`n")){throw 'Replacement changes source requirements'}
    $historyDirectory=Join-Path (Split-Path $Old.path) 'events'
    $history=@(Get-ChildItem -LiteralPath $historyDirectory -Filter '*.md' | Where-Object {$_.FullName -ne $Retirement.path})
    if($history.Count -ne $Resolution.planning_history.Count){throw 'Incomplete planning history'}
    $seen=@{};$ids=@{}
    foreach($pair in $Resolution.planning_history){
        if(@($pair.PSObject.Properties.Name | Sort-Object) -join ',' -ne 'original,replay'){throw 'Invalid planning history pair'}
        foreach($binding in @($pair.original,$pair.replay)){
            if(@($binding.PSObject.Properties.Name | Sort-Object) -join ',' -ne 'path,sha256' -or !(Test-IdentityBinding $Root $binding.path $binding.sha256)){throw 'Stale or missing planning history binding'}
        }
        $originalPath=[IO.Path]::GetFullPath((Join-Path $Root $pair.original.path))
        $replayPath=[IO.Path]::GetFullPath((Join-Path $Root $pair.replay.path))
        if($history.FullName -notcontains $originalPath -or (Split-Path $replayPath) -ne (Join-Path (Split-Path $New.path) 'events') -or $seen.ContainsKey($originalPath)){throw 'Planning history escapes task or repeats'}
        $seen[$originalPath]=$true
        $original=Envelope $originalPath;$replay=Envelope $replayPath
        $eventId=Field $original.front 'event_id'
        if((Field $original.front 'schema') -ne 'fdtasks-event/v3' -or (Field $original.front 'task_id') -ne $oldId -or (Field $original.front 'event_type') -ne 'scope-amended' -or $ids.ContainsKey($eventId) -or $original.front -match '(?m)^acceptance_file:'){throw 'Retired planning source has executable or unsupported history'}
        $null=Field $original.front 'actor';$null=Field $original.front 'base_revision'
        $ids[$eventId]=$true
        if([DateTimeOffset]::Parse((Field $original.front 'created_at')) -ge [DateTimeOffset]::Parse((Field $Retirement.front 'created_at'))){throw 'Planning retirement predates source history'}
        $expected=Convert-PlanningIdentity $original.text $Resolution.id_map
        $mappedId=Convert-PlanningIdentity $eventId $Resolution.id_map
        $expected=$expected.Replace("event_id: $mappedId", "event_id: $mappedId-reidentified-$newId")
        if($expected -cne $replay.text.Replace("`r`n","`n")){throw 'Planning replay changes source requirements'}
    }
}
