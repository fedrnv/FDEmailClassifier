$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../..").Path
& "$PSScriptRoot/verify-governance.ps1" -Root $root
$temp = Join-Path ([IO.Path]::GetTempPath()) ('fdec-legal-' + [guid]::NewGuid())
function MustReject([scriptblock]$Action, [string]$Expected) {
    $rejected = $false
    try { & $Action } catch { if ($_.Exception.Message -match $Expected) { $rejected = $true } else { throw } }
    if (!$rejected) { throw "Expected rejection: $Expected" }
}
try {
    New-Item -ItemType Directory "$temp/docs/legal", "$temp/Tasks/policy" -Force | Out-Null
    Copy-Item "$root/docs/legal/*" "$temp/docs/legal"
    Copy-Item "$root/Tasks/policy/upstream-5.6.md" "$temp/Tasks/policy"
    foreach ($name in 'LICENSE','NOTICE','CONTRIBUTING.md','CODE_OF_CONDUCT.md','SECURITY.md') { Copy-Item "$root/$name" $temp }
    $before = (Get-FileHash "$temp/NOTICE").Hash
    Move-Item -LiteralPath "$temp/LICENSE" -Destination "$temp/LICENSE.saved"
    MustReject { & "$PSScriptRoot/verify-governance.ps1" -Root $temp } 'Missing required governance file: LICENSE'
    Move-Item -LiteralPath "$temp/LICENSE.saved" -Destination "$temp/LICENSE"
    Add-Content "$temp/LICENSE" 'synthetic corruption'
    MustReject { & "$PSScriptRoot/verify-governance.ps1" -Root $temp } 'Material hash mismatch: LICENSE'
    Copy-Item "$root/LICENSE" "$temp/LICENSE" -Force
    MustReject { & "$PSScriptRoot/verify-governance.ps1" -Root $temp -ForDistribution } 'Distribution blocked:'
    $inventory = Get-Content "$temp/docs/legal/inventory.json" -Raw | ConvertFrom-Json
    $inventory.materials[1].decision = 'included'
    $inventory | ConvertTo-Json -Depth 5 | Set-Content "$temp/docs/legal/inventory.json" -Encoding UTF8
    MustReject { & "$PSScriptRoot/verify-governance.ps1" -Root $temp } 'Unknown license cannot be included'
    if ((Get-FileHash "$temp/NOTICE").Hash -ne $before) { throw 'Validator mutated unrelated input' }
    Write-Output 'PASS: missing/corrupt license, unresolved distribution and unknown approval rejected; input preserved'
} finally {
    $resolved = [IO.Path]::GetFullPath($temp)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (!$resolved.StartsWith($parent, [StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-legal-')) { throw 'Unsafe cleanup target' }
    if (Test-Path $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
