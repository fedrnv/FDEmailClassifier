. "$PSScriptRoot/identity.ps1"
function Criterion-Hash([string]$Text) {
    $sha=[Security.Cryptography.SHA256]::Create()
    try{return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text.Trim())))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
}
function Get-EffectiveCriteria([string]$Root,[string]$TaskDirectory) {
    $criteria=[ordered]@{};$revisions=@();$columns=0
    foreach($line in [IO.File]::ReadAllLines((Join-Path $TaskDirectory 'TASK.md'))) {
        if($line -match '^\|\s*AC ID\s*\|'){$columns=[regex]::Split($line,'(?<!\\)\|').Count;continue}
        if($line -match '^\|\s*(AC-[0-9]{2,})\s*\|'){
            $cells=[regex]::Split($line,'(?<!\\)\|')
            if(!$columns -or $cells.Count -ne $columns){throw 'Malformed task acceptance table'}
            $id=$cells[1].Trim();$criterion=$cells[2].Trim()
            if(!$criterion -or $criteria.Contains($id)){throw 'Ambiguous task acceptance criteria'}
            $criteria[$id]=$criterion
        }
    }
    if(!$criteria.Count){throw 'Task has no acceptance criteria'}
    $eventDirectory=Join-Path $TaskDirectory 'events'
    $events=@()
    if(Test-Path $eventDirectory){$events=@(Get-ChildItem $eventDirectory -Filter '*.md'|ForEach-Object{
        $text=[IO.File]::ReadAllText($_.FullName)
        $front=[regex]::Match($text,'\A(?:\uFEFF)?---\r?\n(.*?)\r?\n---\r?\n','Singleline').Groups[1].Value
        if($front -match '(?m)^event_type: scope-amended\r?$'){[pscustomobject]@{path=$_.FullName;text=$text;front=$front;date=[DateTimeOffset]::Parse([regex]::Match($front,'(?m)^created_at: ([^\r\n]+)').Groups[1].Value)}}
    })}
    $last=$null
    foreach($event in $events|Sort-Object date){
        $file=[regex]::Matches($event.front,'(?m)^acceptance_file: ([^\r\n]+)')
        if(!$file.Count){if($event.text -match '\bAC-[0-9]{2,}\b|\|\s*AC ID\s*\|'){throw 'Unstructured acceptance amendment'};continue}
        if($file.Count -ne 1 -or ($null -ne $last -and $last -eq $event.date)){throw 'Ambiguous acceptance amendment'}
        $last=$event.date
        $hash=[regex]::Matches($event.front,'(?m)^acceptance_sha256: ([a-f0-9]{64})\r?$')
        if($hash.Count -ne 1){throw 'Missing acceptance amendment identity'}
        $path=[IO.Path]::GetFullPath((Join-Path $TaskDirectory $file[0].Groups[1].Value))
        $rootFull=[IO.Path]::GetFullPath($Root).TrimEnd('\','/')
        if(!$path.StartsWith((Join-Path $TaskDirectory 'evidence')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or !(Test-IdentityBinding $Root $path.Substring($rootFull.Length+1) $hash[0].Groups[1].Value)){throw 'Invalid acceptance amendment binding'}
        $amendment=Get-Content $path -Raw|ConvertFrom-Json
        $id=[regex]::Match([IO.File]::ReadAllText((Join-Path $TaskDirectory 'TASK.md')),'(?m)^id: (FDEC-[0-9]{3})\r?$').Groups[1].Value
        if($amendment.schema -ne 'fdec-acceptance-amendment/v1' -or $amendment.task_id -ne $id -or (!$amendment.additions -and !$amendment.updates) -or @($amendment.PSObject.Properties.Name|Where-Object{$_ -notin 'schema','task_id','additions','updates'}).Count){throw 'Unsupported acceptance amendment'}
        $seen=@{}
        foreach($mode in 'additions','updates'){
            foreach($row in $amendment.$mode){
                if(!$row){continue}
                if($row.id -cnotmatch '^AC-[0-9]{2,}$' -or $row.criterion -isnot [string] -or !$row.criterion.Trim() -or $seen.ContainsKey($row.id) -or @($row.PSObject.Properties.Name|Where-Object{$_ -notin 'id','criterion'}).Count){throw 'Invalid amended criterion'}
                $exists=$criteria.Contains($row.id)
                if(($mode -eq 'additions' -and $exists) -or ($mode -eq 'updates' -and !$exists)){throw 'Amendment criterion identity mismatch'}
                $seen[$row.id]=$true;$criteria[$row.id]=$row.criterion.Trim()
            }
        }
        foreach($bound in @($event.path,$path)){$relative=$bound.Substring($rootFull.Length+1).Replace('\','/');$revisions+=@{path=$relative;sha256=(Get-IdentityHash $bound)}}
    }
    $rows=@(foreach($id in $criteria.Keys){[pscustomobject]@{id=$id;criterion=$criteria[$id];criterion_sha256=(Criterion-Hash $criteria[$id])}})
    return @{rows=$rows;revisions=$revisions}
}
function Assert-AcceptanceMatrix([string]$Root,[string]$TaskDirectory,$Ready) {
    $effective=Get-EffectiveCriteria $Root $TaskDirectory
    $seen=@{}
    foreach($row in $Ready.matrix){
        if($row.id -cnotmatch '^AC-[0-9]{2,}$' -or $seen.ContainsKey($row.id)){throw 'Invalid or duplicate AC coverage'}
        $seen[$row.id]=$true
        $criterion=@($effective.rows|Where-Object id -CEQ $row.id)
        if($criterion.Count -ne 1){throw 'Unknown AC coverage'}
        if($row.criterion_sha256 -ne $criterion[0].criterion_sha256){throw 'Stale criterion identity'}
        foreach($field in 'scenario','level','command','environment','expected'){
            if($row.$field -isnot [string] -or !$row.$field.Trim()){throw "Incomplete AC contract: $field"}
        }
    }
    if($seen.Count -ne $effective.rows.Count){throw 'Incomplete AC coverage'}
    foreach($revision in $effective.revisions){
        $bound=@($Ready.criteria_revisions|Where-Object path -EQ $revision.path)
        if($bound.Count -ne 1 -or $bound[0].sha256 -ne $revision.sha256){throw 'Unbound acceptance amendment'}
    }
}
