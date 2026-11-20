# Pure result composition. Fixture metadata never attests actual source rights.
function Get-D002ComponentStages {
    @(
        @{name='source freeze negatives';command='powershell -NoProfile -File scripts/verification/test-d002-source.ps1';result='PASS'}
        @{name='rights and verified ingestion';command='powershell -NoProfile -File training/datasets/test-ingestion.ps1';result='PASS'}
        @{name='annotation and classification schemas';command='powershell -NoProfile -File training/labels/test-mapping.ps1';result='PASS'}
        @{name='fixture generation and independent-input boundary';command='powershell -NoProfile -File training/augmentation/test-native.ps1';result='PASS'}
        @{name='Sinabis reviewed-source preparation contract';command='powershell -NoProfile -File training/augmentation/test-sinabis.ps1';result='PASS'}
        @{name='current consent and split protection';command='powershell -NoProfile -File training/splits/test-splits.ps1';result='PASS'}
        @{name='cross-component data pipeline';command='.venv/ingestion/Scripts/python.exe -m unittest discover -s tests/d002 -p test_pipeline.py -v';result='PASS'}
        @{name='unchanged Rust classification contract';command='cargo test --locked --offline -p fdemailclassifier-core schema';result='PASS'}
    )
}
function New-D002CurrentResult($Outcome,$Component,[hashtable]$Expected,$RunnerBindings) {
    foreach($key in 'candidate_sha','candidate_tree','policy_sha256','source_state_sha256'){
        $pattern=if($key -in 'candidate_sha','candidate_tree'){'^[a-f0-9]{40}$'}else{'^[a-f0-9]{64}$'}
        if($Expected[$key] -cnotmatch $pattern){throw 'Invalid expected current-gate identity'}
    }
    if(!$Outcome -or $Outcome.schema -cne 'fdec-outcome-verification/v2' -or $Outcome.task_id -cne 'FDEC-099' -or $Outcome.result -cne 'PASS'){throw 'Invalid current outcome result'}
    foreach($key in 'historical_worktree_removed','original_request_unchanged','independent_review_required'){
        if($Outcome.$key -isnot [bool] -or $Outcome.$key -ne $true){throw 'Missing current outcome boundary'}
    }
    if($Outcome.actual_data_admitted -isnot [bool] -or $Outcome.actual_data_admitted -ne $false -or $Outcome.current_protected_files -ne 102 -or $Outcome.accepted_process_changes -ne 12 -or $Outcome.continuity_negative_checks -ne 23){throw 'Unsupported current outcome claim'}
    $historical=$Outcome.historical_replay
    if($Outcome.historical_replay_source -cne '16e293aadc15f8dd50fac44720a7949e788c9eff' -or $historical.schema -cne 'fdec-outcome-verification/v1' -or $historical.task_id -cne 'FDEC-099' -or $historical.result -cne 'PASS' -or $historical.preserved_files -ne 100 -or $historical.negative_checks -ne 14){throw 'Invalid historical outcome replay'}
    if($historical.actual_training_data_admitted -isnot [bool] -or $historical.actual_training_data_admitted -ne $false -or $historical.semantic_independent_review_required -isnot [bool] -or !$historical.semantic_independent_review_required -or $historical.mutations -isnot [bool] -or $historical.mutations){throw 'Unsupported historical outcome claim'}
    foreach($pair in @(@('schema','fdec-gate-result/v1'),@('task_id','FDEC-013'),@('epic_id','FDEC-EPIC-D002'),@('result','PASS'))){if($Component.($pair[0]) -cne $pair[1]){throw 'Invalid component gate identity or result'}}
    if($Component.exit_code -isnot [int] -or $Component.exit_code -ne 0){throw 'Failed component gate'}
    foreach($key in $Expected.Keys){if($Component.$key -cne $Expected[$key]){throw 'Component gate source mismatch'}}
    foreach($key in 'actual_training_performed','model_release_approved'){if($Component.$key -isnot [bool] -or $Component.$key -ne $false){throw 'Unsupported component training or release claim'}}
    if($Component.actual_dataset_train_test_admission -cne 'not_verified_by_this_gate'){throw 'Unsupported component corpus claim'}
    $expectedStages=@(Get-D002ComponentStages)
    if(@($Component.stages).Count -ne $expectedStages.Count){throw 'Incomplete component stages'}
    for($i=0;$i -lt $expectedStages.Count;$i++){
        foreach($key in 'name','command','result'){if($Component.stages[$i].$key -cne $expectedStages[$i][$key]){throw 'Changed component stage contract'}}
    }
    $expectedPaths=@('docs/verification/run-d002-current.ps1','docs/verification/d002-current-result.ps1','scripts/verification/D002.ps1','docs/verification/verify-d002-outcome-v2.ps1')
    $seen=@()
    foreach($entry in $RunnerBindings){if($entry.path -cnotin $expectedPaths -or $seen -ccontains $entry.path -or $entry.sha256 -cnotmatch '^[a-f0-9]{64}$'){throw 'Invalid current-gate runner binding'};$seen+=@($entry.path)}
    if($seen.Count -ne $expectedPaths.Count){throw 'Incomplete current-gate runner bindings'}
    return [ordered]@{
        schema='fdec-gate-result/v1';task_id='FDEC-013';epic_id='FDEC-EPIC-D002'
        candidate_sha=$Expected.candidate_sha;candidate_tree=$Expected.candidate_tree;policy_sha256=$Expected.policy_sha256;source_state_sha256=$Expected.source_state_sha256
        result='PASS';exit_code=0
        stages=@(@{name='effective outcome and audited source continuity';command='powershell -NoProfile -File docs/verification/verify-d002-outcome-v2.ps1 -TestNegatives';result='PASS'})+@($Component.stages)
        scope='D002 current software integration plus explicit outcome/source continuity; no actual corpus or model admission'
        actual_training_performed=$false;actual_dataset_train_test_admission='not_verified_by_this_gate';model_release_approved=$false
        outcome_verification=$Outcome;component_gate_result=$Component;runner_bindings=@($RunnerBindings)
    }
}
