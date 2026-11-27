param([Parameter(Mandatory)][string]$Root)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path
$entryPoint = 'scripts/validate_tasks/admission.ps1'
& (Join-Path $Root $entryPoint) -Root $Root -Action close

$owned = Join-Path ([IO.Path]::GetTempPath()) "fdec-adopted-rules-$([guid]::NewGuid())"
$fixture = Join-Path $owned 'source'
$pwsh = (Get-Process -Id $PID).Path
New-Item -ItemType Directory -Path $owned | Out-Null
try {
    git -C $Root worktree add --detach $fixture HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create local rule fixture' }
    foreach ($path in $entryPoint, 'scripts/validate_tasks/developer-adoption.ps1') {
        Copy-Item -LiteralPath (Join-Path $Root $path) -Destination (Join-Path $fixture $path) -Force
    }
    Add-Content -LiteralPath (Join-Path $fixture 'AGENTS.md') -Value 'Unexpected local rule change'
    $diagnostic = & $pwsh -NoProfile -NonInteractive -File (Join-Path $fixture $entryPoint) -Root $fixture -Action close 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -or !$diagnostic.Contains('Accepted baseline changed or missing: AGENTS.md')) {
        throw "Unexpected rule-change diagnostic: $diagnostic"
    }
    Write-Output 'PASS: exact adopted rules recognized, unexpected rule change rejected'
} finally {
    if (Test-Path -LiteralPath $fixture) {
        git -C $Root worktree remove --force $fixture
        if ($LASTEXITCODE -ne 0) { throw 'Cannot remove owned rule fixture' }
    }
    if (Test-Path -LiteralPath $owned) { Remove-Item -LiteralPath $owned }
}
