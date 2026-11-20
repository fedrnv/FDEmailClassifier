$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../..").Path
& "$PSScriptRoot/admission.ps1" -Root $root
$temp = Join-Path ([IO.Path]::GetTempPath()) ('fdec-adoption-' + [guid]::NewGuid())
try {
    New-Item -ItemType Directory $temp | Out-Null
    Copy-Item "$root/Tasks" "$temp/Tasks" -Recurse
    Copy-Item "$root/AGENTS.md", "$root/DEVELOPMENT.md" $temp
    # This fixture deliberately has no ready decision for FDEC-001.
    Remove-Item -LiteralPath "$temp/Tasks/items/foundation/FDEC-001-open-source-governance/evidence/readiness.json" -ErrorAction SilentlyContinue
    git -C $temp init --quiet
    git -C $temp add .
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m fixture
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create fixture baseline' }
    foreach ($action in 'claim','dispatch','resume','execute','close') {
        $rejected = $false
        try { & "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-001 -Action $action } catch { $rejected = $_ -match 'Missing accepted readiness' }
        if (!$rejected) { throw "Missing readiness accepted: $action" }
    }
    Add-Content "$temp/AGENTS.md" 'synthetic tamper'
    foreach ($action in 'claim','dispatch','resume','execute','close') {
        $rejected = $false
        try { & "$PSScriptRoot/admission.ps1" -Root $temp -TaskId FDEC-001 -Action $action } catch { $rejected = $_ -match 'Accepted baseline changed' }
        if (!$rejected) { throw "Altered rule accepted: $action" }
    }
    Write-Output 'PASS: all five actions reject missing readiness and tampered baseline'
} finally {
    $resolved = [IO.Path]::GetFullPath($temp)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (!$resolved.StartsWith($parent, [StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-adoption-')) { throw 'Unsafe cleanup target' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
