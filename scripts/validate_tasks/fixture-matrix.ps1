# Synthetic fixture authoring only; this does not claim real task acceptance.
function Initialize-FixtureHistory([string]$Root,[string]$Source) {
    # Historical source bindings in copied Tasks require their actual ancestry.
    # Use a local fetch, not invented commits or a production validation bypass.
    $absolute=[IO.Path]::GetFullPath($Root)
    $parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
    if(!$absolute.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $absolute -Leaf).StartsWith('fdec-') -or $absolute -eq [IO.Path]::GetFullPath($Source)){throw 'Unsafe fixture history target'}
    git -C $absolute init --quiet
    if($LASTEXITCODE -ne 0){throw 'Fixture Git initialization failed'}
    git -C $absolute fetch --quiet --no-tags -- $Source HEAD
    if($LASTEXITCODE -ne 0){throw 'Fixture local history fetch failed'}
    git -C $absolute reset --soft FETCH_HEAD
    if($LASTEXITCODE -ne 0){throw 'Fixture history initialization failed'}
    if(Test-Path (Join-Path $Source '.gitattributes')){Copy-Item -LiteralPath (Join-Path $Source '.gitattributes') -Destination (Join-Path $absolute '.gitattributes')}
}
. "$PSScriptRoot/acceptance-matrix.ps1"
. "$PSScriptRoot/identity-migrations.ps1"
function New-FixtureMigrationBindings([string]$Root) {
    $paths=@(foreach($file in Get-ChildItem "$Root/Tasks/migrations" -Filter '*.json'){Get-MigrationPaths $Root $file.FullName})
    return @($paths | Sort-Object -Unique | ForEach-Object {@{path=$_;sha256=(Get-IdentityHash (Join-Path $Root $_))}})
}
function New-FixtureDependencyBindings([string]$Root,[string]$TaskId) {
    $records=& "$PSScriptRoot/repository.ps1" -Root $Root -AsObject
    $record=$records[$TaskId];$parent=$records[$record.parent]
    $paths=@(foreach($id in @($record.dependencies)+@($parent.dependencies)){foreach($path in $records[$id].state_paths){$path.Substring($Root.Length+1).Replace('\','/')}})
    if(!$paths.Count){$paths=@($parent.path.Substring($Root.Length+1).Replace('\','/'))}
    return @($paths | Sort-Object -Unique | ForEach-Object {@{path=$_;sha256=(Get-IdentityHash (Join-Path $Root $_))}})
}
function Reset-FixtureFoundationEpic([string]$Root) {
    # Admission fixtures target the foundation stage. Isolate them from later
    # actual Epic activations/closures without changing production validation.
    $absolute=[IO.Path]::GetFullPath($Root)
    if(!$absolute.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()),[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $absolute -Leaf).StartsWith('fdec-')){throw 'Unsafe fixture foundation reset'}
    foreach($epic in Get-ChildItem (Join-Path $absolute 'Tasks/epics') -Directory | Where-Object Name -Match '^FDEC-EPIC-D[0-9]{3}$'){
        foreach($file in Get-ChildItem (Join-Path $epic.FullName 'events') -Filter '*.md' -ErrorAction SilentlyContinue){
            if([IO.File]::ReadAllText($file.FullName) -match '(?m)^event_type: (?:status-changed|work-started)\r?$'){Remove-Item -LiteralPath $file.FullName}
        }
        Remove-Item -LiteralPath (Join-Path $absolute "Tasks/version-requests/$($epic.Name).json") -ErrorAction SilentlyContinue
    }
    @'
---
schema: fdtasks-event/v3
event_id: fixture-foundation-stage-active
task_id: FDEC-EPIC-D001
event_type: status-changed
created_at: 2026-11-20T00:00:00Z
actor: fixture
base_revision: fixture
server_revision: null
---
Planned -> Active.
'@ | Set-Content (Join-Path $absolute 'Tasks/epics/FDEC-EPIC-D001/events/fixture-active.md') -Encoding UTF8
}
function New-FixtureMatrix([string]$Root,[string]$TaskPath,[string]$Command) {
    $effective=Get-EffectiveCriteria $Root (Join-Path $Root $TaskPath)
    return @($effective.rows|ForEach-Object{@{id=$_.id;criterion_sha256=$_.criterion_sha256;scenario="Exercise fixture admission for $($_.id)";level='local admission contract';command=$Command;environment='Owned synthetic Git fixture';expected='Fixture-specific positive or explicit rejection outcome'}})
}
