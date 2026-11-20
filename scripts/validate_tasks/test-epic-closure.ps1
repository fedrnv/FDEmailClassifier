$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/identity.ps1"
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-epic-'+[guid]::NewGuid())
$epic='Tasks/epics/FDEC-EPIC-D001'
$gate='Tasks/items/quality/FDEC-902-gate'
$review='Tasks/items/quality/FDEC-903-review'
$functional='Tasks/items/foundation/FDEC-901-functional'
function Put([string]$Path,[string]$Text){$full=Join-Path $temp $Path;$null=New-Item -ItemType Directory (Split-Path $full) -Force;[IO.File]::WriteAllText($full,$Text,[Text.UTF8Encoding]::new($false))}
function Json([string]$Path,$Value){Put $Path ($Value|ConvertTo-Json -Depth 30)}
function Bound([string]$Path){@{path=$Path;sha256=(Get-IdentityHash (Join-Path $temp $Path))}}
function Event($Directory,$Id,$Name,$Transition,$Extra=''){
    Put "$Directory/events/$Name.md" @"
---
schema: fdtasks-event/v3
event_id: fixture-$Id-$Name
task_id: $Id
event_type: status-changed
created_at: 2026-11-22T00:00:$($script:second.ToString('00'))Z
actor: fixture
base_revision: fixture
server_revision: null
$Extra
---
$Transition.
"@
    $script:second++
}
function Task($Directory,$Id,$Dependencies){Put "$Directory/TASK.md" @"
---
schema: fdtasks-spec/v3
id: $Id
title: "Synthetic $Id"
type: Task
area: quality
epic_id: FDEC-EPIC-D001
size: medium
initial_status: Planned
initial_dependencies: $Dependencies
atomicity:
  outcomes: ["One synthetic outcome"]
  packets: ["One synthetic packet"]
  independent_acceptance: false
  boundary_reason: "One fixture contract"
---
| AC-01 | Synthetic valid closure |
| AC-02 | Synthetic invalid closure |
"@}
function CloseTask($Directory,$Id,$Verification){
    $proof=@{source_sha=$script:candidate;task_sha256=(Bound "$Directory/TASK.md").sha256;verification=$Verification}
    Json "$Directory/evidence/closure.json" $proof
    Event $Directory $Id done 'Planned -> Done' "closure_proof: evidence/closure.json`nclosure_proof_sha256: $((Bound "$Directory/evidence/closure.json").sha256)"
    Json "Tasks/version-requests/$Id.json" @{schema='fdtasks-version-request/v1';request_id="request-$Id";type='task_closed';epic_id='FDEC-EPIC-D001';work_item_id=$Id;summary='Synthetic completed outcome';verification=@($Verification|ForEach-Object {$_.path})}
}
function Validate {& "$PSScriptRoot/repository.ps1" -Root $temp}
function Reject([string]$Label,[scriptblock]$Change,[string]$Pattern){
    & $Change
    $failed=$false
    try {Validate} catch {if($_.Exception.Message -match $Pattern){$failed=$true}else{throw}}
    if(!$failed){throw "Expected rejection: $Label"}
    Write-Output "PASS: reject $Label"
    # Every case resets only this owned disposable fixture to its exact baseline.
    git -C $temp reset --hard --quiet $script:ledger
    if($LASTEXITCODE -ne 0){throw 'Fixture reset failed'}
    $owned=[IO.Path]::GetFullPath($temp)
    if(!$owned.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()),[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $owned -Leaf).StartsWith('fdec-epic-')){throw 'Unsafe fixture clean'}
    git -C $temp clean -fd --quiet
    if($LASTEXITCODE -ne 0){throw 'Fixture clean failed'}
    WriteClosure
}
function WriteClosure {
    Json "$epic/evidence/closure.json" $script:proof
    Put "$epic/evidence/verification.md" 'Synthetic Epic acceptance evidence.'
    $hash=(Bound "$epic/evidence/closure.json").sha256
    $script:second=30
    Event $epic FDEC-EPIC-D001 closed 'Active -> Done' "closure_proof: evidence/closure.json`nclosure_proof_sha256: $hash"
    Json 'Tasks/version-requests/FDEC-EPIC-D001.json' $script:request
}
function ChangeProof([scriptblock]$Change){$copy=$script:proof|ConvertTo-Json -Depth 30|ConvertFrom-Json;& $Change $copy;Json "$epic/evidence/closure.json" $copy;Event $epic FDEC-EPIC-D001 closed 'Active -> Done' "closure_proof: evidence/closure.json`nclosure_proof_sha256: $((Bound "$epic/evidence/closure.json").sha256)"}
function GateVariant([scriptblock]$Change){
    $result=Get-Content "$temp/$gate/evidence/result.json" -Raw|ConvertFrom-Json
    & $Change $result
    Json "$gate/evidence/repeated-result.json" $result
    $ready=Get-Content "$temp/$gate/evidence/closure.json" -Raw|ConvertFrom-Json
    $ready.verification=@((Bound "$gate/evidence/repeated-result.json"))
    Json "$gate/evidence/repeated-closure.json" $ready
    $script:second=20
    Event $gate FDEC-902 reopen 'Done -> Planned'
    Event $gate FDEC-902 repeated 'Planned -> Done' "closure_proof: evidence/repeated-closure.json`nclosure_proof_sha256: $((Bound "$gate/evidence/repeated-closure.json").sha256)"
    Event $review FDEC-903 reopen 'Done -> Planned'
    Event $review FDEC-903 repeated 'Planned -> Done' "closure_proof: evidence/closure.json`nclosure_proof_sha256: $((Bound "$review/evidence/closure.json").sha256)"
    ChangeProof {
        param($p)
        $p.gate_result=Bound "$gate/evidence/repeated-result.json"
        foreach($pair in @(@('FDEC-902',$gate),@('FDEC-903',$review))){
            $member=@($p.members|Where-Object id -EQ $pair[0])[0]
            $member.state=@((Bound "$($pair[1])/TASK.md")) + @(Get-ChildItem "$temp/$($pair[1])/events" -File|ForEach-Object {Bound $_.FullName.Substring($temp.Length+1).Replace('\','/')})
        }
    }
}
try {
    $null=New-Item -ItemType Directory $temp
    Put '.gitattributes' '* text=auto eol=lf'
    Put 'implementation.txt' 'Synthetic frozen implementation.'
    foreach($special in 'S001','S002'){Put "Tasks/epics/FDEC-EPIC-$special/EPIC.md" "---`nschema: fdtasks-epic/v4`nid: FDEC-EPIC-$special`ninitial_status: Active`ninitial_dependencies: []`n---`nPermanent synthetic process area.`n"}
    Put "$epic/EPIC.md" "---`nschema: fdtasks-epic/v4`nid: FDEC-EPIC-D001`ninitial_status: Active`ninitial_dependencies: []`n---`n- FDEC-901`n- FDEC-902`n- FDEC-903`n"
    Task $functional FDEC-901 '[]';Task $gate FDEC-902 '[FDEC-901]';Task $review FDEC-903 '[FDEC-902]'
    Put 'Tasks/policy/upstream-5.6.md' 'Synthetic pinned policy for disposable validator tests only.'
    $policy=(Bound 'Tasks/policy/upstream-5.6.md').sha256
    Json 'Tasks/policy/adoption-5.6.json' @{policy_sha256=$policy}
    git -C $temp init --quiet
    git -C $temp add .
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m candidate
    if($LASTEXITCODE -ne 0){throw 'Fixture baseline failed'}
    $script:candidate=git -C $temp rev-parse HEAD;$tree=git -C $temp rev-parse 'HEAD^{tree}'
    $script:second=0
    Put "$functional/evidence/pass.md" 'Synthetic PASS.'
    CloseTask $functional FDEC-901 @((Bound "$functional/evidence/pass.md"))
    Json "$gate/evidence/result.json" @{schema='fdec-gate-result/v1';task_id='FDEC-902';epic_id='FDEC-EPIC-D001';result='PASS';exit_code=0;candidate_sha=$script:candidate;candidate_tree=$tree;policy_sha256=$policy}
    CloseTask $gate FDEC-902 @((Bound "$gate/evidence/result.json"))
    $round="$epic/reviews/R001"
    $gateHash=(Bound "$gate/evidence/result.json").sha256
    $identity="review_id: R001`nreview_task_id: FDEC-903`nepic_id: FDEC-EPIC-D001`ncandidate_sha: $script:candidate`ncandidate_tree: $tree`npolicy_sha256: $policy`ngate_result_sha256: $gateHash"
    Put "$round/REQUEST.md" "---`nschema: fdec-independent-review-request/v1`n$identity`n---`nSynthetic independent request.`n"
    Put "$round/RESULT.md" "---`nschema: fdec-independent-review-result/v1`n$identity`nreviewer: independent-fixture`nresult: Accepted`n---`nSynthetic independent result; not real acceptance evidence.`n"
    Json "$review/evidence/reconciliation.json" @{schema='fdec-review-reconciliation/v1';task_id='FDEC-903';result='Accepted';candidate_sha=$script:candidate;artifacts=@((Bound "$round/RESULT.md"))}
    CloseTask $review FDEC-903 @((Bound "$review/evidence/reconciliation.json"))
    Validate
    git -C $temp add .
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m ledger
    if($LASTEXITCODE -ne 0){throw 'Fixture ledger failed'}
    $script:ledger=git -C $temp rev-parse HEAD
    Put "$epic/evidence/verification.md" 'Synthetic Epic acceptance evidence.'
    $records=& "$PSScriptRoot/repository.ps1" -Root $temp -AsObject
    $script:proof=@{schema='fdec-epic-closure/v1';epic_id='FDEC-EPIC-D001';source_sha=$script:ledger;candidate_sha=$script:candidate;candidate_tree=$tree;policy_sha256=$policy;gate_task_id='FDEC-902';review_task_id='FDEC-903';gate_result=(Bound "$gate/evidence/result.json");review_result=(Bound "$round/RESULT.md");epic_state=@($records['FDEC-EPIC-D001'].state_paths|ForEach-Object {Bound $_.Substring($temp.Length+1).Replace('\','/')});members=@($records['FDEC-EPIC-D001'].members|ForEach-Object {$id=$_;@{id=$id;state=@($records[$id].state_paths|ForEach-Object {Bound $_.Substring($temp.Length+1).Replace('\','/')})}});verification=@((Bound "$epic/evidence/verification.md"))}
    $script:request=@{schema='fdtasks-version-request/v1';request_id='epic-request';type='epic_closed';epic_id='FDEC-EPIC-D001';work_item_id='FDEC-EPIC-D001';summary='Synthetic completed Epic';verification=@("$epic/evidence/verification.md")}
    WriteClosure
    Validate
    Write-Output 'PASS: valid development Epic first closure and request admitted without allocation'
    Reject 'missing request' {Remove-Item -LiteralPath "$temp/Tasks/version-requests/FDEC-EPIC-D001.json"} 'Missing verified Epic closure request'
    Reject 'never-closed Epic' {Remove-Item -LiteralPath "$temp/$epic/events/closed.md"} 'Invalid development Epic closure request'
    Reject 'special Epic' {$copy=$script:request.Clone();$copy.epic_id='FDEC-EPIC-S001';$copy.work_item_id='FDEC-EPIC-S001';Json 'Tasks/version-requests/FDEC-EPIC-D001.json' $copy} 'Invalid development Epic closure request'
    Reject 'duplicate identity' {Json 'Tasks/version-requests/duplicate.json' $script:request} 'duplicate version request|Invalid closed item request'
    Reject 'missing member request' {Remove-Item -LiteralPath "$temp/Tasks/version-requests/FDEC-901.json"} 'Immutable record changed|Epic member lacks'
    Reject 'omitted member' {ChangeProof {param($p)$p.members=@($p.members|Where-Object id -NE FDEC-901)}} 'Incomplete Epic closure membership'
    Reject 'unfinished member' {$script:second=20;Event $functional FDEC-901 reopen 'Done -> Planned'} 'Epic member is not Done'
    Reject 'duplicate member' {ChangeProof {param($p)$p.members[1]=$p.members[0]}} 'Invalid Epic closure member'
    Reject 'stale snapshot' {ChangeProof {param($p)$p.members[0].state[0].sha256=('0'*64)}} 'Invalid Epic closure state binding'
    Reject 'stale source' {ChangeProof {param($p)$p.source_sha=$script:candidate}} 'Stale Epic closure source'
    Reject 'wrong candidate tree' {ChangeProof {param($p)$p.candidate_tree=('0'*40)}} 'Invalid or mismatched passing gate'
    Reject 'wrong gate identity' {ChangeProof {param($p)$p.gate_task_id='FDEC-901'}} 'Invalid Epic gate/review topology'
    Reject 'tampered Epic evidence' {Put "$epic/evidence/verification.md" 'Changed'} 'Invalid Epic closure artifact binding'
    Reject 'foreign verification' {$copy=$script:request.Clone();$copy.verification=@('implementation.txt');Json 'Tasks/version-requests/FDEC-EPIC-D001.json' $copy} 'Unverified Epic closure evidence'
    Reject 'gate mismatch' {ChangeProof {param($p)$p.gate_result.sha256=('0'*64)}} 'Invalid Epic closure artifact binding'
    Reject 'failed latest gate' {GateVariant {param($r)$r.result='FAIL';$r.exit_code=1}} 'Invalid or mismatched passing gate'
    Reject 'gate candidate mismatch' {GateVariant {param($r)$r.candidate_sha=('0'*40)}} 'Invalid or mismatched passing gate'
    Reject 'review mismatch' {ChangeProof {param($p)$p.review_result.sha256=('0'*64)}} 'Invalid Epic closure artifact binding'
    Reject 'unfinished new review round' {Put "$epic/reviews/R002/REQUEST.md" "---`n$identity`n---`nNew request without result."} 'Review is not the latest requested round'
    Reject 'ChangesRequired review' {
        $newIdentity=$identity.Replace('R001','R002')
        Put "$epic/reviews/R002/REQUEST.md" "---`nschema: fdec-independent-review-request/v1`n$newIdentity`n---`nSynthetic new request."
        Put "$epic/reviews/R002/RESULT.md" "---`nschema: fdec-independent-review-result/v1`n$newIdentity`nreviewer: independent-fixture`nresult: ChangesRequired`n---`nSynthetic rejected review."
        ChangeProof {param($p)$p.review_result=Bound "$epic/reviews/R002/RESULT.md"}
    } 'Independent review is not Accepted'
    Reject 'ambiguous independent decision' {
        $newIdentity=$identity.Replace('R001','R002')
        Put "$epic/reviews/R002/REQUEST.md" "---`nschema: fdec-independent-review-request/v1`n$newIdentity`n---`nSynthetic new request."
        Put "$epic/reviews/R002/RESULT.md" "---`nschema: fdec-independent-review-result/v1`n$newIdentity`nreviewer: independent-fixture`nresult: Accepted`nresult: ChangesRequired`n---`nAmbiguous decision."
        ChangeProof {param($p)$p.review_result=Bound "$epic/reviews/R002/RESULT.md"}
    } 'Missing or ambiguous Epic field: result'
    Reject 'invalid review schema' {
        $newIdentity=$identity.Replace('R001','R002')
        Put "$epic/reviews/R002/REQUEST.md" "---`nschema: fdec-independent-review-request/v1`n$newIdentity`n---`nSynthetic new request."
        Put "$epic/reviews/R002/RESULT.md" "---`nschema: unknown/v1`n$newIdentity`nreviewer: independent-fixture`nresult: Accepted`n---`nInvalid schema."
        ChangeProof {param($p)$p.review_result=Bound "$epic/reviews/R002/RESULT.md"}
    } 'Invalid independent review schema'
    Reject 'changed tracked implementation' {Put 'implementation.txt' 'Changed after passing gate'} 'Implementation differs from passing candidate'
    Reject 'new implementation' {Put 'new-source.rs' 'New code after passing gate'} 'Implementation differs from passing candidate'
    Reject 'staged implementation' {Put 'implementation.txt' 'Staged change';git -C $temp add implementation.txt} 'Implementation differs from passing candidate'
    Reject 'release allocation request' {$copy=$script:request.Clone();$copy.type='release_published';Json 'Tasks/version-requests/FDEC-EPIC-D001.json' $copy} 'Release/major requests require'
    # Accepted immutable request survives later reopen and reclose; its proof is
    # evaluated at the first closure, not against today's mutable projection.
    Validate
    git -C $temp add .
    git -C $temp -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m close
    if($LASTEXITCODE -ne 0){throw 'Closure baseline failed'}
    $before=(Get-FileHash "$temp/Tasks/version-requests/FDEC-EPIC-D001.json").Hash
    $script:second=40
    Event $epic FDEC-EPIC-D001 reopen 'Done -> Active'
    Event $functional FDEC-901 reopen 'Done -> Planned'
    Put 'implementation.txt' 'Later authorized work does not rewrite historical closure.'
    Validate
    Event $functional FDEC-901 reclose 'Planned -> Done'
    Event $epic FDEC-EPIC-D001 reclose 'Active -> Done'
    $failed=$false
    try {Validate} catch {if($_.Exception.Message -match 'Missing or ambiguous Epic field: closure_proof'){$failed=$true}else{throw}}
    if(!$failed){throw 'Reclosure reused historical acceptance without new proof'}
    Remove-Item -LiteralPath "$temp/$epic/events/reclose.md"
    Put 'implementation.txt' 'Synthetic frozen implementation.'
    $records=& "$PSScriptRoot/repository.ps1" -Root $temp -AsObject
    $reproof=$script:proof.Clone();$reproof.source_sha=git -C $temp rev-parse HEAD
    $reproof.epic_state=@($records['FDEC-EPIC-D001'].state_paths|ForEach-Object {Bound $_.Substring($temp.Length+1).Replace('\','/')})
    $reproof.members=@($records['FDEC-EPIC-D001'].members|ForEach-Object {$id=$_;@{id=$id;state=@($records[$id].state_paths|ForEach-Object {Bound $_.Substring($temp.Length+1).Replace('\','/')})}})
    Json "$epic/evidence/reclosure.json" $reproof
    Event $epic FDEC-EPIC-D001 reclose 'Active -> Done' "closure_proof: evidence/reclosure.json`nclosure_proof_sha256: $((Bound "$epic/evidence/reclosure.json").sha256)"
    Validate
    if((Get-FileHash "$temp/Tasks/version-requests/FDEC-EPIC-D001.json").Hash -ne $before){throw 'Historical request changed'}
    if(Test-Path "$temp/Tasks/version.json"){throw 'Validator allocated a version'}
    Write-Output 'PASS: Epic reopen/reclose retains first request; reclosure needs current proof; no versions allocated'
} finally {
    $resolved=[IO.Path]::GetFullPath($temp);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-epic-')){throw 'Unsafe cleanup target'}
    if(Test-Path $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
