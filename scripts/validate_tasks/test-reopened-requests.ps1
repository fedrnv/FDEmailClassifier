$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/fixture-matrix.ps1"
$records=& "$PSScriptRoot/repository.ps1" -Root $root -AsObject
if ($records['FDEC-006'].status -notin 'Planned','InProgress','Done' -or !$records['FDEC-006'].closure_history.Count) { throw 'Expected gate closure history' }
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-reopen-'+[guid]::NewGuid())
function Reject([scriptblock]$Run,[string]$Pattern) {
    $failed=$false
    try {& $Run} catch {if($_.Exception.Message -match $Pattern){$failed=$true}else{throw}}
    if(!$failed){throw "Expected rejection: $Pattern"}
}
function Write-Transition($name,$transition,$extra='') {
    @"
---
schema: fdtasks-event/v3
event_id: fixture-$name
task_id: FDEC-006
event_type: status-changed
created_at: 2026-11-22T00:00:$($script:second.ToString('00'))Z
actor: fixture
base_revision: fixture
server_revision: null
$extra
---
$transition.
"@ | Set-Content "$temp/Tasks/items/quality/FDEC-006-targeted-integration-gate/events/fixture-$name.md" -Encoding UTF8
    $script:second++
}
try {
    New-Item -ItemType Directory $temp | Out-Null
    Copy-Item "$root/Tasks" "$temp/Tasks" -Recurse
    Copy-Item "$root/AGENTS.md","$root/DEVELOPMENT.md" $temp
    # This synthetic task stays Planned regardless of later real correction work.
    $target='Tasks/items/governance/FDEC-999-reopen-fixture'
    New-Item -ItemType Directory "$temp/$target/events","$temp/$target/evidence" -Force|Out-Null
    $spec=[IO.File]::ReadAllText("$root/Tasks/items/foundation/FDEC-005-architecture-and-backend-adr/TASK.md").Replace('FDEC-005','FDEC-999').Replace('epic_id: FDEC-EPIC-D001','epic_id: FDEC-EPIC-S001')
    [IO.File]::WriteAllText("$temp/$target/TASK.md",$spec)
    @'
---
schema: fdtasks-event/v3
event_id: fixture-member-999
task_id: FDEC-EPIC-S001
event_type: membership-added
created_at: 2026-11-21T00:00:00Z
actor: fixture
base_revision: fixture
server_revision: null
---
Add FDEC-999 as a synthetic fixture member only.
'@|Set-Content "$temp/Tasks/epics/FDEC-EPIC-S001/events/fixture-member.md" -Encoding UTF8
    Initialize-FixtureHistory $temp $root
    git -C $temp add .
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m fixture
    if($LASTEXITCODE -ne 0){throw 'Fixture baseline failed'}
    $request="$temp/Tasks/version-requests/FDEC-006.json"
    $before=(Get-FileHash $request).Hash
    $script:second=0
    if($records['FDEC-006'].status -ne 'Planned'){Write-Transition reset "$($records['FDEC-006'].status) -> Planned"}
    Write-Transition start 'Planned -> InProgress'
    Write-Transition reclose 'InProgress -> Done'
    $state=& "$PSScriptRoot/repository.ps1" -Root $temp -AsObject
    if($state['FDEC-006'].status -ne 'Done'){throw 'Reclose projection failed'}
    Write-Transition reopen 'Done -> Planned'
    $state=& "$PSScriptRoot/repository.ps1" -Root $temp -AsObject
    if($state['FDEC-006'].status -ne 'Planned' -or (Get-FileHash $request).Hash -ne $before){throw 'First request was not preserved'}
    $duplicate=Get-Content $request -Raw|ConvertFrom-Json
    $duplicate.request_id=[guid]::NewGuid().ToString()
    $duplicate|ConvertTo-Json -Depth 5|Set-Content "$temp/Tasks/version-requests/duplicate.json" -Encoding UTF8
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'Invalid closed item request'
    Remove-Item -LiteralPath "$temp/Tasks/version-requests/duplicate.json"
    $fake=@{schema='fdtasks-version-request/v1';request_id='fixture-new-request';type='task_closed';epic_id='FDEC-EPIC-S001';work_item_id='FDEC-999';summary='fixture';verification=@("$target/evidence/proof.md")}
    [IO.File]::WriteAllText("$temp/$target/evidence/proof.md",'Synthetic proof')
    $fake|ConvertTo-Json -Depth 5|Set-Content "$temp/Tasks/version-requests/new.json" -Encoding UTF8
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'Invalid closed item request'
    @'
---
schema: fdtasks-event/v3
event_id: fixture-fabricated-done
task_id: FDEC-999
event_type: status-changed
created_at: 2026-11-22T00:01:00Z
actor: fixture
base_revision: fixture
server_revision: null
---
Planned -> Done.
'@|Set-Content "$temp/$target/events/fake-done.md" -Encoding UTF8
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'requires verified first-closure proof'
    $proof=@{source_sha=(git -C $temp rev-parse HEAD);task_sha256=(Get-FileHash "$temp/$target/TASK.md" -Algorithm SHA256).Hash.ToLowerInvariant();verification=@(@{path="$target/evidence/proof.md";sha256=(Get-FileHash "$temp/$target/evidence/proof.md" -Algorithm SHA256).Hash.ToLowerInvariant()})}
    $proof|ConvertTo-Json -Depth 5|Set-Content "$temp/$target/evidence/closure.json" -Encoding UTF8
    $proofHash=(Get-FileHash "$temp/$target/evidence/closure.json" -Algorithm SHA256).Hash.ToLowerInvariant()
    $eventPath="$temp/$target/events/fake-done.md"
    $text=[IO.File]::ReadAllText($eventPath).Replace('server_revision: null',"server_revision: null`nclosure_proof: evidence/closure.json`nclosure_proof_sha256: $proofHash")
    [IO.File]::WriteAllText($eventPath,$text)
    $null=& "$PSScriptRoot/repository.ps1" -Root $temp -AsObject
    [IO.File]::WriteAllText("$temp/$target/evidence/proof.md",'Changed synthetic evidence')
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'Unverified closure evidence'
    [IO.File]::WriteAllText("$temp/$target/evidence/proof.md",'Synthetic proof')
    $fake.epic_id='FDEC-EPIC-D001'
    $fake|ConvertTo-Json -Depth 5|Set-Content "$temp/Tasks/version-requests/new.json" -Encoding UTF8
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'Invalid closed item request'
    $fake.epic_id='FDEC-EPIC-S001'; $fake.verification=@('README.md')
    $fake|ConvertTo-Json -Depth 5|Set-Content "$temp/Tasks/version-requests/new.json" -Encoding UTF8
    Reject {& "$PSScriptRoot/repository.ps1" -Root $temp} 'verification reference'
    Write-Output 'PASS: reopen/reclose preserves first request; duplicate, never-closed, fabricated proof, wrong parent and foreign evidence reject'
} finally {
    $resolved=[IO.Path]::GetFullPath($temp);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-reopen-')){throw 'Unsafe cleanup target'}
    if(Test-Path $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
# Epic first-closure requests share this lifecycle boundary and run in the D001
# gate through this existing entrypoint. The suite owns a separate tiny fixture.
& "$PSScriptRoot/test-epic-closure.ps1"
