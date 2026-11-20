$ErrorActionPreference = 'Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/source-state.ps1"
. "$PSScriptRoot/readiness-events.ps1"
. "$PSScriptRoot/fixture-matrix.ps1"
& "$PSScriptRoot/repository.ps1" -Root $root
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-validation-'+[guid]::NewGuid())
function Reject([scriptblock]$Run,[string]$Expected) {
    $failed=$false
    try { & $Run } catch { if ($_.Exception.Message -match $Expected) { $failed=$true } else { throw } }
    if (!$failed) { throw "Expected rejection: $Expected" }
}
function Bound($path) { @{path=$path;sha256=(Get-FileHash (Join-Path $temp $path) -Algorithm SHA256).Hash.ToLowerInvariant()} }
try {
    New-Item -ItemType Directory $temp | Out-Null
    Copy-Item "$root/Tasks" "$temp/Tasks" -Recurse
    Copy-Item "$root/AGENTS.md","$root/DEVELOPMENT.md" $temp
    Reset-FixtureFoundationEpic $temp
    # Freeze the test fixture's target at its initial Planned state, regardless
    # of later project progress. These are disposable copies, not accepted history.
    $task='Tasks/items/foundation/FDEC-005-architecture-and-backend-adr'
    $ownedEvents=[IO.Path]::GetFullPath("$temp/$task/events")
    if (!$ownedEvents.StartsWith([IO.Path]::GetFullPath($temp)+[IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe fixture reset' }
    if (Test-Path $ownedEvents) { Remove-Item -LiteralPath $ownedEvents -Recurse -Force }
    Remove-Item -LiteralPath "$temp/Tasks/version-requests/FDEC-005.json" -ErrorAction SilentlyContinue
    # The dependency-negative fixture also needs its gate to be nonterminal,
    # independently of the real D001 gate's later completed history.
    $ownedGate=[IO.Path]::GetFullPath("$temp/Tasks/items/quality/FDEC-006-targeted-integration-gate/events")
    if(!$ownedGate.StartsWith([IO.Path]::GetFullPath($temp)+[IO.Path]::DirectorySeparatorChar)){throw 'Unsafe fixture gate reset'}
    if(Test-Path -LiteralPath $ownedGate){
        foreach($file in Get-ChildItem -LiteralPath $ownedGate -Filter '*.md'){
            if([IO.File]::ReadAllText($file.FullName) -match '(?m)^event_type: (?:status-changed|work-started)\r?$'){Remove-Item -LiteralPath $file.FullName}
        }
    }
    Remove-Item -LiteralPath "$temp/Tasks/version-requests/FDEC-006.json" -ErrorAction SilentlyContinue
    git -C $temp init --quiet
    git -C $temp config core.autocrlf false
    git -C $temp add .
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m fixture
    if ($LASTEXITCODE -ne 0) { throw 'Fixture baseline failed' }
    $ready=Get-Content "$root/Tasks/items/foundation/FDEC-004-repository-policy-and-fdtasks-adoption/evidence/readiness.json" -Raw | ConvertFrom-Json
    New-Item -ItemType Directory "$temp/$task/evidence" -Force | Out-Null
    $ready.task_sha256=(Bound "$task/TASK.md").sha256
    $ready.matrix=New-FixtureMatrix $temp $task 'test-validation.ps1 admission scenarios'
    $ready.dependency_revisions=New-FixtureDependencyBindings $temp 'FDEC-005'
    $ready.source_sha=git -C $temp rev-parse HEAD
    $ready.epic_state_evidence=@(Get-ChildItem "$temp/Tasks/epics" -Recurse -File | ForEach-Object { Bound $_.FullName.Substring($temp.Length+1).Replace('\','/') })
    $ready.allowed_paths=@('Tasks')
    $ready.rule_sources+= (Bound 'Tasks/policy/checkout-identities-076.json')
    $ready | Add-Member migration_revisions (New-FixtureMigrationBindings $temp) -Force
    [IO.File]::WriteAllText("$temp/$task/evidence/fixture-proof.md",'Synthetic PASS evidence')
    $ready | Add-Member verification @((Bound "$task/evidence/fixture-proof.md")) -Force
    $ready | Add-Member source_state_algorithm 'fdec-source-state/v1' -Force
    $ready | Add-Member source_state_sha256 (Get-SourceState $temp 'FDEC-005') -Force
    $ready | ConvertTo-Json -Depth 10 | Set-Content "$temp/$task/evidence/fixture-ready.json" -Encoding UTF8
    foreach ($action in 'claim','dispatch','resume','execute','close') {
        Write-ReadinessAcceptance $temp $task 'evidence/fixture-ready.json' fixture
        & "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-005 -Action $action -ReadinessFile evidence/fixture-ready.json
        $saved=$ready.source_sha
        $ready.source_sha='0000000000000000000000000000000000000000'
        $ready | ConvertTo-Json -Depth 10 | Set-Content "$temp/$task/evidence/stale.json" -Encoding UTF8
        Reject { & "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-005 -Action $action -ReadinessFile evidence/stale.json } 'Stale source readiness'
        $ready.source_sha=$saved
    }
    $path="$temp/Tasks/items/foundation/FDEC-002-rust-workspace-bootstrap/TASK.md"
    $original=[IO.File]::ReadAllBytes($path)
    Add-Content $path 'synthetic tamper'
    Reject { & "$PSScriptRoot/repository.ps1" -Root $temp } 'Immutable record changed'
    [IO.File]::WriteAllBytes($path,$original)
    New-Item -ItemType Directory "$temp/.github/workflows" -Force | Out-Null
    [IO.File]::WriteAllText("$temp/.github/workflows/unsafe.yml", "on: push`njobs: { tests: { steps: [{run: cargo test}] } }")
    Reject { & "$PSScriptRoot/repository.ps1" -Root $temp } 'Unreviewed hosted workflow'
    Remove-Item -LiteralPath "$temp/.github/workflows/unsafe.yml"
    $request=Get-Content "$temp/Tasks/version-requests/FDEC-001.json" -Raw
    [IO.File]::WriteAllText("$temp/Tasks/version-requests/duplicate.json",$request)
    Reject { & "$PSScriptRoot/repository.ps1" -Root $temp } 'duplicate version request'
    Remove-Item -LiteralPath "$temp/Tasks/version-requests/duplicate.json"
    # A new scoped rule is not authorized by an older root-only ready decision.
    [IO.File]::WriteAllText("$temp/Tasks/items/AGENTS.md",'# Synthetic scoped rule')
    $scoped=$ready|ConvertTo-Json -Depth 12|ConvertFrom-Json
    $scoped.source_state_sha256=Get-SourceState $temp 'FDEC-005'
    $scoped|ConvertTo-Json -Depth 12|Set-Content "$temp/$task/evidence/fixture-unscoped.json" -Encoding UTF8
    Write-ReadinessAcceptance $temp $task 'evidence/fixture-unscoped.json' fixture
    Reject { & "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-005 -ReadinessFile evidence/fixture-unscoped.json } 'Missing governing rule'
    Remove-Item -LiteralPath "$temp/Tasks/items/AGENTS.md"
    $gate='Tasks/items/quality/FDEC-006-targeted-integration-gate'
    $ready.task_sha256=(Bound "$gate/TASK.md").sha256
    $ready.matrix=New-FixtureMatrix $temp $gate 'test-validation.ps1 unready gate scenario'
    $records=& "$PSScriptRoot/repository.ps1" -Root $temp -AsObject
    $ready.dependency_revisions=@($records.Values | ForEach-Object { $_.state_paths } | ForEach-Object { Bound $_.Substring($temp.Length+1).Replace('\','/') })
    $ready.source_state_sha256=Get-SourceState $temp 'FDEC-006'
    $ready | ConvertTo-Json -Depth 12 | Set-Content "$temp/$gate/evidence/fixture-gate.json" -Encoding UTF8
    Write-ReadinessAcceptance $temp $gate 'evidence/fixture-gate.json' fixture
    Reject { & "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-006 -ReadinessFile evidence/fixture-gate.json } 'Dependency not Done'
    # No immutable input changes are necessary to demonstrate competing Epic state.
    $event=@'
---
schema: fdtasks-event/v3
event_id: fixture-second-active
task_id: FDEC-EPIC-D002
event_type: status-changed
created_at: 2026-11-21T00:00:00Z
actor: fixture
base_revision: fixture
server_revision: null
---
Planned -> Active.
'@
    New-Item -ItemType Directory "$temp/Tasks/epics/FDEC-EPIC-D002/events" -Force | Out-Null
    [IO.File]::WriteAllText("$temp/Tasks/epics/FDEC-EPIC-D002/events/fixture.md",$event)
    Reject { & "$PSScriptRoot/repository.ps1" -Root $temp } 'Multiple active development Epics'
    Remove-Item -LiteralPath "$temp/Tasks/epics/FDEC-EPIC-D002/events/fixture.md"
    & "$PSScriptRoot/repository.ps1" -Root $temp
    Write-Output 'PASS: all action entrypoints, stale source, immutable history, dependency readiness, scoped rules, active Epics, requests and hosted boundary'
} finally {
    $resolved=[IO.Path]::GetFullPath($temp)
    $parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-validation-')) { throw 'Unsafe cleanup target' }
    if (Test-Path $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
