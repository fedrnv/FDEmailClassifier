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
if ($TaskId) {
    $specs = @(Get-ChildItem "$Root/Tasks/items" -Filter TASK.md -Recurse | Where-Object { (Get-Content $_.FullName -Raw) -match "(?m)^id: $([regex]::Escape($TaskId))\r?$" })
    if ($specs.Count -ne 1) { throw 'Task must resolve uniquely' }
    $spec = $specs[0]
    $readyPath = Join-Path $spec.DirectoryName $ReadinessFile
    if (!(Test-Path $readyPath)) { throw 'Missing accepted readiness' }
    $ready = Get-Content $readyPath -Raw | ConvertFrom-Json
    if ($ready.task_sha256 -ne (Get-FileHash $spec.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -or $ready.policy_sha256 -ne $pin.policy_sha256) { throw 'Stale task or policy readiness' }
    $head = git -C $Root rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $ready.source_sha -ne $head) { throw 'Stale source readiness' }
    if ($ready.atomicity.outcomes.Count -ne 1 -or $ready.atomicity.packets.Count -lt 1 -or $ready.atomicity.packets.Count -gt 3 -or $ready.atomicity.independent_acceptance -ne $false -or !$ready.atomicity.boundary_reason) { throw 'Invalid atomicity' }
    if ($ready.atomicity.packets.Count -gt 1 -and !$ready.atomicity.inseparability_reason) { throw 'Missing inseparability reason' }
    if (!$ready.matrix -or !$ready.rule_sources -or !$ready.dependency_revisions -or !$ready.epic_state_evidence) { throw 'Incomplete readiness closure' }
    foreach ($entry in @($ready.rule_sources) + @($ready.dependency_revisions) + @($ready.epic_state_evidence)) {
        if (!$entry.path -or !$entry.sha256 -or (Get-FileHash (Join-Path $Root $entry.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Changed readiness input' }
    }
    # Status/dependency semantics and scope remain an explicit executor review.
    if ($ready.semantic_review -ne 'accepted') { throw 'Semantic readiness review required' }
    if ($Action -eq 'close' -and !$ready.verification) { throw 'Closure requires verification evidence' }
}
Write-Output "PASS: immutable baseline and $Action admission inputs"
