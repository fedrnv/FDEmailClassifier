$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/source-state.ps1"
. "$PSScriptRoot/readiness-events.ps1"
. "$PSScriptRoot/fixture-matrix.ps1"
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-matrix-'+[guid]::NewGuid())
function Bound($path){@{path=$path;sha256=(Get-IdentityHash (Join-Path $temp $path))}}
function Check($brief,[string]$Expected=''){
    $file='evidence/matrix-'+[guid]::NewGuid().ToString()+'.json'
    $brief|ConvertTo-Json -Depth 12|Set-Content (Join-Path "$temp/$task" $file) -Encoding UTF8
    Write-ReadinessAcceptance $temp $task $file fixture
    foreach($action in 'claim','dispatch','resume','execute','close'){
        $failed=$false
        try{& "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-005 -Action $action -ReadinessFile $file}catch{if($Expected -and $_.Exception.Message -match $Expected){$failed=$true}else{throw}}
        if($Expected -and !$failed){throw "Invalid matrix admitted: $action"}
    }
}
function Copy-Brief {return $ready|ConvertTo-Json -Depth 12|ConvertFrom-Json}
try{
    New-Item -ItemType Directory $temp|Out-Null
    Copy-Item "$root/Tasks" "$temp/Tasks" -Recurse
    Copy-Item "$root/AGENTS.md","$root/DEVELOPMENT.md" $temp
    $task='Tasks/items/foundation/FDEC-005-architecture-and-backend-adr'
    $owned=[IO.Path]::GetFullPath("$temp/$task/events")
    if(!$owned.StartsWith([IO.Path]::GetFullPath($temp)+[IO.Path]::DirectorySeparatorChar)){throw 'Unsafe fixture reset'}
    Remove-Item -LiteralPath $owned -Recurse -Force
    Remove-Item -LiteralPath "$temp/Tasks/version-requests/FDEC-005.json"
    git -C $temp init --quiet
    git -C $temp add .
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m fixture
    if($LASTEXITCODE -ne 0){throw 'Fixture baseline failed'}
    $ready=Get-Content "$root/Tasks/items/quality/FDEC-079-require-complete-acceptance-matrix/evidence/readiness.json" -Raw|ConvertFrom-Json
    $ready.source_sha=git -C $temp rev-parse HEAD
    $ready.task_sha256=(Bound "$task/TASK.md").sha256
    $ready.allowed_paths=@('Tasks')
    $ready.dependency_revisions=@((Bound "$task/TASK.md"))
    # Bind this copied fixture's current Epic events, not the historical template.
    $ready.epic_state_evidence=@(Get-ChildItem "$temp/Tasks/epics" -Recurse -File|ForEach-Object {Bound $_.FullName.Substring($temp.Length+1).Replace('\','/')})
    [IO.File]::WriteAllText("$temp/$task/evidence/proof.md",'Synthetic verification')
    $ready.verification=@((Bound "$task/evidence/proof.md"))
    $ready.matrix=New-FixtureMatrix $temp $task 'test-acceptance-matrix.ps1 criterion contract cases'
    $ready.source_state_sha256=Get-SourceState $temp 'FDEC-005'
    Check $ready
    $bad=Copy-Brief;$bad.matrix=@($bad.matrix[0]);Check $bad 'Incomplete AC coverage'
    $bad=Copy-Brief;$bad.matrix+=@($bad.matrix[0]);Check $bad 'duplicate AC coverage'
    $bad=Copy-Brief;$bad.matrix[1].id='AC-99';Check $bad 'Unknown AC coverage'
    $bad=Copy-Brief;$bad.matrix[1].criterion_sha256=('0'*64);Check $bad 'Stale criterion identity'
    foreach($field in 'scenario','level','command','environment','expected'){$bad=Copy-Brief;$bad.matrix[1].$field=' ';Check $bad 'Incomplete AC contract'}
    $amendment=@{schema='fdec-acceptance-amendment/v1';task_id='FDEC-005';additions=@(@{id='AC-03';criterion='Synthetic additional boundary criterion'})}
    $amendment|ConvertTo-Json -Depth 5|Set-Content "$temp/$task/evidence/amendment.json" -Encoding UTF8
    $hash=(Bound "$task/evidence/amendment.json").sha256
    $now=(Get-Date).ToUniversalTime();$uid=[guid]::NewGuid().ToString()
    @"
---
schema: fdtasks-event/v3
event_id: $uid
task_id: FDEC-005
event_type: scope-amended
created_at: $($now.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'))
actor: fixture
base_revision: fixture
server_revision: null
acceptance_file: evidence/amendment.json
acceptance_sha256: $hash
---
Add synthetic required criterion through hash-bound scope evidence.
"@|Set-Content "$temp/$task/events/fixture-amendment.md" -Encoding UTF8
    Check $ready 'Incomplete AC coverage'
    $ready.matrix=New-FixtureMatrix $temp $task 'test-acceptance-matrix.ps1 amended criterion cases'
    Check $ready 'Unbound acceptance amendment'
    $effective=Get-EffectiveCriteria $temp "$temp/$task"
    $ready|Add-Member criteria_revisions $effective.revisions -Force
    Check $ready
    Write-Output 'PASS: exact complete base/amended criteria admitted; omitted, duplicate, unknown, stale, incomplete and unbound matrices rejected on all five actions'
}finally{
    $resolved=[IO.Path]::GetFullPath($temp);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-matrix-')){throw 'Unsafe cleanup target'}
    if(Test-Path $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
