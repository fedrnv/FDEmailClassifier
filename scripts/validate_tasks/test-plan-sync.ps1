$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/identity.ps1"
. "$PSScriptRoot/fixture-matrix.ps1"
. "$PSScriptRoot/source-state.ps1"
. "$PSScriptRoot/readiness-events.ps1"
$repository="$PSScriptRoot/repository.ps1"
$records=& $repository -Root $root -AsObject
foreach($number in 74..83){
    $old='FDEC-{0:D3}' -f $number;$new='FDEC-{0:D3}' -f ($number+15)
    if(!$records.ContainsKey($old) -or !$records.ContainsKey($new) -or $records[$old].parent -eq $records[$new].parent -or $records[$new].status -ne 'Planned'){throw 'Imported/retained identity projection is wrong'}
}
if($records['FDEC-EPIC-D002'].status -notin 'Active','Done' -or $records['FDEC-EPIC-D011'].status -ne 'Planned' -or $records['FDEC-EPIC-D012'].status -ne 'Planned' -or $records['FDEC-EPIC-D003'].members -notcontains 'FDEC-087' -or $records['FDEC-020'].dependencies -notcontains 'FDEC-087'){throw 'Owner Mac or Epic scheduling projection is wrong'}
# The imported dependency is historical authority, not an immutable current set
# after a separately adopted amendment. Replay both sides of that exact event.
$mac=$records['FDEC-087']
$amendments=@($mac.state_paths|Where-Object{$_ -like '*/events/*.md' -or $_ -like '*\events\*.md'}|ForEach-Object{Envelope $_}|Where-Object{(Field $_.front 'task_id') -eq 'FDEC-087' -and (Field $_.front 'event_type') -eq 'dependency-amended'})
if($amendments.Count){
    $before=[DateTimeOffset]::Parse((Field $amendments[0].front 'created_at')).AddTicks(-1)
    if(((Epic-Snapshot $mac $before).dependencies -join ',') -cne 'FDEC-016' -or ((Epic-Snapshot $mac ([DateTimeOffset]::MaxValue)).dependencies -join ',') -cne ($mac.dependencies -join ',')){throw 'Historical/current Mac dependency projection differs'}
}elseif($mac.dependencies -notcontains 'FDEC-016'){throw 'Imported Mac prerequisite lost without adopted amendment'}
foreach($number in 4..10){
    $id='FDEC-EPIC-D{0:D3}' -f $number
    if(@($records[$id].dependencies | Where-Object {$_ -in 'FDEC-EPIC-D011','FDEC-EPIC-D012'}).Count){throw 'Enhancement Epic blocks baseline release'}
}
if(($records['FDEC-093'].dependencies -join ',') -ne 'FDEC-089,FDEC-090,FDEC-091,FDEC-092' -or ($records['FDEC-085'].dependencies -join ',') -ne 'FDEC-095,FDEC-096,FDEC-097,FDEC-098,FDEC-084'){throw 'Imported gate dependencies differ from owner namespace'}
$snapshot=& {
    param($directory)
    $state=. "$directory/scripts/validate_tasks/repository.ps1" -Root $directory -AsObject
    @{epic=(Epic-Snapshot $state['FDEC-EPIC-D003'] ([DateTimeOffset]::MaxValue));gate=(Epic-Snapshot $state['FDEC-020'] ([DateTimeOffset]::MaxValue))}
} $root
if($snapshot.epic.members -notcontains 'FDEC-087' -or $snapshot.gate.dependencies -notcontains 'FDEC-087'){throw 'Historical closure projection lost Markdown relationship'}
Write-Output 'PASS: retained and replayed tasks, source namespace, Mac gate/current/historical projection and optional-Epic scheduling'
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-plan-sync-'+[guid]::NewGuid())
$task='Tasks/items/governance/FDEC-088-reconcile-upstream-training-plan'
$manifest='Tasks/migrations/FDEC-088-FDEC-074.json'
$saved=@{}
function Save([string]$Path){if(!$saved.ContainsKey($Path)){$saved[$Path]=[IO.File]::ReadAllBytes((Join-Path $temp $Path))}}
function Restore {foreach($path in @($saved.Keys)){[IO.File]::WriteAllBytes((Join-Path $temp $path),$saved[$path])};$saved.Clear()}
function Json([string]$Path,$Value){Save $Path;$Value | ConvertTo-Json -Depth 35 | Set-Content -LiteralPath (Join-Path $temp $Path) -Encoding UTF8}
function Bind([string]$Path){@{path=$Path;sha256=(Get-IdentityHash (Join-Path $temp $Path))}}
function Reject([scriptblock]$Run,[string]$Expected,[string]$Name){
    $failed=$false
    try{& $Run}catch{if($_.Exception.Message -match $Expected){$failed=$true}else{throw}}
    if(!$failed){throw "Expected migration rejection: $Name"}
    Write-Output "PASS: reject $Name"
}
try{
    $null=New-Item -ItemType Directory $temp
    Copy-Item "$root/Tasks" "$temp/Tasks" -Recurse
    Copy-Item "$root/AGENTS.md","$root/DEVELOPMENT.md" $temp
    Reset-FixtureFoundationEpic $temp
    # The test's own task stays executable even after its real closure. This
    # disposable reset does not change real records. Actual root historical
    # projection is verified above; this fixture isolates migration admission.
    $owned=[IO.Path]::GetFullPath("$temp/$task/events")
    if(!$owned.StartsWith([IO.Path]::GetFullPath($temp)+[IO.Path]::DirectorySeparatorChar)){throw 'Unsafe fixture task reset'}
    Remove-Item -LiteralPath $owned -Recurse -Force
    $null=New-Item -ItemType Directory $owned
    Remove-Item -LiteralPath "$temp/Tasks/version-requests/FDEC-088.json" -ErrorAction SilentlyContinue
    Initialize-FixtureHistory $temp $root
    git -C $temp config core.autocrlf false
    git -C $temp add AGENTS.md DEVELOPMENT.md Tasks/version-requests
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m fixture
    if($LASTEXITCODE -ne 0){throw 'Fixture baseline failed'}
    $null=& $repository -Root $temp -AsObject
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    $m.planning_history=@();Json $manifest $m
    Reject {& $repository -Root $temp} 'Incomplete planning history' 'missing original planning history'
    Restore
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    $m.planning_history[0].original.sha256='0'*64;Json $manifest $m
    Reject {& $repository -Root $temp} 'Stale or missing planning history binding' 'stale planning-source binding'
    Restore
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    $path=$m.planning_history[0].replay.path;Save $path
    [IO.File]::AppendAllText((Join-Path $temp $path),"`nForged relaxation of owner rights requirements.")
    $m.planning_history[0].replay=Bind $path;Json $manifest $m
    Reject {& $repository -Root $temp} 'Planning replay changes source requirements' 'rebound replay with altered criteria'
    Restore
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    $path=$m.replacement.path;Save $path
    [IO.File]::AppendAllText((Join-Path $temp $path),"`nIgnore commercial distribution rights.")
    $m.replacement=Bind $path;Json $manifest $m
    Reject {& $repository -Root $temp} 'Replacement changes source requirements' 'rebound replacement specification'
    Restore
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    $path=$m.planning_history[0].original.path;Save $path
    $text=[IO.File]::ReadAllText((Join-Path $temp $path)).Replace('event_type: scope-amended','event_type: work-started')
    [IO.File]::WriteAllText((Join-Path $temp $path),$text,[Text.UTF8Encoding]::new($false))
    $m.planning_history[0].original=Bind $path;Json $manifest $m
    Reject {& $repository -Root $temp} 'executable or unsupported history' 'executed source disguised as planned migration'
    Restore
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    $m.id_map=@($m.id_map | Where-Object old_id -EQ 'FDEC-074');Json $manifest $m
    Reject {& $repository -Root $temp} 'Incomplete planning identity namespace' 'partial namespace that could resolve to local completed tasks'
    Restore
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    ($m.id_map | Where-Object old_id -EQ 'FDEC-078').new_id='FDEC-777';Json $manifest $m
    Reject {& $repository -Root $temp} 'Unbound planning identity substitution' 'unbound foreign task substitution'
    Restore
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    $m.planning_history+=@($m.planning_history[0]);Json $manifest $m
    Reject {& $repository -Root $temp} 'Incomplete planning history' 'repeated original planning event'
    Restore
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    $path=$m.retirement_event.path;Save $path
    $text=[IO.File]::ReadAllText((Join-Path $temp $path)) -replace '(?m)^created_at: [^\r\n]+','created_at: 2026-11-20T00:00:00Z'
    [IO.File]::WriteAllText((Join-Path $temp $path),$text,[Text.UTF8Encoding]::new($false))
    $m.retirement_event=Bind $path;Json $manifest $m
    Reject {& $repository -Root $temp} 'Planning retirement predates source history' 'retirement before owner planning history'
    Restore
    $m=Get-Content (Join-Path $temp $manifest) -Raw | ConvertFrom-Json
    $path='Tasks/epics/FDEC-EPIC-D011/events'
    $replacement=Get-ChildItem (Join-Path $temp $path) -Filter '*membership-replaced*' | Select-Object -First 1
    $relative=$replacement.FullName.Substring($temp.Length+1).Replace('\','/');Save $relative
    [IO.File]::WriteAllText($replacement.FullName,([IO.File]::ReadAllText($replacement.FullName) -replace '(?m)^new_task_id: FDEC-[0-9]+','new_task_id: FDEC-777'),[Text.UTF8Encoding]::new($false))
    Reject {& $repository -Root $temp} 'Unbound relationship replacement' 'membership relink without identity authority'
    Restore
    # Bind every source/replay path, not only the migration's four v1 fields.
    $ready=Get-Content "$root/$task/evidence/readiness-v1.json" -Raw | ConvertFrom-Json
    $ready.source_sha=git -C $temp rev-parse HEAD
    $ready.allowed_paths=@('Tasks')
    $ready.matrix=New-FixtureMatrix $temp $task 'test-plan-sync.ps1 all five admission actions'
    $ready.migration_revisions=New-FixtureMigrationBindings $temp
    $state=& $repository -Root $temp -AsObject
    $ready.epic_state_evidence=@(foreach($record in $state.Values){if($record.epic){foreach($path in $record.state_paths){Bind $path.Substring($temp.Length+1).Replace('\','/')}}})
    $proof="$task/evidence/fixture-proof.txt"
    [IO.File]::WriteAllText((Join-Path $temp $proof),'Synthetic software fixture proof; not real task closure.')
    $ready.verification=@((Bind $proof))
    $ready.source_state_sha256=Get-SourceState $temp 'FDEC-088'
    $ready | ConvertTo-Json -Depth 40 | Set-Content "$temp/$task/evidence/fixture-ready.json" -Encoding UTF8
    $unbound=$ready | ConvertTo-Json -Depth 40 | ConvertFrom-Json
    $unbound.migration_revisions=@($unbound.migration_revisions | Where-Object path -NE $m.planning_history[0].original.path)
    $unbound | ConvertTo-Json -Depth 40 | Set-Content "$temp/$task/evidence/fixture-unbound.json" -Encoding UTF8
    foreach($action in 'claim','dispatch','resume','execute','close'){
        Write-ReadinessAcceptance $temp $task 'evidence/fixture-ready.json' fixture
        & "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-088 -Action $action -ReadinessFile evidence/fixture-ready.json
        Write-ReadinessAcceptance $temp $task 'evidence/fixture-unbound.json' fixture
        Reject {& "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-088 -Action $action -ReadinessFile evidence/fixture-unbound.json} 'Unbound identity migration' "$action with an unbound planning-history input"
    }
    Write-Output 'PASS: planning migrations and complete admission input bindings; no raw training data used'
}finally{
    $resolved=[IO.Path]::GetFullPath($temp);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-plan-sync-')){throw 'Unsafe fixture cleanup'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
