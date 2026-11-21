$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/identity.ps1"
. "$PSScriptRoot/source-state.ps1"
. "$PSScriptRoot/readiness-events.ps1"
. "$PSScriptRoot/fixture-matrix.ps1"
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('fdec-deps-'+[guid]::NewGuid().ToString('N'))
$changePath='Tasks/dependency-amendments/FDEC-087-D001.json'
$task='Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff'
$governing='Tasks/items/governance/FDEC-101-reconcile-mlx-dependency'
$script:negativeCount=0
function Assert-Owned {
    $absolute=[IO.Path]::GetFullPath($fixture)
    $parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar
    if(!$absolute.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $absolute -Leaf) -notmatch '^fdec-deps-[a-f0-9]{32}$' -or $absolute -eq $root){throw 'Unsafe dependency fixture target'}
    if((Test-Path $absolute) -and ((Get-Item $absolute -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked dependency fixture target'}
}
function Fixture-Git([string[]]$Arguments){& git -C $fixture @Arguments;if($LASTEXITCODE -ne 0){throw 'Dependency fixture Git failed'}}
function Save-Json($path,$value){$absolute=Join-Path $fixture $path;New-Item -ItemType Directory -Force (Split-Path $absolute)|Out-Null;$value|ConvertTo-Json -Depth 40|Set-Content -LiteralPath $absolute -Encoding UTF8}
function Bound($path){@{path=$path;sha256=(Get-IdentityHash (Join-Path $fixture $path))}}
function Commit-Case {Fixture-Git @('add','--all');Fixture-Git @('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--quiet','--allow-empty','-m','dependency fixture')}
function Reset-Case {
    Assert-Owned
    Fixture-Git @('reset','--hard','--quiet',$script:baseline)
    Fixture-Git @('clean','-fd','--quiet')
    $script:change=Get-Content -LiteralPath "$fixture/$changePath" -Raw|ConvertFrom-Json
    $script:event=(Get-ChildItem "$fixture/$task/events" -Filter '*.md'|Where-Object{[IO.File]::ReadAllText($_.FullName) -match '(?m)^event_type: dependency-amended\r?$'}|Select-Object -First 1).FullName
}
function Rebind {
    Save-Json $changePath $script:change
    Rebind-Raw
}
function Rebind-Raw {
    $hash=(Bound $changePath).sha256
    foreach($path in @($script:event,(Join-Path $fixture $script:change.adoption_event))){
        if(Test-Path -LiteralPath $path){$text=[IO.File]::ReadAllText($path);[IO.File]::WriteAllText($path,[regex]::Replace($text,'(?m)^dependency_sha256: [a-f0-9]{64}',('dependency_sha256: '+$hash)))}
    }
}
function Rejected([string]$Name,[scriptblock]$Mutate,[string]$Expected) {
    Reset-Case
    & $Mutate
    Commit-Case
    $failed=$false
    try{& "$PSScriptRoot/repository.ps1" -Root $fixture -AsObject|Out-Null}catch{if($_.Exception.Message -match $Expected){$failed=$true}else{throw}}
    if(!$failed){throw "Invalid amendment admitted: $Name"}
    $script:negativeCount++
    Write-Output "PASS negative: $Name"
}
try {
    Assert-Owned
    & git -c core.longpaths=true clone --quiet --shared --no-checkout -- $root $fixture
    if($LASTEXITCODE -ne 0){throw 'Dependency fixture clone failed'}
    Fixture-Git @('checkout','--quiet','--detach','HEAD')
    Fixture-Git @('config','core.safecrlf','false')
    # Overlay the reviewed working candidate, never private ignored data/weights.
    Copy-Item -LiteralPath "$root/Tasks" -Destination $fixture -Recurse -Force
    Copy-Item -LiteralPath "$root/scripts" -Destination $fixture -Recurse -Force
    # Reproduce the proposal stage even after the real Correction has closed.
    foreach($file in Get-ChildItem "$fixture/$governing/events" -Filter '*.md'){
        if([IO.File]::ReadAllText($file.FullName) -match '\bInProgress -> (Done|Blocked|Cancelled)\b'){Remove-Item -LiteralPath $file.FullName}
    }
    if(Test-Path "$fixture/Tasks/version-requests/FDEC-101.json"){Remove-Item -LiteralPath "$fixture/Tasks/version-requests/FDEC-101.json"}
    Commit-Case
    $script:baseline=(& git -C $fixture rev-parse HEAD)
    Reset-Case
    $records=& "$PSScriptRoot/repository.ps1" -Root $fixture -AsObject
    if(($records['FDEC-087'].dependencies -join ',') -cne 'FDEC-019,FDEC-101' -or $records['FDEC-101'].status -cne 'InProgress' -or $records['FDEC-016'].status -cne 'Blocked'){throw 'Incorrect initial dependency reconciliation'}
    foreach($id in 'FDEC-015','FDEC-016','FDEC-087'){if($records['FDEC-020'].dependencies -notcontains $id){throw 'D003 gate prerequisite removed'}}
    foreach($path in @("$task/TASK.md",'Tasks/items/ai/FDEC-016-lora-qlora-trainer/TASK.md','Tasks/items/quality/FDEC-020-targeted-integration-gate/TASK.md')){
        if((Bound $path).sha256 -ne (Get-IdentityHash (Join-Path $root $path))){throw 'Original task criteria changed'}
    }
    Write-Output 'PASS positive: exact graph; original task/GPU/gate criteria preserved'
    $amended=$records['FDEC-087']
    $eventObject=Envelope $script:event
    $before=[DateTimeOffset]::Parse((Field $eventObject.front 'created_at')).AddTicks(-1)
    $old=Epic-Snapshot $amended $before
    $current=Epic-Snapshot $amended ([DateTimeOffset]::MaxValue)
    if(($old.dependencies -join ',') -cne 'FDEC-016' -or ($current.dependencies -join ',') -cne 'FDEC-019,FDEC-101' -or $old.paths -contains (Join-Path $fixture $changePath) -or $current.paths -notcontains (Join-Path $fixture $changePath)){throw 'Historical dependency/artifact cutoff incorrect'}
    Write-Output 'PASS positive: original and amended historical snapshots bind only artifacts effective at cutoff'
    $ready=Get-Content "$root/$governing/evidence/readiness-v1.json" -Raw|ConvertFrom-Json
    $ready.task_sha256=(Bound "$task/TASK.md").sha256
    $ready.source_sha=(& git -C $fixture rev-parse HEAD)
    $ready.allowed_paths=@('training/finetune','training/config','training/scripts','docs/training')
    $ready.matrix=New-FixtureMatrix $fixture $task 'dependency-amendment premature admission'
    $ready.criteria_revisions=(Get-EffectiveCriteria $fixture "$fixture/$task").revisions
    $ready.dependency_revisions=New-FixtureDependencyBindings $fixture 'FDEC-087'
    $ready.migration_revisions=New-FixtureMigrationBindings $fixture
    $ready.rule_sources=@('AGENTS.md','DEVELOPMENT.md','Tasks/AGENTS.md','Tasks/policy/checkout-identities-076.json','Tasks/policy/dependency-amendment-1.0.md'|ForEach-Object{Bound $_})
    $ready.epic_state_evidence=@(foreach($r in $records.Values|Where-Object epic){foreach($path in $r.state_paths){Bound $path.Substring($fixture.Length+1).Replace('\','/')}})
    $ready.source_state_sha256=Get-SourceState $fixture 'FDEC-087'
    Save-Json "$task/evidence/dependency-fixture-ready.json" $ready
    Write-ReadinessAcceptance $fixture $task evidence/dependency-fixture-ready.json fixture
    foreach($action in 'claim','dispatch','resume','execute','close'){
        $failed=$false
        try{& "$PSScriptRoot/admission.ps1" -Root $fixture -TaskId FDEC-087 -ReadinessFile evidence/dependency-fixture-ready.json -Action $action}catch{if($_.Exception.Message -match 'Dependency not Done: FDEC-101'){$failed=$true}else{throw}}
        if(!$failed){throw "Premature MLX admission: $action"}
    }
    Write-Output 'PASS boundary: all five admission actions reject unverified governing Correction'
    $ready.rule_sources=@($ready.rule_sources|Where-Object path -CNE 'Tasks/policy/dependency-amendment-1.0.md')
    Save-Json "$task/evidence/ruleless-ready.json" $ready
    Write-ReadinessAcceptance $fixture $task evidence/ruleless-ready.json fixture
    $ruleRejected=$false
    try{& "$PSScriptRoot/admission.ps1" -Root $fixture -TaskId FDEC-087 -ReadinessFile evidence/ruleless-ready.json -Action dispatch}catch{if($_.Exception.Message -match 'Missing governing rule: Tasks/policy/dependency-amendment-1.0.md'){$ruleRejected=$true}else{throw}}
    if(!$ruleRejected){throw 'Amended dependency contract omitted from admission rules'}
    Write-Output 'PASS boundary: omitted dependency contract rejects fresh readiness'
    Rejected 'stale prior' {$script:change.previous_dependencies=@('FDEC-015');Rebind} 'Stale, empty'
    Rejected 'non-array prior' {$script:change.previous_dependencies='FDEC-016';Rebind} 'explicit arrays'
    Rejected 'unknown field' {$script:change|Add-Member unknown $true;Rebind} 'Unsupported recovery fields'
    Rejected 'duplicate new dependency' {$script:change.new_dependencies=@('FDEC-019','FDEC-101','FDEC-101');Rebind} 'duplicate amended'
    Rejected 'missing governing dependency' {$script:change.new_dependencies=@('FDEC-019');Rebind} 'self-authorizing'
    Rejected 'self dependency' {$script:change.new_dependencies+=@('FDEC-087');Rebind} 'self-authorizing'
    Rejected 'non-ancestor source' {$script:change.source_sha='f'*40;Rebind} 'not an ancestor'
    Rejected 'stale target identity' {$script:change.target_spec.sha256='0'*64;Rebind} 'artifact binding'
    Rejected 'changed source specification despite new hash' {$p=Join-Path $fixture "$task/TASK.md";[IO.File]::AppendAllText($p,"`nFixture source drift.`n");$script:change.target_spec=Bound "$task/TASK.md";Rebind} 'source bytes changed'
    Rejected 'wrong governing specification' {$script:change.governing_spec=Bound 'Tasks/items/ai/FDEC-016-lora-qlora-trainer/TASK.md';Rebind} 'requires separate S001 Correction'
    Rejected 'wrong target' {$script:change.target_id='FDEC-015';Rebind} 'Unsupported dependency amendment'
    Rejected 'unsafe adoption path' {$script:change.adoption_event='../outside.md';Save-Json $changePath $script:change;$hash=(Bound $changePath).sha256;[IO.File]::WriteAllText($script:event,[regex]::Replace([IO.File]::ReadAllText($script:event),'(?m)^dependency_sha256: [a-f0-9]{64}',('dependency_sha256: '+$hash)))} 'Invalid dependency adoption'
    Rejected 'missing adoption' {Remove-Item -LiteralPath (Join-Path $fixture $script:change.adoption_event)} 'ReadAllText|find'
    Rejected 'changed adoption' {$p=Join-Path $fixture $script:change.adoption_event;[IO.File]::WriteAllText($p,[IO.File]::ReadAllText($p).Replace('correction_id: FDEC-101','correction_id: FDEC-100'))} 'explicit dependency adoption'
    Rejected 'terminal target' {$p=Join-Path $fixture "$task/TASK.md";[IO.File]::WriteAllText($p,[IO.File]::ReadAllText($p).Replace('initial_status: Planned','initial_status: Done'))} 'Unsupported dependency amendment'
    Rejected 'inactive governing Correction' {$f=Get-ChildItem "$fixture/$governing/events" -Filter '*.md'|Where-Object{[IO.File]::ReadAllText($_.FullName) -match 'Planned -> InProgress'};[IO.File]::WriteAllText($f.FullName,[IO.File]::ReadAllText($f.FullName).Replace('Planned -> InProgress','Planned -> Cancelled'))} 'Inactive dependency amendment governance'
    Rejected 'unsupported contract' {$script:change.contract=Bound 'Tasks/policy/adoption-5.6.json';Rebind} 'Unsupported dependency amendment contract'
    Rejected 'missing dependency target' {$script:change.new_dependencies+=@('FDEC-999');Rebind} 'Missing dependency'
    Rejected 'cycle through D003 gate' {$script:change.new_dependencies+=@('FDEC-020');Rebind} 'Dependency cycle'
    Rejected 'orphan amendment' {Copy-Item -LiteralPath "$fixture/$changePath" -Destination "$fixture/Tasks/dependency-amendments/FDEC-087-D002.json"} 'orphan dependency amendment'
    Rejected 'duplicate JSON key' {$p=Join-Path $fixture $changePath;$text=[IO.File]::ReadAllText($p);$start=$text.IndexOf('{')+1;[IO.File]::WriteAllText($p,$text.Insert($start,'"schema":"duplicate",'));Rebind-Raw} 'Duplicate or invalid request JSON key'
    Rejected 'duplicate amendment event' {$text=[IO.File]::ReadAllText($script:event);$text=[regex]::Replace($text,'(?m)^event_id: [^\r\n]+',('event_id: '+[guid]::NewGuid().ToString()));$text=[regex]::Replace($text,'(?m)^created_at: [^\r\n]+',('created_at: '+[DateTimeOffset]::UtcNow.AddDays(1).ToString('yyyy-MM-ddTHH:mm:ss.fffZ')));[IO.File]::WriteAllText((Join-Path $fixture "$task/events/duplicate-fixture-event.md"),$text)} 'duplicate dependency amendment reference'
    Reset-Case
    & "$PSScriptRoot/repository.ps1" -Root $fixture|Out-Null
    Write-Output "PASS: $script:negativeCount negative amendment cases, exact graph, five shared admission denials, contract binding and final ordinary repository validation"
} finally {
    Assert-Owned
    if(Test-Path -LiteralPath $fixture){Remove-Item -LiteralPath $fixture -Recurse -Force}
}
