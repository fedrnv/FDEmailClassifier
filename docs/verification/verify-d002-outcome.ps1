param([switch]$TestNegatives)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$root/scripts/validate_tasks/identity.ps1"
$relative='Tasks/epics/FDEC-EPIC-D002/evidence/effective-outcome-v1.json'
$baseline='0bcd4c4f377af86ee8b83d1d0bf770f0eb448ad8'
$original='Produce provenance-tracked, lawful, reproducible training/evaluation data without publishing copyrighted/private corpora.'
$effective='Deliver provenance-tracked, rights-gated reproducible preprocessing, annotation mapping, fixture generation and grouped split/consent software, plus conditional independently sourced preparation, without claiming an admitted training/evaluation corpus.'
$required=@('independent_permitted_annotation','quality_evaluation','current_source_consent_and_split_integration','training_task_admission','whole_thread_duplicate_family_separation','model_specific_training_and_distribution_rights','actual_held_out_evaluation','operator_release_authorization')
$taskPaths=@('Tasks/items/ai/FDEC-015-zero-shot-baseline/TASK.md','Tasks/items/ai/FDEC-016-lora-qlora-trainer/TASK.md','Tasks/items/ai/FDEC-017-multi-label-evaluation-suite/TASK.md','Tasks/items/ai/FDEC-019-model-export-and-provenance/TASK.md','Tasks/items/quality/FDEC-020-targeted-integration-gate/TASK.md','Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/TASK.md')
$evidencePaths=@('Tasks/items/ai/FDEC-011-multilingual-synthetic-augmentation/evidence/independent-data-acceptance-v2.json','Tasks/items/ai/FDEC-011-multilingual-synthetic-augmentation/evidence/sinabis-acceptance-v3.json','Tasks/items/ai/FDEC-011-multilingual-synthetic-augmentation/evidence/sinabis-final-preparation-report-v12.json','Tasks/items/quality/FDEC-013-targeted-integration-gate/evidence/result-v1.json','Tasks/epics/FDEC-EPIC-D002/reviews/R001/RESULT.md')
$evidencePaths+=@(Get-ChildItem "$root/Tasks/items/ai/FDEC-011-multilingual-synthetic-augmentation/events" -Filter '*scope-amended*' | ForEach-Object {$_.FullName.Substring($root.Length+1).Replace('\','/')})
function Invoke-OutcomeGit([string[]]$Arguments){
    $output=@(& git -C $root @Arguments)
    if($LASTEXITCODE -ne 0){throw 'Cannot inspect preserved Git source'}
    return $output
}
function SameSet($Actual,$Expected,[string]$Reason){
    $values=@($Actual)
    if($values.Count -ne @($Expected).Count -or @($values|Select-Object -Unique).Count -ne $values.Count -or @(Compare-Object $values @($Expected)).Count){throw $Reason}
}
function Bound($Entry,[string]$Expected){
    if(!$Entry -or $Entry.path -cne $Expected -or !(Test-IdentityBinding $root $Expected $Entry.sha256)){throw "Invalid bound artifact: $Expected"}
}
function Bindings($Entries,$Expected){
    SameSet @($Entries.path) $Expected 'Incomplete or duplicate proof set'
    foreach($entry in $Entries){Bound $entry $entry.path}
}
function Assert-Outcome($Value){
    if($Value.schema -cne 'fdec-epic-outcome-amendment/v1' -or $Value.epic_id -cne 'FDEC-EPIC-D002' -or $Value.correction_id -cne 'FDEC-099' -or $Value.finding_id -cne 'R001-B1'){throw 'Invalid amendment identity'}
    if($Value.original_outcome -cne $original -or $Value.effective_outcome -cne $effective -or $Value.preserved_source_sha -cne $baseline){throw 'Contradictory outcome or baseline'}
    if($Value.authority_kind -cne 'recorded_application_of_existing_owner_instructions' -or !$Value.reason -or !$Value.lifecycle){throw 'Missing authority application or lifecycle'}
    Bound $Value.authority 'Tasks/epics/FDEC-EPIC-D002/evidence/outcome-authority-v1.md'
    Bound $Value.original_epic 'Tasks/epics/FDEC-EPIC-D002/EPIC.md'
    foreach($key in 'full_project_objective_preserved','codex_packs_fixture_only'){if($Value.$key -isnot [bool] -or $Value.$key -ne $true){throw "Missing retained boundary: $key"}}
    foreach($key in 'actual_training_data_admitted','actual_training_performed','model_release_approved'){if($Value.$key -isnot [bool] -or $Value.$key -ne $false){throw "Unsupported achieved status: $key"}}
    if($Value.sinabis_10k -cne 'conditional_source_preparation_only' -or $Value.sinabis_10m -cne 'not_admitted'){throw 'Unsupported source promotion'}
    SameSet $Value.optional_enhancement_epics @('FDEC-EPIC-D011','FDEC-EPIC-D012') 'Changed optional enhancement scope'
    SameSet $Value.remaining_requirements $required 'Missing mandatory actual-data requirement'
    Bindings $Value.downstream_task_specs $taskPaths
    Bindings $Value.evidence $evidencePaths
    $report=Get-Content (Join-Path $root 'Tasks/items/ai/FDEC-011-multilingual-synthetic-augmentation/evidence/sinabis-final-preparation-report-v12.json') -Raw|ConvertFrom-Json
    if($report.training_ready -ne $false -or $report.summary.supervised_records -ne 0 -or $report.summary.independent_source_cohorts -ne 1){throw 'Preparation evidence contradicts declared unavailable data'}
}
$value=Get-Content (Join-Path $root $relative) -Raw|ConvertFrom-Json
Assert-Outcome $value
# Check the actual append-only event identity, not just a freely supplied JSON.
$events=@(Get-ChildItem "$root/Tasks/epics/FDEC-EPIC-D002/events" -Filter '*.md'|Where-Object {(Get-Content $_.FullName -Raw) -match '(?m)^outcome_file: evidence/effective-outcome-v1.json\r?$'})
if($events.Count -ne 1){throw 'Missing or ambiguous outcome event'}
$event=Get-Content $events[0].FullName -Raw
foreach($line in @('schema: fdtasks-event/v3','task_id: FDEC-EPIC-D002','event_type: scope-amended','correction_id: FDEC-099')){
    if([regex]::Matches($event,('(?m)^'+[regex]::Escape($line)+'\r?$')).Count -ne 1){throw 'Invalid scope event'}
}
$hash=[regex]::Matches($event,'(?m)^outcome_sha256: ([a-f0-9]{64})\r?$')
if($hash.Count -ne 1 -or !(Test-IdentityBinding $root $relative $hash[0].Groups[1].Value)){throw 'Scope event proof mismatch'}
$paths=@(Invoke-OutcomeGit @('ls-tree','-r','--name-only',$baseline,'--','training','scripts','schemas','.gitattributes','.gitignore'))
Bindings $value.preserved_files $paths
# Hash actual working bytes using Git's checkout normalization. Hidden index
# flags cannot conceal changes from hash-object; compare directly to the blob.
foreach($path in @($paths)+@($value.original_epic.path)){
    $expected=@(Invoke-OutcomeGit @('rev-parse',"${baseline}:$path"))[0]
    $actual=@(Invoke-OutcomeGit @('hash-object',"--path=$path",(Join-Path $root $path)))[0]
    if($actual -cne $expected){throw "Accepted source changed: $path"}
}
$negatives=0
if($TestNegatives){
    function Reject([scriptblock]$Change,[string]$Expected){
        $copy=$value|ConvertTo-Json -Depth 25|ConvertFrom-Json
        & $Change $copy
        try {Assert-Outcome $copy} catch {
            if($_.Exception.Message -notlike $Expected){throw "Unexpected negative failure: $($_.Exception.Message)"}
            $script:negatives++;return
        }
        throw 'Invalid metadata accepted'
    }
    Reject {$args[0].authority=$null} 'Invalid bound artifact:*'
    Reject {$args[0].authority.sha256='0'*64} 'Invalid bound artifact:*'
    Reject {$args[0].original_epic.sha256='0'*64} 'Invalid bound artifact:*'
    Reject {$args[0].evidence[0].sha256='0'*64} 'Invalid bound artifact:*'
    Reject {$args[0].evidence=@($args[0].evidence|Select-Object -Skip 1)} 'Incomplete or duplicate proof set'
    Reject {$args[0].remaining_requirements=@($args[0].remaining_requirements|Select-Object -Skip 1)} 'Missing mandatory actual-data requirement'
    Reject {$args[0].effective_outcome='Actual training corpus is ready'} 'Contradictory outcome or baseline'
    Reject {$args[0].actual_training_data_admitted=$true} 'Unsupported achieved status:*'
    Reject {$args[0].actual_training_performed=$true} 'Unsupported achieved status:*'
    Reject {$args[0].model_release_approved=$true} 'Unsupported achieved status:*'
    Reject {$args[0].codex_packs_fixture_only=$false} 'Missing retained boundary:*'
    Reject {$args[0].sinabis_10k='training_approved'} 'Unsupported source promotion'
    Reject {$args[0].authority_kind='new_owner_license_grant'} 'Missing authority application or lifecycle'
    Reject {$args[0].downstream_task_specs[0].path='Tasks/epics/FDEC-EPIC-D002/EPIC.md'} 'Incomplete or duplicate proof set'
}
[ordered]@{schema='fdec-outcome-verification/v1';result='PASS';task_id='FDEC-099';preserved_files=$paths.Count;negative_checks=$negatives;actual_training_data_admitted=$false;semantic_independent_review_required=$true;mutations=$false}|ConvertTo-Json
