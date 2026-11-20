param([Parameter(Mandatory=$true)][string]$Log)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
. "$root/scripts/validate_tasks/identity.ps1"
Set-Location $root
foreach($name in 'test-output-v2.txt','result-v2.json'){if(Test-Path (Join-Path $PSScriptRoot $name)){throw 'Gate evidence is append-only'}}
$text=[IO.File]::ReadAllText($Log)
$objects=[regex]::Matches($text,'(?ms)^GATE_RESULT_BEGIN\r?\n(.*?)^GATE_RESULT_END\r?$')
if($objects.Count -ne 1 -or [regex]::Matches($text,'(?m)^COMPONENT_GATE_RESULT_BEGIN\r?$').Count -ne 1){throw 'Missing unique current/component gate markers'}
$result=$objects[0].Groups[1].Value|ConvertFrom-Json
$ready=Get-Content "$PSScriptRoot/frozen-readiness-v5.json" -Raw|ConvertFrom-Json
if($result.schema -cne 'fdec-gate-result/v1' -or $result.result -cne 'PASS' -or $result.exit_code -ne 0 -or $result.task_id -cne 'FDEC-013' -or $result.epic_id -cne 'FDEC-EPIC-D002'){throw 'Recorded result is not a current passing gate'}
$head=git rev-parse HEAD;$tree=git rev-parse 'HEAD^{tree}'
if($result.candidate_sha -cne $head -or $result.candidate_tree -cne $tree -or $result.candidate_sha -cne $ready.source_sha -or $result.source_state_sha256 -cne $ready.source_state_sha256 -or $result.policy_sha256 -cne $ready.policy_sha256){throw 'Gate output differs from frozen candidate/readiness'}
if($result.stages.Count -ne 9 -or $result.component_gate_result.stages.Count -ne 8 -or !$text.TrimEnd().EndsWith("PASS: current nine-stage D002 gate on $head")){throw 'Incomplete actual gate transcript'}
foreach($entry in $result.runner_bindings){if(!(Test-IdentityBinding $root $entry.path $entry.sha256)){throw 'Changed actual gate runner'}}
$counts=@([regex]::Matches($text,'(?m)^Ran ([0-9]+) tests')|ForEach-Object {[int]$_.Groups[1].Value})
if($counts.Count -ne 8 -or ($counts|Measure-Object -Sum).Sum -ne 139 -or !$text.Contains('test result: ok. 4 passed; 0 failed')){throw 'Missing full Python/Rust coverage in monitor log'}
$raw=(Get-FileHash -LiteralPath $Log -Algorithm SHA256).Hash.ToLowerInvariant()
$normalized=($text.Replace("`r`n","`n").Split("`n")|ForEach-Object {$_.TrimEnd()}) -join "`n"
[IO.File]::WriteAllText("$PSScriptRoot/test-output-v2.txt",($normalized.TrimEnd()+"`n"),[Text.UTF8Encoding]::new($false))
$result|Add-Member noteproperty monitor_task_id 'f870132b-9e8a-4fce-9010-01279a2c3945'
$result|Add-Member noteproperty raw_monitor_log_sha256 $raw
$result|Add-Member noteproperty transcript_normalization 'Complete monitor log retained; trailing whitespace and final blank lines removed'
$result|Add-Member noteproperty python_test_groups $counts
$result|Add-Member noteproperty python_test_count 139
$result|Add-Member noteproperty rust_test_count 4
$relative='Tasks/items/quality/FDEC-013-targeted-integration-gate/evidence'
$result|Add-Member noteproperty preflight_evidence @('preflight-v2.json','preflight-output-v2.txt'|ForEach-Object {@{path="$relative/$_";sha256=(Get-IdentityHash "$PSScriptRoot/$_")}})
$result|ConvertTo-Json -Depth 25|Set-Content -LiteralPath "$PSScriptRoot/result-v2.json" -Encoding UTF8
Write-Output 'PASS: actual nine-stage current gate, eight-stage component, full log, frozen bindings and 139 Python/four Rust tests preserved'
