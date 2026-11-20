$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/source-state.ps1"
. "$PSScriptRoot/readiness-events.ps1"
. "$PSScriptRoot/fixture-matrix.ps1"
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-ready-'+[guid]::NewGuid())
function Bound($path){@{path=$path;sha256=(Get-IdentityHash (Join-Path $temp $path))}}
function Actions($file,[string]$Expected=''){
    foreach($action in 'claim','dispatch','resume','execute','close'){
        $failed=$false
        try{& "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-005 -Action $action -ReadinessFile $file}catch{if($Expected -and $_.Exception.Message -match $Expected){$failed=$true}else{throw}}
        if($Expected -and !$failed){throw "Unaccepted readiness admitted: $action"}
    }
}
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
    $ready=Get-Content "$root/Tasks/items/quality/FDEC-078-bind-readiness-to-accepted-events/evidence/readiness.json" -Raw|ConvertFrom-Json
    $ready.source_sha=git -C $temp rev-parse HEAD
    $ready.task_sha256=(Bound "$task/TASK.md").sha256
    $ready.allowed_paths=@('Tasks')
    $ready.matrix=New-FixtureMatrix $temp $task 'test-readiness-events.ps1 decision scenarios'
    $ready.dependency_revisions=@((Bound "$task/TASK.md"))
    [IO.File]::WriteAllText("$temp/$task/evidence/proof.md",'Synthetic verification')
    $ready.verification=@((Bound "$task/evidence/proof.md"))
    $ready.source_state_sha256=Get-SourceState $temp 'FDEC-005'
    $a="$temp/$task/evidence/a.json"
    $ready|ConvertTo-Json -Depth 12|Set-Content $a -Encoding UTF8
    Actions evidence/a.json 'Missing accepted readiness event'
    Write-ReadinessAcceptance $temp $task evidence/a.json fixture
    Actions evidence/a.json
    Copy-Item $a "$temp/$task/evidence/alternate.json"
    Actions evidence/alternate.json 'not the current accepted decision'
    $bytes=[IO.File]::ReadAllBytes($a)
    [IO.File]::AppendAllText($a,"`n ")
    Actions evidence/a.json 'evidence hash mismatch'
    [IO.File]::WriteAllBytes($a,$bytes)
    Write-ReadinessAcceptance $temp $task evidence/alternate.json fixture
    Actions evidence/a.json 'not the current accepted decision'
    Actions evidence/alternate.json
    # Two decisions with the same greatest timestamp must not depend on filename
    # order. The fixture event is untracked and removed after the negative case.
    $last=@(Read-ReadinessEvents "$temp/$task"|Sort-Object date -Descending)[0]
    $copy=[IO.File]::ReadAllText($last.path)
    $copy=[regex]::Replace($copy,'(?m)^event_id: [^\r\n]+',('event_id: '+[guid]::NewGuid()))
    $ambiguous="$temp/$task/events/fixture-ambiguous.md"
    [IO.File]::WriteAllText($ambiguous,$copy)
    Actions evidence/alternate.json 'Ambiguous accepted readiness events'
    Remove-Item -LiteralPath $ambiguous
    # Legacy prose-only decisions remain history, but cannot authorize new work.
    Write-ReadinessAcceptance $temp $task evidence/alternate.json fixture
    $last=@(Read-ReadinessEvents "$temp/$task"|Sort-Object date -Descending)[0]
    $legacy=[regex]::Replace([IO.File]::ReadAllText($last.path),'(?m)^readiness_(file|sha256): [^\r\n]+\r?\n','')
    [IO.File]::WriteAllText($last.path,$legacy)
    Actions evidence/alternate.json 'missing readiness event field'
    Write-ReadinessAcceptance $temp $task evidence/alternate.json fixture
    Actions evidence/alternate.json
    Write-Output 'PASS: all five actions require exact latest accepted evidence; missing, alternate, changed, superseded, ambiguous and legacy-only decisions reject'
}finally{
    $resolved=[IO.Path]::GetFullPath($temp);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-ready-')){throw 'Unsafe cleanup target'}
    if(Test-Path $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
