$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/source-state.ps1"
. "$PSScriptRoot/readiness-events.ps1"
. "$PSScriptRoot/fixture-matrix.ps1"
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-source-'+[guid]::NewGuid())
function Bound($path){@{path=$path;sha256=(Get-IdentityHash (Join-Path $temp $path))}}
function Reject([scriptblock]$Run){$failed=$false;try{& $Run}catch{if($_.Exception.Message -match 'Stale actual source readiness'){$failed=$true}else{throw}};if(!$failed){throw 'Changed source admitted'}}
function Actions($file,[bool]$Invalid=$false){Write-ReadinessAcceptance $temp $task $file fixture;foreach($action in 'claim','dispatch','resume','execute','close'){if($Invalid){Reject {& "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-005 -Action $action -ReadinessFile $file}}else{& "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-005 -Action $action -ReadinessFile $file}}}
try{
    New-Item -ItemType Directory $temp|Out-Null
    Copy-Item "$root/Tasks" "$temp/Tasks" -Recurse
    Copy-Item "$root/AGENTS.md","$root/DEVELOPMENT.md" $temp
    Reset-FixtureFoundationEpic $temp
    $task='Tasks/items/foundation/FDEC-005-architecture-and-backend-adr'
    $owned=[IO.Path]::GetFullPath("$temp/$task/events")
    if(!$owned.StartsWith([IO.Path]::GetFullPath($temp)+[IO.Path]::DirectorySeparatorChar)){throw 'Unsafe fixture reset'}
    Remove-Item -LiteralPath $owned -Recurse -Force
    Remove-Item -LiteralPath "$temp/Tasks/version-requests/FDEC-005.json"
    New-Item -ItemType Directory "$temp/docs/architecture" -Force|Out-Null
    $source="$temp/docs/architecture/source.txt"
    [IO.File]::WriteAllText($source,'original source')
    $code="$temp/docs/architecture/code.rs"
    [IO.File]::WriteAllText($code,"pub const VERSION: u8 = 1;`n")
    Initialize-FixtureHistory $temp $root
    git -C $temp add .
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m fixture
    if($LASTEXITCODE -ne 0){throw 'Fixture baseline failed'}
    $ready=Get-Content "$root/Tasks/items/quality/FDEC-077-bind-readiness-to-actual-source-state/evidence/readiness.json" -Raw|ConvertFrom-Json
    $ready.source_sha=git -C $temp rev-parse HEAD
    $ready.task_sha256=(Bound "$task/TASK.md").sha256
    $ready.allowed_paths=@('Tasks','docs/architecture')
    $ready.matrix=New-FixtureMatrix $temp $task 'test-source-readiness.ps1 source mutation scenarios'
    $ready.dependency_revisions=@((Bound "$task/TASK.md"))
    $ready.migration_revisions=New-FixtureMigrationBindings $temp
    # Bind this copied fixture's current Epic events, not the historical template.
    $ready.epic_state_evidence=@(Get-ChildItem "$temp/Tasks/epics" -Recurse -File|ForEach-Object {Bound $_.FullName.Substring($temp.Length+1).Replace('\','/')})
    $ready|Add-Member source_state_algorithm 'fdec-source-state/v1' -Force
    [IO.File]::WriteAllText("$temp/$task/evidence/source-proof.md",'Synthetic focused proof')
    $ready|Add-Member verification @((Bound "$task/evidence/source-proof.md")) -Force
    $ready|Add-Member source_state_sha256 (Get-SourceState $temp 'FDEC-005') -Force
    $ready|ConvertTo-Json -Depth 12|Set-Content "$temp/$task/evidence/source-ready.json" -Encoding UTF8
    Actions evidence/source-ready.json
    [IO.File]::WriteAllText($code,"pub const VERSION: u8 = 1;`r`n")
    if((Get-SourceState $temp 'FDEC-005') -ne $ready.source_state_sha256){throw 'Checkout EOL alone invalidated source identity'}
    [IO.File]::WriteAllText($source,'changed tracked source')
    Actions evidence/source-ready.json $true
    # Explicitly renewed state allows authorized in-progress work without hiding
    # its bytes or globally ignoring every dirty file.
    $ready.source_state_sha256=Get-SourceState $temp 'FDEC-005'
    $ready|ConvertTo-Json -Depth 12|Set-Content "$temp/$task/evidence/renewed.json" -Encoding UTF8
    Actions evidence/renewed.json
    [IO.File]::WriteAllText($source,'another changed source')
    Actions evidence/renewed.json $true
    [IO.File]::WriteAllText($source,'original source')
    [IO.File]::WriteAllText("$temp/docs/architecture/new.txt",'new untracked source')
    Actions evidence/source-ready.json $true
    Remove-Item -LiteralPath "$temp/docs/architecture/new.txt"
    # A staged source change remains bound even if working bytes are restored.
    [IO.File]::WriteAllText($source,'staged source')
    git -C $temp add docs/architecture/source.txt
    [IO.File]::WriteAllText($source,'original source')
    Actions evidence/source-ready.json $true
    git -C $temp restore --staged docs/architecture/source.txt
    Remove-Item -LiteralPath $source
    Actions evidence/source-ready.json $true
    [IO.File]::WriteAllText($source,'original source')
    [IO.File]::WriteAllText("$temp/$task/evidence/progress.md",'Owned append-only progress')
    New-Item -ItemType Directory "$temp/.idea" -Force|Out-Null
    [IO.File]::WriteAllText("$temp/.idea/workspace.xml",'<synthetic/>')
    Actions evidence/source-ready.json
    [IO.File]::WriteAllText("$temp/.idea/not-ide-source.rs",'pub const OTHER: u8 = 2;')
    Actions evidence/source-ready.json $true
    Write-Output 'PASS: tracked/staged/deleted/new source invalidates all five actions; renewed current state and task-owned progress admitted'
}finally{
    $resolved=[IO.Path]::GetFullPath($temp);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-source-')){throw 'Unsafe cleanup target'}
    if(Test-Path $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
