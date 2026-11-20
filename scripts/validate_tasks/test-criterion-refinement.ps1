$ErrorActionPreference='Stop'
. "$PSScriptRoot/acceptance-matrix.ps1"
$root=(Resolve-Path "$PSScriptRoot/../..").Path
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('fdec-refinement-'+[guid]::NewGuid())
try {
    $task=Join-Path $fixture 'Tasks/items/foundation/FDEC-005-fixture'
    New-Item -ItemType Directory -Force "$task/events","$task/evidence"|Out-Null
    Copy-Item "$root/Tasks/items/foundation/FDEC-005-architecture-and-backend-adr/TASK.md" "$task/TASK.md"
    $original=Get-EffectiveCriteria $fixture $task
    $data=@{schema='fdec-acceptance-amendment/v1';task_id='FDEC-005';updates=@(@{id='AC-02';criterion='Refined synthetic failure and recovery boundary'})}
    function Publish-Fixture {
        $data|ConvertTo-Json -Depth 5|Set-Content "$task/evidence/update.json" -Encoding UTF8
        $hash=Get-IdentityHash "$task/evidence/update.json"
        @"
---
schema: fdtasks-event/v3
event_id: refinement-fixture
task_id: FDEC-005
event_type: scope-amended
created_at: 2026-11-20T12:00:00Z
actor: fixture
base_revision: fixture
server_revision: null
acceptance_file: evidence/update.json
acceptance_sha256: $hash
---
Explicit synthetic criterion refinement.
"@|Set-Content "$task/events/update.md" -Encoding UTF8
    }
    Publish-Fixture
    $updated=Get-EffectiveCriteria $fixture $task
    if($updated.rows.Count -ne 2 -or $updated.revisions.Count -ne 2 -or $updated.rows[1].criterion_sha256 -eq $original.rows[1].criterion_sha256){throw 'Refinement identity was not updated'}
    [IO.File]::AppendAllText("$task/evidence/update.json",' ')
    $rejected=$false
    try{$null=Get-EffectiveCriteria $fixture $task}catch{if($_.Exception.Message -match 'Invalid acceptance amendment binding'){$rejected=$true}else{throw}}
    if(!$rejected){throw 'Tampered amendment accepted'}
    $data.updates[0].id='AC-99'
    Publish-Fixture
    $rejected=$false
    try{$null=Get-EffectiveCriteria $fixture $task}catch{if($_.Exception.Message -match 'Amendment criterion identity mismatch'){$rejected=$true}else{throw}}
    if(!$rejected){throw 'Unknown refinement accepted'}
    Write-Output 'PASS: same-ID refinement changes criterion hash; tampered and unknown refinements reject'
} finally {
    $resolved=[IO.Path]::GetFullPath($fixture)
    $parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-refinement-')){throw 'Unsafe cleanup target'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
