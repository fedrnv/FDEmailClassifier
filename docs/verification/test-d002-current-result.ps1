# Counterfactual metadata only; no actual gate acceptance, source grant or model.
$ErrorActionPreference='Stop'
. "$PSScriptRoot/d002-current-result.ps1"
$expected=@{candidate_sha='1'*40;candidate_tree='2'*40;policy_sha256='3'*64;source_state_sha256='4'*64}
$component=[ordered]@{schema='fdec-gate-result/v1';task_id='FDEC-013';epic_id='FDEC-EPIC-D002';candidate_sha=$expected.candidate_sha;candidate_tree=$expected.candidate_tree;policy_sha256=$expected.policy_sha256;source_state_sha256=$expected.source_state_sha256;result='PASS';exit_code=0;stages=@(Get-D002ComponentStages);actual_training_performed=$false;actual_dataset_train_test_admission='not_verified_by_this_gate';model_release_approved=$false}
$outcome=@{schema='fdec-outcome-verification/v2';task_id='FDEC-099';result='PASS';current_protected_files=102;accepted_process_changes=12;continuity_negative_checks=23;historical_replay_source='16e293aadc15f8dd50fac44720a7949e788c9eff';historical_replay=@{schema='fdec-outcome-verification/v1';task_id='FDEC-099';result='PASS';preserved_files=100;negative_checks=14;actual_training_data_admitted=$false;semantic_independent_review_required=$true;mutations=$false};historical_worktree_removed=$true;original_request_unchanged=$true;actual_data_admitted=$false;independent_review_required=$true}
$bindings=@('docs/verification/run-d002-current.ps1','docs/verification/d002-current-result.ps1','scripts/verification/D002.ps1','docs/verification/verify-d002-outcome-v2.ps1'|ForEach-Object {@{path=$_;sha256='5'*64}})
$before=@($outcome,$component,$expected,$bindings)|ConvertTo-Json -Depth 20 -Compress
$positive=New-D002CurrentResult ($outcome|ConvertTo-Json -Depth 15|ConvertFrom-Json) ($component|ConvertTo-Json -Depth 15|ConvertFrom-Json) $expected $bindings
if($positive.stages.Count -ne 9 -or $positive.component_gate_result.stages.Count -ne 8){throw 'Composition lost or duplicated stages'}
if((@($outcome,$component,$expected,$bindings)|ConvertTo-Json -Depth 20 -Compress) -cne $before){throw 'Result composition mutated inputs'}
$script:negativeCount=0
function Reject([string]$Label,[scriptblock]$Change){
    $o=$outcome|ConvertTo-Json -Depth 15|ConvertFrom-Json;$c=$component|ConvertTo-Json -Depth 15|ConvertFrom-Json
    $e=$expected.Clone();$b=($bindings|ConvertTo-Json -Depth 5|ConvertFrom-Json)
    & $Change $o $c $e $b
    $failed=$false
    try {$null=New-D002CurrentResult $o $c $e $b} catch {$failed=$true}
    if(!$failed){throw "Invalid result composed: $Label"}
    $script:negativeCount++;Write-Output "PASS: reject $Label"
}
Reject 'failed outcome' {$args[0].result='FAIL'}
Reject 'unknown outcome schema' {$args[0].schema='unknown/v9'}
Reject 'actual source admission' {$args[0].actual_data_admitted=$true}
Reject 'incomplete historical cleanup' {$args[0].historical_worktree_removed=$false}
Reject 'request rewrite' {$args[0].original_request_unchanged=$false}
Reject 'missing independent review boundary' {$args[0].independent_review_required=$false}
Reject 'omitted outcome negatives' {$args[0].continuity_negative_checks=0}
Reject 'wrong historical source' {$args[0].historical_replay_source='f'*40}
Reject 'omitted historical negatives' {$args[0].historical_replay.negative_checks=0}
Reject 'unknown component schema' {$args[1].schema='unknown/v9'}
Reject 'wrong candidate' {$args[1].candidate_sha='f'*40}
Reject 'wrong candidate tree' {$args[1].candidate_tree='f'*40}
Reject 'wrong policy' {$args[1].policy_sha256='f'*64}
Reject 'wrong frozen source state' {$args[1].source_state_sha256='f'*64}
Reject 'failed component decision' {$args[1].result='FAIL'}
Reject 'nonzero component exit' {$args[1].exit_code=1}
Reject 'missing component stage' {$args[1].stages=@($args[1].stages|Select-Object -Skip 1)}
Reject 'duplicate component stage' {$args[1].stages[0]=$args[1].stages[1]}
Reject 'substituted stage command' {$args[1].stages[0].command='unverified-command'}
Reject 'actual training claim' {$args[1].actual_training_performed=$true}
Reject 'model release claim' {$args[1].model_release_approved=$true}
Reject 'actual corpus claim' {$args[1].actual_dataset_train_test_admission='verified'}
Reject 'invalid runner hash' {$args[3][0].sha256='invalid'}
Reject 'duplicate runner identity' {$args[3][0].path=$args[3][1].path}
Reject 'unsupported runner path' {$args[3][0].path='other.ps1'}
Reject 'invalid expected source' {$args[2].candidate_sha='short'}
Write-Output "PASS: immutable nine-stage metadata composition and $script:negativeCount rejection scenarios; no actual source/model grant"
