param([Parameter(Mandatory)][string]$Root)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path
$validator = 'scripts/validate_tasks/repository.ps1'
$helper = 'scripts/validate_tasks/developer-adoption.ps1'
$verified = & (Join-Path $Root $validator) -Root $Root -AsObject
if ($verified['FDEC-102'].status -cne 'Done' -or
    $verified['FDEC-102'].closure_history.Count -ne 1 -or
    $verified['FDEC-EPIC-S001'].members -notcontains 'FDEC-102' -or
    $verified['FDEC-087'].status -cne 'Blocked') {
    throw 'Unexpected adoption or ordinary task projection'
}
Write-Output 'PASS: accepted adoption, version request and ordinary ledger projection'

$owned = Join-Path ([IO.Path]::GetTempPath()) "fdec-adoption-$([guid]::NewGuid())"
$fixture = Join-Path $owned 'source'
$pwsh = (Get-Process -Id $PID).Path
New-Item -ItemType Directory -Path $owned | Out-Null
function Assert-Rejected([string]$Reason) {
    $diagnostic = & $pwsh -NoProfile -NonInteractive -File (Join-Path $fixture $validator) -Root $fixture 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -or !$diagnostic.Contains($Reason)) {
        throw "Expected rejection '$Reason'. Actual diagnostic: $diagnostic"
    }
}
try {
    git -C $Root worktree add --detach $fixture HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create local fixture' }
    foreach ($path in $validator, $helper) {
        Copy-Item -LiteralPath (Join-Path $Root $path) -Destination (Join-Path $fixture $path) -Force
    }
    $event = Join-Path $fixture 'Tasks/items/governance/FDEC-238-fdtasks-adoption-record-compatibility/events/rejected-adoption-fixture.md'
    @'
---
schema: fdtasks-event/v3
event_id: 563c69a7-f760-41bc-b4d6-dbb48527949e
task_id: FDEC-238
event_type: completed
created_at: 2026-11-28T00:00:00.000Z
actor: fixture
base_revision: null
server_revision: null
status_from: "In Progress"
status_to: "Done"
---

Unapproved adoption closure envelope.
'@ | Set-Content -LiteralPath $event
    Assert-Rejected 'Unsupported event semantics: completed'
    Remove-Item -LiteralPath $event

    $proof = 'Tasks/items/governance/FDEC-102-adopt-fdtasks-5-7/evidence/20261121-closure.json'
    Add-Content -LiteralPath (Join-Path $fixture $proof) -Value ' '
    git -C $fixture add -- $proof
    if ($LASTEXITCODE -ne 0) { throw 'Cannot prepare tamper fixture' }
    git -C $fixture -c user.name=Fixture -c user.email=fixture@example.invalid commit -m 'Tamper with accepted adoption closure in disposable fixture'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot freeze tamper fixture' }
    Assert-Rejected 'Accepted developer adoption identity changed'
    Write-Output 'PASS: substitute event envelope and committed adoption tampering rejected'
} finally {
    if (Test-Path -LiteralPath $fixture) {
        git -C $Root worktree remove --force $fixture
        if ($LASTEXITCODE -ne 0) { throw 'Cannot remove owned local fixture' }
    }
    if (Test-Path -LiteralPath $owned) { Remove-Item -LiteralPath $owned }
}
