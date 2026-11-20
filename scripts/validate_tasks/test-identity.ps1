$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/source-state.ps1"
. "$PSScriptRoot/readiness-events.ps1"
$records=& "$PSScriptRoot/repository.ps1" -Root $root -AsObject
if ($records['FDEC-073'].parent -ne 'FDEC-EPIC-S001' -or $records['FDEC-073'].status -ne 'Done' -or $records['FDEC-075'].parent -ne 'FDEC-EPIC-D009' -or $records['FDEC-075'].status -ne 'Planned' -or $records['FDEC-063'].dependencies -notcontains 'FDEC-075' -or $records['FDEC-063'].dependencies -contains 'FDEC-073') { throw 'Identity projection differs from accepted migration' }
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-identity-'+[guid]::NewGuid())
function Reject([scriptblock]$Run,[string]$Expected) {
    $rejected=$false
    try { & $Run } catch { if ($_.Exception.Message -match $Expected) {$rejected=$true} else {throw} }
    if (!$rejected) { throw "Expected rejection: $Expected" }
}
function Bound($path) {@{path=$path;sha256=(Get-FileHash (Join-Path $temp $path) -Algorithm SHA256).Hash.ToLowerInvariant()}}
try {
    New-Item -ItemType Directory $temp | Out-Null
    Copy-Item "$root/Tasks" "$temp/Tasks" -Recurse
    Copy-Item "$root/AGENTS.md","$root/DEVELOPMENT.md" $temp
    $target='Tasks/items/governance/FDEC-072-polish-public-github-repository-presentation'
    # Keep this disposable target nonterminal even after real FDEC-072 closure.
    $ownedEvents=[IO.Path]::GetFullPath("$temp/$target/events")
    if (!$ownedEvents.StartsWith([IO.Path]::GetFullPath($temp)+[IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe fixture reset' }
    if (Test-Path $ownedEvents) { Remove-Item -LiteralPath $ownedEvents -Recurse -Force }
    New-Item -ItemType Directory $ownedEvents | Out-Null
    @'
---
schema: fdtasks-event/v3
event_id: identity-fixture-blocked
task_id: FDEC-072
event_type: status-changed
created_at: 2026-11-20T00:00:00Z
actor: fixture
base_revision: fixture
server_revision: null
---
Planned -> Blocked.
'@ | Set-Content "$ownedEvents/fixture.md" -Encoding UTF8
    Remove-Item -LiteralPath "$temp/Tasks/version-requests/FDEC-072.json" -ErrorAction SilentlyContinue
    # Synthetic candidate files remain untracked here to exercise semantic hash
    # rejection separately from the immutable-history tests in test-validation.
    git -C $temp init --quiet
    git -C $temp add AGENTS.md DEVELOPMENT.md Tasks/version-requests
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m fixture
    if ($LASTEXITCODE -ne 0) { throw 'Fixture initialization failed' }
    $ready=Get-Content "$temp/$target/evidence/readiness.json" -Raw | ConvertFrom-Json
    $ready.source_sha=git -C $temp rev-parse HEAD
    $ready.epic_state_evidence=@(Get-ChildItem "$temp/Tasks/epics" -Recurse -File | ForEach-Object {Bound $_.FullName.Substring($temp.Length+1).Replace('\','/')})
    $ready.allowed_paths=@('Tasks')
    $ready.rule_sources+= (Bound 'Tasks/policy/checkout-identities-076.json')
    $migration=Get-Content "$temp/Tasks/migrations/FDEC-074.json" -Raw | ConvertFrom-Json
    $ready | Add-Member migration_revisions @(@('Tasks/migrations/FDEC-074.json',$migration.retired.path,$migration.retained.path,$migration.replacement.path,$migration.retirement_event.path) | ForEach-Object {Bound $_}) -Force
    $ready | Add-Member verification @((Bound "$target/evidence/github-preview-verified.md")) -Force
    $ready | Add-Member source_state_algorithm 'fdec-source-state/v1' -Force
    $ready | Add-Member source_state_sha256 (Get-SourceState $temp 'FDEC-072') -Force
    $ready | ConvertTo-Json -Depth 12 | Set-Content "$temp/$target/evidence/fixture-ready.json" -Encoding UTF8
    $unbound=$ready | ConvertTo-Json -Depth 12 | ConvertFrom-Json
    $unbound.migration_revisions=@()
    $unbound | ConvertTo-Json -Depth 12 | Set-Content "$temp/$target/evidence/fixture-unbound.json" -Encoding UTF8
    foreach ($action in 'claim','dispatch','resume','execute','close') {
        Write-ReadinessAcceptance $temp $target 'evidence/fixture-ready.json' fixture
        & "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-072 -Action $action -ReadinessFile evidence/fixture-ready.json
        Write-ReadinessAcceptance $temp $target 'evidence/fixture-unbound.json' fixture
        Reject { & "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-072 -Action $action -ReadinessFile evidence/fixture-unbound.json } 'Unbound identity migration'
    }
    $manifest="$temp/Tasks/migrations/FDEC-074.json"
    $saved=[IO.File]::ReadAllBytes($manifest)
    $migration=Get-Content $manifest -Raw | ConvertFrom-Json
    $migration.retired.sha256='0000000000000000000000000000000000000000000000000000000000000000'
    $migration | ConvertTo-Json -Depth 8 | Set-Content $manifest -Encoding UTF8
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'Stale or missing identity binding'
    [IO.File]::WriteAllBytes($manifest,$saved)
    $migration=Get-Content $manifest -Raw | ConvertFrom-Json
    $migration.replacement.path='Tasks/items/web/missing/TASK.md'
    $migration | ConvertTo-Json -Depth 8 | Set-Content $manifest -Encoding UTF8
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'Stale or missing identity binding'
    [IO.File]::WriteAllBytes($manifest,$saved)
    $migration=Get-Content $manifest -Raw | ConvertFrom-Json
    $migration.correction_id='FDEC-999'
    $migration | ConvertTo-Json -Depth 8 | Set-Content $manifest -Encoding UTF8
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'Invalid retirement event'
    [IO.File]::WriteAllBytes($manifest,$saved)
    New-Item -ItemType Directory "$temp/Tasks/items/foundation/FDEC-005-duplicate-fixture" | Out-Null
    Copy-Item "$temp/Tasks/items/foundation/FDEC-005-architecture-and-backend-adr/TASK.md" "$temp/Tasks/items/foundation/FDEC-005-duplicate-fixture/TASK.md"
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'Duplicate record'
    Write-Output 'PASS: retained/replacement identities, gate relinking, all admission actions and incomplete/stale/unrelated migration rejection'
} finally {
    $resolved=[IO.Path]::GetFullPath($temp)
    $parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-identity-')) { throw 'Unsafe cleanup target' }
    if (Test-Path $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
