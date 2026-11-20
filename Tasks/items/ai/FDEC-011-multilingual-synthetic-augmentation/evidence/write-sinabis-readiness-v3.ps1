param([Parameter(Mandatory=$true)][string]$Name)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
. "$root/scripts/validate_tasks/identity.ps1"
. "$root/scripts/validate_tasks/source-state.ps1"
. "$root/scripts/validate_tasks/acceptance-matrix.ps1"
. "$root/scripts/validate_tasks/readiness-events.ps1"
$task=Split-Path $PSScriptRoot
$relative=$task.Substring($root.Length+1).Replace('\','/')
$ready=Get-Content "$PSScriptRoot/independent-data-frozen-readiness-v2.json" -Raw | ConvertFrom-Json
$effective=Get-EffectiveCriteria $root $task
$ready.source_sha=git -C $root rev-parse HEAD
$ready.source_state_sha256=Get-SourceState $root 'FDEC-011'
$ready.criteria_revisions=$effective.revisions
$ready.atomicity.boundary_reason='One augmentation/input-provenance outcome including owner-requested independently generated source admission; no model training, split-policy weakening or later task execution.'
$ready.matrix=@(foreach($criterion in $effective.rows){
    [pscustomobject]@{id=$criterion.id;criterion_sha256=$criterion.criterion_sha256;level='Local software acceptance and source-rights/integrity verification';scenario=$criterion.criterion;command='powershell -NoProfile -File training/augmentation/test-native.ps1; powershell -NoProfile -File training/augmentation/test-sinabis.ps1';environment='Windows CPython 3.14.5 with pinned PyArrow; permitted technical fixtures, pinned public-source metadata and private source bytes only';expected='PASS with Codex fixture denial preserved, independent origin evidence, no trusted automatic labels or cross-thread/source-family split leakage'}
})
$output=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $output){throw 'Readiness evidence is append-only'}
$ready | ConvertTo-Json -Depth 45 | Set-Content -LiteralPath $output -Encoding UTF8
Write-ReadinessAcceptance $root $relative "evidence/$Name"
& "$root/scripts/validate_tasks/admission.ps1" -TaskId FDEC-011 -Action execute -ReadinessFile "evidence/$Name"
