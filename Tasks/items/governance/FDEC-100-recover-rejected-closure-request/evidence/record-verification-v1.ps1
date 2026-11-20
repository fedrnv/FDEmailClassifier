$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
. "$root/scripts/validate_tasks/identity.ps1"
Set-Location $root
$source='406e0121fae75e6c0623bf331d11e8e4d8aeccd1'
if((git rev-parse HEAD) -cne $source){throw 'Wrong verification source'}
foreach($name in 'test-output-v1.txt','result-v1.json'){if(Test-Path (Join-Path $PSScriptRoot $name)){throw 'Evidence is append-only'}}
$observations=Get-Content "$PSScriptRoot/focused-observations-v1.json" -Raw|ConvertFrom-Json
if($observations.Count -ne 7){throw 'Incomplete focused observations'}
$first=[IO.File]::ReadAllText("$PSScriptRoot/first-verification-output-v1.txt")
$boundary=$first.IndexOf('STAGE: test-source-readiness.ps1')
if($boundary -lt 0){throw 'Missing original stage boundary'}
$prefix=$first.Substring(0,$boundary)
foreach($stage in 'test-request-recovery.ps1','check-adoption.ps1','test-validation.ps1'){
    if([regex]::Matches($prefix,('(?m)^STAGE: '+[regex]::Escape($stage)+'\r?$')).Count -ne 1){throw 'Invalid original passing-stage prefix'}
}
foreach($marker in 'PASS: 32 recovery rejection scenarios','PASS: all five actions reject missing readiness and tampered baseline','PASS: all action entrypoints, stale source, immutable history, dependency readiness, scoped rules, active Epics, requests and hosted boundary'){
    if(!$prefix.Contains($marker)){throw 'Missing actual earlier stage result'}
}
$combined=[Text.StringBuilder]::new()
$null=$combined.AppendLine('Prior successful components at 6cab0e941f63b00457715f55a1109415a113fbc5; the full original run FAILED in its next stage and is preserved separately.')
$null=$combined.AppendLine($prefix.TrimEnd())
$runs=@()
foreach($observation in $observations){
    if($observation.status -cne 'completed' -or $observation.exit_code -ne 0 -or $observation.log_truncated){throw 'Focused command did not pass with complete output'}
    $text=if($observation.log_file){[IO.File]::ReadAllText($observation.log_file)}else{$observation.output}
    if(!$text.Contains("STAGE: $($observation.stage); SOURCE: $source")){throw 'Log belongs to another command'}
    $matches=[regex]::Matches($text,'(?s)\{\s*"schema":\s*"fdec-focused-process-verification/v1".*?\r?\n\}')
    if($matches.Count -ne 1){throw 'Missing unique typed focused result'}
    $result=$matches[0].Value|ConvertFrom-Json
    if($result.result -cne 'PASS' -or $result.source_sha -cne $source -or $result.stage -cne $observation.stage -or $result.original_request_raw_sha256 -cne '46d15301e74ec77de2bc0dc2fb2a6aa38ecd1e7db29277f871a42651e1e5611f'){throw 'Focused result identity mismatch'}
    if((Get-FileHash 'Tasks/version-requests/FDEC-099.json' -Algorithm SHA256).Hash.ToLowerInvariant() -cne $result.original_request_raw_sha256){throw 'Original request bytes changed'}
    $null=$combined.AppendLine("`nFocused command monitor $($observation.task_id), source $source")
    $null=$combined.AppendLine($text.TrimEnd())
    $runs+=@{stage=$observation.stage;monitor_task_id=$observation.task_id;result=$result;raw_monitor_log_sha256=$(if($observation.log_file){(Get-FileHash $observation.log_file -Algorithm SHA256).Hash.ToLowerInvariant()}else{$null})}
}
$output=($combined.ToString().Replace("`r`n","`n").Split("`n")|ForEach-Object {$_.TrimEnd()}) -join "`n"
[IO.File]::WriteAllText("$PSScriptRoot/test-output-v1.txt",($output.TrimEnd()+"`n"),[Text.UTF8Encoding]::new($false))
$refs=@('Tasks/request-recoveries/FDEC-099-R001.json','Tasks/policy/rejected-request-recovery-1.0.md','Tasks/version-requests/FDEC-099.json','scripts/validate_tasks/request-recovery.ps1','scripts/validate_tasks/repository.ps1','docs/verification/rejected-request-recovery.md')
@{schema='fdec-correction-result/v1';task_id='FDEC-100';epic_id='FDEC-EPIC-S001';result='PASS';source_sha=$source;policy_sha256=(Get-Content 'Tasks/policy/adoption-5.6.json' -Raw|ConvertFrom-Json).policy_sha256;negative_recovery_cases=32;repository_records=114;prior_component_source='6cab0e941f63b00457715f55a1109415a113fbc5';prior_component_monitor='462f6519-8ede-4c68-a331-e1c42668ee0b';prior_component_stages=@('test-request-recovery.ps1','check-adoption.ps1','test-validation.ps1');prior_full_run_result='FAIL: inherited source-readiness fixture, corrected in the current source';focused_runs=$runs;coverage='Ten selected stages, three unchanged implementation stages attributed to their earlier passing component executions and seven focused stages on current source; not a fictional all-green original run';original_request_canonical_sha256=(Get-IdentityHash 'Tasks/version-requests/FDEC-099.json');original_request_raw_sha256=(Get-FileHash 'Tasks/version-requests/FDEC-099.json' -Algorithm SHA256).Hash.ToLowerInvariant();actual_training_performed=$false;allocated=$false;published=$false;artifacts=@($refs|ForEach-Object {@{path=$_;sha256=(Get-IdentityHash $_)}})}|ConvertTo-Json -Depth 20|Set-Content -LiteralPath "$PSScriptRoot/result-v1.json" -Encoding UTF8
Write-Output 'PASS: actual complete outputs and per-source component attribution preserved; original request raw bytes unchanged'
