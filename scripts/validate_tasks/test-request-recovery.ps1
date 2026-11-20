$ErrorActionPreference='Stop'
$validator=Join-Path $PSScriptRoot 'repository.ps1'
. "$PSScriptRoot/identity.ps1"
. "$PSScriptRoot/request-recovery.ps1"
function Field($Text,$Key){$m=[regex]::Match($Text,"(?m)^$([regex]::Escape($Key)): ([^\r\n]+)");if(!$m.Success){throw 'Missing fixture field'};return $m.Groups[1].Value.Trim().Trim('"')}
function Envelope($Path){$text=[IO.File]::ReadAllText($Path);$m=[regex]::Match($text,'\A(?:\uFEFF)?---\r?\n(.*?)\r?\n---\r?\n','Singleline');if(!$m.Success){throw 'Invalid fixture envelope'};return @{front=$m.Groups[1].Value;text=$text;path=$Path}}
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('fdec-request-recovery-'+[guid]::NewGuid())
$target='Tasks/items/quality/FDEC-901-rejected'
$governing='Tasks/items/governance/FDEC-902-recovery'
$requestPath='Tasks/version-requests/FDEC-901.json'
$recoveryPath='Tasks/request-recoveries/FDEC-901-R001.json'
$adoptionPath='Tasks/epics/FDEC-EPIC-S001/events/adoption.md'
$rejectionPath="$target/evidence/rejection.json"
function Assert-Owned {
    $full=[IO.Path]::GetFullPath($fixture);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
    if(!$full.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $full -Leaf).StartsWith('fdec-request-recovery-')){throw 'Unsafe recovery fixture path'}
}
function Put([string]$Path,[string]$Text){$full=Join-Path $fixture $Path;$null=New-Item -ItemType Directory -Force -Path (Split-Path $full);[IO.File]::WriteAllText($full,$Text,[Text.UTF8Encoding]::new($false))}
function Json([string]$Path,$Value){Put $Path ($Value|ConvertTo-Json -Depth 30)}
function Bound([string]$Path){@{path=$Path;sha256=(Get-IdentityHash (Join-Path $fixture $Path))}}
function Commit([string]$Message){git -C $fixture add .;git -C $fixture -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m $Message;if($LASTEXITCODE -ne 0){throw 'Fixture commit failed'}}
function Spec([string]$Path,[string]$Id,[string]$Parent){Put "$Path/TASK.md" "---`nschema: fdtasks-spec/v3`nid: $Id`ntitle: Synthetic metadata fixture`ntype: Correction`nepic_id: $Parent`nsize: medium`ninitial_status: Planned`ninitial_dependencies: []`natomicity:`n  outcomes: [`"One synthetic verification outcome`"]`n  packets: [`"One synthetic packet`"]`n  independent_acceptance: false`n  boundary_reason: `"One isolated fixture`"`n---`n| AC-01 | Valid fixture |`n| AC-02 | Invalid fixture |`n"}
function Event([string]$Path,[string]$Id,[string]$Kind,[string]$Payload,[string]$Extra=''){
    Put $Path "---`nschema: fdtasks-event/v3`nevent_id: $([guid]::NewGuid())`ntask_id: $Id`nevent_type: $Kind`ncreated_at: 2026-11-22T01:00:00Z`nactor: fixture`nbase_revision: fixture`nserver_revision: null`n$Extra`n---`n$Payload`n"
}
function Write-Recovery {
    Json $recoveryPath $script:recovery
    Event $adoptionPath FDEC-EPIC-S001 scope-amended 'Explicit synthetic recovery adoption; never actual project acceptance.' "correction_id: FDEC-902`nrecovery_file: $recoveryPath`nrecovery_sha256: $((Bound $recoveryPath).sha256)`nrecovery_contract: Tasks/policy/rejected-request-recovery-1.0.md`nrecovery_contract_sha256: $((Bound 'Tasks/policy/rejected-request-recovery-1.0.md').sha256)"
}
function Reset-Case {
    Assert-Owned
    git -C $fixture reset --hard --quiet $script:badSource
    git -C $fixture clean -fd --quiet
    if($LASTEXITCODE -ne 0){throw 'Fixture reset failed'}
    $script:recovery=$script:pristine|ConvertFrom-Json
    Json $rejectionPath $script:rejection
    Write-Recovery
    $script:fixtureRecords=& $validator -Root $fixture -AsObject
}
function Resolve-Fixture {
    $files=@(Get-ChildItem "$fixture/Tasks/version-requests" -Filter '*.json')
    Get-ResolvedClosureRequests $fixture $script:fixtureRecords $files (git -C $fixture rev-parse HEAD)
}
$script:negativeCount=0
function Reject([string]$Label,[scriptblock]$Change,[string]$Pattern,[switch]$NoWrite,[switch]$Full){
    Reset-Case
    & $Change
    if(!$NoWrite){Write-Recovery}
    $failed=$false
    try {if($Full){$null=& $validator -Root $fixture -AsObject}else{$null=Resolve-Fixture}} catch {
        if($_.Exception.Message -notmatch $Pattern){throw "Unexpected failure for ${Label}: $($_.Exception.Message)"};$failed=$true
    }
    if(!$failed){throw "Invalid recovery accepted: $Label"}
    $script:negativeCount++
    Write-Output "PASS: reject $Label"
}
try {
    Assert-Owned;$null=New-Item -ItemType Directory -Path $fixture
    Put '.gitattributes' '* text=auto eol=lf'
    foreach($special in 'S001','S002'){Put "Tasks/epics/FDEC-EPIC-$special/EPIC.md" "---`nschema: fdtasks-epic/v4`nid: FDEC-EPIC-$special`ninitial_status: Active`ninitial_dependencies: []`n---`n$(if($special -eq 'S001'){'- FDEC-902'})`n"}
    Put 'Tasks/epics/FDEC-EPIC-D001/EPIC.md' "---`nschema: fdtasks-epic/v4`nid: FDEC-EPIC-D001`ninitial_status: Active`ninitial_dependencies: []`n---`n- FDEC-901`n"
    Spec $target FDEC-901 FDEC-EPIC-D001;Spec $governing FDEC-902 FDEC-EPIC-S001
    Event "$governing/events/started.md" FDEC-902 work-started 'Planned -> InProgress.'
    Put 'Tasks/policy/rejected-request-recovery-1.0.md' ([IO.File]::ReadAllText("$PSScriptRoot/../../Tasks/policy/rejected-request-recovery-1.0.md"))
    git -C $fixture init --quiet;Commit 'synthetic source'
    $script:candidate=git -C $fixture rev-parse HEAD
    Put "$target/evidence/pass.md" 'Synthetic metadata proof, no actual project or data grant.'
    Json "$target/evidence/closure.json" @{source_sha=$script:candidate;task_sha256=(Bound "$target/TASK.md").sha256;verification=@((Bound "$target/evidence/pass.md"))}
    Event "$target/events/done.md" FDEC-901 status-changed 'Planned -> Done.' "closure_proof: evidence/closure.json`nclosure_proof_sha256: $((Bound "$target/evidence/closure.json").sha256)"
    $script:original=@{schema='fdtasks-version-request/v1';request_id='synthetic-rejected-id';type='task_closed';work_item_id='FDEC-901';epic_id='FDEC-EPIC-D001';summary='One synthetic rejected request';verification=@("$target/evidence/pass.md")}
    Json $requestPath $script:original;Commit 'synthetic rejected request'
    $script:badSource=git -C $fixture rev-parse HEAD
    $failed=$false
    try {$null=& $validator -Root $fixture -AsObject} catch {if($_.Exception.Message -match 'Closure request type does not match item'){$failed=$true}else{throw}}
    if(!$failed){throw 'Unrecovered original did not reject'}
    $script:rejection=@{schema='fdec-local-verification/v1';result='FAIL';exit_code=1;reason='Closure request type does not match item';actual_type='task_closed';required_type='correction_closed';correction='FDEC-902';request=(Bound $requestPath);allocated=$false;published=$false;acceptance_claimed=$false;source_sha=$script:badSource}
    Json $rejectionPath $script:rejection
    $script:recovery=@{schema='fdec-rejected-request-recovery/v1';recovery_id='FDEC-901-R001';correction_id='FDEC-902';request=(Bound $requestPath);spec=(Bound "$target/TASK.md");first_closure=(Bound "$target/events/done.md");closure_proof=(Bound "$target/evidence/closure.json");rejection=(Bound $rejectionPath);governing_spec=(Bound "$governing/TASK.md");contract=(Bound 'Tasks/policy/rejected-request-recovery-1.0.md');adoption_event=$adoptionPath;source_sha=$script:badSource;expected_type='correction_closed';reason='Synthetic rejected type mismatch only'}
    $script:pristine=$script:recovery|ConvertTo-Json -Depth 30
    Write-Recovery
    $script:fixtureRecords=& $validator -Root $fixture -AsObject
    $resolved=@(Resolve-Fixture)
    if($resolved.Count -ne 1 -or $resolved[0].request.type -cne 'correction_closed'){throw 'Effective correction missing'}
    $copy=$resolved[0].request|ConvertTo-Json|ConvertFrom-Json;$copy.type='task_closed'
    if(($copy|ConvertTo-Json -Compress) -cne ((Get-Content "$fixture/$requestPath" -Raw|ConvertFrom-Json)|ConvertTo-Json -Compress)){throw 'Recovery altered other request fields'}
    if((Bound $requestPath).sha256 -cne $script:recovery.request.sha256){throw 'Original request was overwritten'}
    Write-Output 'PASS: exact rejected request recovers; original bytes, all other fields and one identity preserved'
    Reject 'missing recovery' {Remove-Item -LiteralPath "$fixture/$recoveryPath"} 'Closure request type does not match item' -NoWrite -Full
    Reject 'unknown overlay field' {$script:recovery|Add-Member noteproperty request_id 'replacement'} 'Unsupported recovery fields'
    Reject 'wrong derived type' {$script:recovery.expected_type='bug_closed'} 'cannot rewrite a valid request or invent'
    Reject 'wrong request hash' {$script:recovery.request.sha256='0'*64} 'Invalid recovery artifact binding'
    Reject 'wrong specification' {$script:recovery.spec=Bound "$governing/TASK.md"} 'specification does not match'
    Reject 'wrong first closure' {$script:recovery.first_closure=Bound "$governing/events/started.md"} 'does not bind first closure'
    Reject 'wrong closure proof' {$script:recovery.closure_proof.sha256='0'*64} 'Invalid recovery artifact binding'
    Reject 'missing evidence binding' {$script:recovery.rejection=$null} 'Missing recovery binding'
    Reject 'allocated input' {$copy=$script:rejection.Clone();$copy.allocated=$true;Json $rejectionPath $copy;$script:recovery.rejection=Bound $rejectionPath} 'explicitly rejected unallocated'
    Reject 'published input' {$copy=$script:rejection.Clone();$copy.published=$true;Json $rejectionPath $copy;$script:recovery.rejection=Bound $rejectionPath} 'explicitly rejected unallocated'
    Reject 'accepted input' {$copy=$script:rejection.Clone();$copy.acceptance_claimed=$true;Json $rejectionPath $copy;$script:recovery.rejection=Bound $rejectionPath} 'explicitly rejected unallocated'
    Reject 'wrong rejection reason' {$copy=$script:rejection.Clone();$copy.reason='unrelated';Json $rejectionPath $copy;$script:recovery.rejection=Bound $rejectionPath} 'Invalid rejected-request evidence'
    Reject 'unknown rejected source' {$script:recovery.source_sha='f'*40} 'not an ancestor'
    Reject 'wrong source commit' {$script:recovery.source_sha=$script:candidate} 'original request creation commit'
    Reject 'self-authorized correction' {$script:recovery.correction_id='FDEC-901'} 'Invalid rejected-request evidence|Missing independent governing'
    Reject 'inactive governing correction' {$script:fixtureRecords['FDEC-902'].status='Planned'} 'Invalid governing process Correction'
    Reject 'unsupported contract' {$script:recovery.contract=Bound "$target/TASK.md"} 'Unsupported recovery contract'
    Reject 'missing adoption' {$script:recovery.adoption_event='Tasks/epics/FDEC-EPIC-S001/events/absent.md'} 'Missing recovery adoption event'
    Reject 'invalid adoption hash' {Write-Recovery;Put $adoptionPath ([IO.File]::ReadAllText("$fixture/$adoptionPath").Replace((Bound $recoveryPath).sha256,('0'*64)))} 'Invalid recovery adoption binding' -NoWrite
    Reject 'duplicate recovery' {Write-Recovery;$second=$script:recovery|ConvertTo-Json -Depth 20|ConvertFrom-Json;$second.recovery_id='FDEC-901-R002';Json 'Tasks/request-recoveries/FDEC-901-R002.json' $second} 'duplicate recovered request'
    Reject 'unsupported record file' {Put 'Tasks/request-recoveries/extra.txt' 'Not a supported recovery'} 'Unsupported recovery record file'
    Reject 'duplicate original request identity' {Json 'Tasks/version-requests/duplicate.json' $script:original} 'duplicate version request'
    Reject 'ambiguous JSON keys' {Write-Recovery;Put $recoveryPath ([IO.File]::ReadAllText("$fixture/$recoveryPath").Replace('"schema":','"schema":"fdec-rejected-request-recovery/v1", "schema":'))} 'Duplicate or invalid request JSON key' -NoWrite
    Reject 'escaped duplicate JSON keys' {Write-Recovery;Put $recoveryPath ([IO.File]::ReadAllText("$fixture/$recoveryPath").Replace('"schema":','"\u0073chema":"fdec-rejected-request-recovery/v1", "schema":'))} 'Duplicate or invalid request JSON key' -NoWrite
    Reject 'duplicate work-item identity' {$copy=$script:original.Clone();$copy.request_id='another-id';Json 'Tasks/version-requests/duplicate.json' $copy} 'Invalid closed item request'
    Reject 'unsupported recovery schema' {$script:recovery.schema='unsupported/v2'} 'Invalid recovery identity'
    Reject 'changed first proof with rebound hash' {$copy=Get-Content "$fixture/$target/evidence/closure.json" -Raw|ConvertFrom-Json;$copy.task_sha256='0'*64;Json "$target/evidence/closure.json" $copy;$script:recovery.closure_proof=Bound "$target/evidence/closure.json"} 'does not bind first closure proof'
    Reject 'valid request cannot be rewritten' {$valid=$script:original.Clone();$valid.type='correction_closed';Json $requestPath $valid;$script:recovery.request=Bound $requestPath} 'cannot rewrite a valid request'
    Reject 'rebound changed summary' {$changed=$script:original.Clone();$changed.summary='Substituted';Json $requestPath $changed;$script:recovery.request=Bound $requestPath} 'source bytes changed'
    Reject 'wrong parent still rejects' {$changed=$script:original.Clone();$changed.epic_id='FDEC-EPIC-S001';Json $requestPath $changed;$script:recovery.request=Bound $requestPath} 'Immutable record changed|source bytes changed' -Full
    Reject 'foreign evidence still rejects' {$changed=$script:original.Clone();$changed.verification=@('.gitattributes');Json $requestPath $changed;$script:recovery.request=Bound $requestPath} 'Immutable record changed|source bytes changed' -Full
    # An actual allocated-state blob at the request's first appearance rejects,
    # even if the local rejection attestation falsely says unallocated.
    Reset-Case;Assert-Owned
    git -C $fixture reset --hard --quiet $script:candidate
    git -C $fixture clean -fd --quiet
    git -C $fixture checkout $script:badSource -- $requestPath "$target/events/done.md" "$target/evidence/closure.json" "$target/evidence/pass.md"
    Json 'Tasks/version.json' @{synthetic_allocated_state=$true}
    Commit 'request first appears with allocated state'
    $script:recovery=$script:pristine|ConvertFrom-Json
    $script:recovery.source_sha=git -C $fixture rev-parse HEAD
    $copy=$script:rejection.Clone();$copy.source_sha=$script:recovery.source_sha
    Json $rejectionPath $copy;$script:recovery.rejection=Bound $rejectionPath;Write-Recovery
    $failed=$false
    try {$null=Resolve-Fixture} catch {if($_.Exception.Message -match 'with allocated state'){$failed=$true}else{throw}}
    if(!$failed){throw 'Allocated source was recovered'}
    $script:negativeCount++;Write-Output 'PASS: reject actual source allocation state despite false local attestation'
    # A normally valid unrecovered request still validates unchanged.
    Reset-Case
    $normal=$script:original.Clone();$normal.type='correction_closed';Json $requestPath $normal
    Assert-Owned;git -C $fixture clean -fd --quiet
    Commit 'normal valid request without recovery'
    $null=& $validator -Root $fixture -AsObject
    Write-Output 'PASS: normal valid request remains valid without recovery'
    Write-Output "PASS: $script:negativeCount recovery rejection scenarios; isolated fixture cleanup follows"
} finally {
    Assert-Owned
    if(Test-Path -LiteralPath $fixture){Remove-Item -LiteralPath $fixture -Recurse -Force}
}
