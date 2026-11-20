param(
    [string]$Root = (Resolve-Path "$PSScriptRoot/../..").Path,
    [string]$TaskId,
    [string]$ReadinessFile = 'evidence/readiness.json',
    [ValidateSet('claim','dispatch','resume','execute','close')][string]$Action = 'dispatch'
)
$ErrorActionPreference = 'Stop'
$pin = Get-Content "$Root/Tasks/policy/adoption-5.6.json" -Raw | ConvertFrom-Json
foreach ($entry in $pin.inventory) {
    $path = Join-Path $Root $entry.path
    if (!(Test-Path -LiteralPath $path) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) {
        throw "Accepted baseline changed or missing: $($entry.path)"
    }
}
if ((Get-FileHash "$Root/Tasks/policy/upstream-5.6.md" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.policy_sha256) { throw 'Policy hash mismatch' }
$records = & "$PSScriptRoot/repository.ps1" -Root $Root -AsObject
if ($TaskId) {
    if (!$records.ContainsKey($TaskId) -or $records[$TaskId].epic) { throw 'Task must resolve uniquely' }
    $spec = Get-Item -LiteralPath $records[$TaskId].path
    $readyPath = [IO.Path]::GetFullPath((Join-Path $spec.DirectoryName $ReadinessFile))
    if (!$readyPath.StartsWith($spec.DirectoryName + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Readiness escapes task directory' }
    if (!(Test-Path $readyPath)) { throw 'Missing accepted readiness' }
    $ready = Get-Content $readyPath -Raw | ConvertFrom-Json
    if ($ready.task_sha256 -ne (Get-FileHash $spec.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -or $ready.policy_sha256 -ne $pin.policy_sha256) { throw 'Stale task or policy readiness' }
    $head = git -C $Root rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $ready.source_sha -ne $head) { throw 'Stale source readiness' }
    if ($ready.atomicity.outcomes.Count -ne 1 -or $ready.atomicity.packets.Count -lt 1 -or $ready.atomicity.packets.Count -gt 3 -or $ready.atomicity.independent_acceptance -ne $false -or !$ready.atomicity.boundary_reason) { throw 'Invalid atomicity' }
    if ($ready.atomicity.packets.Count -gt 1 -and !$ready.atomicity.inseparability_reason) { throw 'Missing inseparability reason' }
    if (!$ready.matrix -or !$ready.rule_sources -or !$ready.dependency_revisions -or !$ready.epic_state_evidence) { throw 'Incomplete readiness closure' }
    foreach ($row in $ready.matrix) { if (!$row.id -or !$row.command -or !$row.expected) { throw 'Incomplete AC row' } }
    if (!$ready.allowed_paths) { throw 'Missing bounded path scope' }
    $requiredRules = @('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md')
    $rootAbsolute = [IO.Path]::GetFullPath($Root).TrimEnd('\','/')
    foreach ($scope in $ready.allowed_paths) {
        $absolute = [IO.Path]::GetFullPath((Join-Path $Root $scope))
        if (!$absolute.StartsWith($rootAbsolute + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Scope escapes repository' }
        $dir = if (Test-Path $absolute -PathType Container) { $absolute } else { Split-Path $absolute }
        while ($dir.Length -gt $rootAbsolute.Length) {
            foreach ($name in 'AGENTS.md','DEVELOPMENT.md') {
                $rule = Join-Path $dir $name
                if (Test-Path $rule) { $requiredRules += $rule.Substring($rootAbsolute.Length+1).Replace('\','/') }
            }
            $dir = Split-Path $dir
        }
        if (Test-Path $absolute -PathType Container) {
            $requiredRules += @(Get-ChildItem $absolute -Recurse -File | Where-Object Name -In 'AGENTS.md','DEVELOPMENT.md' | ForEach-Object { $_.FullName.Substring($rootAbsolute.Length+1).Replace('\','/') })
        }
    }
    foreach ($rule in $requiredRules | Select-Object -Unique) { if ($ready.rule_sources.path -notcontains $rule) { throw "Missing governing rule: $rule" } }
    if (Test-Path "$Root/Tasks/migrations") {
        foreach ($file in Get-ChildItem "$Root/Tasks/migrations" -Filter '*.json') {
            $migration=Get-Content $file.FullName -Raw | ConvertFrom-Json
            $paths=@($file.FullName.Substring($rootAbsolute.Length+1).Replace('\','/')) + @($migration.retired.path,$migration.retained.path,$migration.replacement.path,$migration.retirement_event.path)
            foreach ($path in $paths) { if ($ready.migration_revisions.path -notcontains $path) { throw "Unbound identity migration: $path" } }
        }
    }
    foreach ($entry in @($ready.rule_sources) + @($ready.dependency_revisions) + @($ready.epic_state_evidence) + @($ready.migration_revisions)) {
        if ($null -eq $entry) { continue }
        $boundPath = [IO.Path]::GetFullPath((Join-Path $Root $entry.path))
        if (!$boundPath.StartsWith($rootAbsolute + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Readiness input escapes repository' }
        if (!$entry.path -or !$entry.sha256 -or (Get-FileHash (Join-Path $Root $entry.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Changed readiness input' }
    }
    $record = $records[$TaskId]
    if (!$record -or $record.status -in 'Done','Cancelled') { throw 'Task is terminal or missing' }
    $parent = $records[$record.parent]
    if ($parent.status -eq 'Done') { throw 'Epic is closed' }
    foreach ($dependency in @($record.dependencies) + @($parent.dependencies)) {
        if ($records[$dependency].status -ne 'Done') { throw "Dependency not Done: $dependency" }
        foreach ($path in $records[$dependency].state_paths) {
            $relative = $path.Substring($rootAbsolute.Length+1).Replace('\','/')
            if ($ready.dependency_revisions.path -notcontains $relative) { throw "Unbound dependency revision: $relative" }
        }
    }
    foreach ($epic in $records.Values | Where-Object epic) {
        if ($parent.id -match 'EPIC-D' -and $epic.id -match 'EPIC-D' -and $epic.id -ne $parent.id -and $epic.status -in 'Active','InProgress') { throw 'Another development Epic is active' }
        foreach ($path in $epic.state_paths) {
            $relative = $path.Substring($rootAbsolute.Length+1).Replace('\','/')
            if ($ready.epic_state_evidence.path -notcontains $relative) { throw "Unbound Epic revision: $relative" }
        }
    }
    # Semantic atomicity and impact review cannot be inferred from counters.
    if ($ready.semantic_review -ne 'accepted') { throw 'Semantic readiness review required' }
    if ($Action -eq 'close' -and !$ready.verification) { throw 'Closure requires verification evidence' }
    if ($Action -eq 'close') {
        foreach ($entry in $ready.verification) {
            $path = [IO.Path]::GetFullPath((Join-Path $Root $entry.path))
            if (!$path.StartsWith((Join-Path $spec.DirectoryName 'evidence') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or !$entry.sha256 -or (Get-FileHash $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Invalid closure evidence' }
        }
    }
}
Write-Output "PASS: immutable baseline and $Action admission inputs"
