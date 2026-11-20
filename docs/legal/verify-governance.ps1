param([string]$Root = (Resolve-Path "$PSScriptRoot/../..").Path, [switch]$ForDistribution)
$ErrorActionPreference = 'Stop'
foreach ($path in 'LICENSE','NOTICE','CONTRIBUTING.md','CODE_OF_CONDUCT.md','SECURITY.md','docs/legal/THIRD_PARTY.md','docs/legal/inventory.json') {
    if (!(Test-Path -LiteralPath (Join-Path $Root $path) -PathType Leaf)) { throw "Missing required governance file: $path" }
    if (!(Get-Content -LiteralPath (Join-Path $Root $path) -Raw).Trim()) { throw "Empty governance file: $path" }
}
$inventory = Get-Content "$Root/docs/legal/inventory.json" -Raw | ConvertFrom-Json
if ($inventory.schema -ne 'fdec-third-party/v1' -or !$inventory.materials) { throw 'Invalid inventory' }
foreach ($entry in $inventory.materials) {
    if (!$entry.path -or !$entry.source -or !$entry.sha256 -or !$entry.license -or $entry.decision -notin @('included','blocked')) { throw 'Incomplete inventory entry' }
    if ($entry.decision -eq 'included' -and $entry.license -eq 'UNKNOWN') { throw 'Unknown license cannot be included' }
    if ($ForDistribution -and $entry.decision -eq 'blocked') { throw "Distribution blocked: $($entry.path)" }
    $path = [IO.Path]::GetFullPath((Join-Path $Root $entry.path))
    if (!$path.StartsWith(([IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Inventory path escapes repository' }
    if (!(Test-Path -LiteralPath $path)) { throw "Missing inventoried material: $($entry.path)" }
    # Canonical LF allows Git checkouts with core.autocrlf enabled.
    $bytes = [Text.Encoding]::UTF8.GetBytes(([IO.File]::ReadAllText($path) -replace "`r`n", "`n"))
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $actual = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
    # The adopted policy pin binds original raw bytes; other materials use canonical LF.
    if ($entry.path -eq 'Tasks/policy/upstream-5.6.md') { $actual = (Get-FileHash $path -Algorithm SHA256).Hash.ToLowerInvariant() }
    if ($actual -ne $entry.sha256) { throw "Material hash mismatch: $($entry.path)" }
}
if ($inventory.runtime_dependencies.Count -gt 0 -and !(Test-Path "$Root/Cargo.lock")) { throw 'Runtime inventory requires locked graph' }
if (Test-Path "$Root/Cargo.toml") {
    Push-Location $Root
    try { & cargo deny check licenses; if ($LASTEXITCODE -ne 0) { throw 'cargo deny license check failed' } } finally { Pop-Location }
} else { Write-Output 'NOT APPLICABLE: cargo deny (no Cargo.toml at this foundation baseline)' }
Write-Output 'PASS: source governance and inventory integrity (distribution requires -ForDistribution)'
