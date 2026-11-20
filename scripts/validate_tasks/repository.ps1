# Offline validation of the repository's deliberately restricted FDTasks envelope.
param([string]$Root = (Resolve-Path "$PSScriptRoot/../..").Path, [switch]$AsObject)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/identity.ps1"
. "$PSScriptRoot/epic-closure.ps1"
. "$PSScriptRoot/identity-migrations.ps1"
. "$PSScriptRoot/request-recovery.ps1"
function Field($text, $key) {
    $match = [regex]::Match($text, "(?m)^$([regex]::Escape($key)): ([^\r\n]+)")
    if (!$match.Success) { throw "Missing field: $key" }
    return $match.Groups[1].Value.Trim().Trim('"')
}
function Envelope($path) {
    $text = [IO.File]::ReadAllText($path)
    $match = [regex]::Match($text, '\A(?:\uFEFF)?---\r?\n(.*?)\r?\n---\r?\n', 'Singleline')
    if (!$match.Success) { throw "Invalid envelope: $path" }
    return @{ front=$match.Groups[1].Value; text=$text; path=$path }
}
function IdList($value) {
    if ($value -notmatch '^\[(?:[A-Z0-9-]+(?:, )?)*\]$') { throw 'Unsupported dependency list' }
    return @([regex]::Matches($value, 'FDEC-(?:EPIC-[DS])?[0-9]{3}') | ForEach-Object Value)
}
$rootPath = [IO.Path]::GetFullPath($Root).TrimEnd('\','/')
$gitHead = git -C $Root rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Git baseline unavailable' }
# Git applies checkout normalization; do not confuse CRLF with rewritten history.
$changes = @(git -C $Root -c core.quotepath=false diff --name-status HEAD -- Tasks)
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect immutable history' }
foreach ($line in $changes) {
    if ($line -match '^[MDRCTU]' -and $line -match '(TASK\.md|EPIC\.md|/events/|/evidence/|/reviews/|/decisions/|/version-requests/|/request-recoveries/|/policy/|/migrations/)') { throw "Immutable record changed: $line" }
}
$retiredPaths=@{}; $resolutions=@()
if (Test-Path "$Root/Tasks/migrations") {
    foreach ($file in Get-ChildItem "$Root/Tasks/migrations" -Filter '*.json') {
        $resolution=Get-Content $file.FullName -Raw | ConvertFrom-Json
        if ($resolution.schema -notin 'fdec-identity-resolution/v1','fdec-identity-resolution/v2') { throw 'Unsupported identity migration' }
        foreach ($binding in @($resolution.retired,$resolution.retained,$resolution.replacement,$resolution.retirement_event)) {
            if (!$binding.path -or !$binding.sha256) { throw 'Incomplete identity binding' }
            $absolute=[IO.Path]::GetFullPath((Join-Path $Root $binding.path))
            if (!(Test-IdentityBinding $Root $binding.path $binding.sha256)) { throw 'Stale or missing identity binding' }
        }
        $old=Envelope (Join-Path $Root $resolution.retired.path)
        $kept=Envelope (Join-Path $Root $resolution.retained.path)
        $new=Envelope (Join-Path $Root $resolution.replacement.path)
        $retirement=Envelope (Join-Path $Root $resolution.retirement_event.path)
        $oldId=Field $old.front 'id'; $newId=Field $new.front 'id'
        $oldParent=Field $old.front 'epic_id'
        if ($oldId -ne (Field $kept.front 'id') -or $oldId -eq $newId -or $newId -notmatch '^FDEC-[0-9]{3}$' -or $oldParent -ne (Field $new.front 'epic_id') -or $oldParent -eq (Field $kept.front 'epic_id') -or (Field $old.front 'initial_status') -ne 'Planned') { throw 'Invalid collision identity mapping' }
        if ((Field $retirement.front 'event_type') -ne 'superseded' -or (Field $retirement.front 'task_id') -ne $oldId -or (Field $retirement.front 'replacement_id') -ne $newId -or (Field $retirement.front 'correction_id') -ne $resolution.correction_id -or (Split-Path (Split-Path $retirement.path)) -ne (Split-Path $old.path)) { throw 'Invalid retirement event' }
        if ($resolution.schema -eq 'fdec-identity-resolution/v2') {
            Assert-PlanningMigration $Root $resolution $old $new $retirement
        } elseif (@(Get-ChildItem (Join-Path (Split-Path $old.path) 'events') -Filter '*.md').Count -ne 1) { throw 'Retired collision has unsupported execution history' }
        if ($retiredPaths.ContainsKey($old.path)) { throw 'Duplicate retirement mapping' }
        $resolution | Add-Member old_id $oldId
        $resolution | Add-Member new_id $newId
        $resolution | Add-Member old_parent $oldParent
        $retiredPaths[$old.path]=$true; $resolutions+= $resolution
    }
}
foreach ($resolution in $resolutions | Where-Object schema -EQ 'fdec-identity-resolution/v2') {
    $namespace=@($resolutions | Where-Object {$_.schema -eq 'fdec-identity-resolution/v2' -and $_.correction_id -eq $resolution.correction_id -and $_.source_revision -eq $resolution.source_revision})
    if ($resolution.id_map.Count -ne $namespace.Count) { throw 'Incomplete planning identity namespace' }
    foreach ($pair in $resolution.id_map) {
        $matches=@($resolutions | Where-Object {$_.schema -eq 'fdec-identity-resolution/v2' -and $_.correction_id -eq $resolution.correction_id -and $_.source_revision -eq $resolution.source_revision -and $_.old_id -eq $pair.old_id -and $_.new_id -eq $pair.new_id})
        if ($matches.Count -ne 1) { throw 'Unbound planning identity substitution' }
    }
}
$records = @{}
foreach ($file in Get-ChildItem "$Root/Tasks/items","$Root/Tasks/epics" -Recurse -File | Where-Object Name -In 'TASK.md','EPIC.md') {
    $record = Envelope $file.FullName
    if ($retiredPaths.ContainsKey($file.FullName)) { continue }
    $id = Field $record.front 'id'
    if ($records.ContainsKey($id)) { throw "Duplicate record: $id" }
    $epic = $file.Name -eq 'EPIC.md'
    if (($epic -and $id -notmatch '^FDEC-EPIC-(D00[1-9]|D0[1-9][0-9]|D[1-9][0-9]{2}|S00[12])$') -or (!$epic -and $id -notmatch '^FDEC-[0-9]{3}$')) { throw "Invalid identity: $id" }
    if ((Field $record.front 'schema') -ne $(if($epic){'fdtasks-epic/v4'}else{'fdtasks-spec/v3'})) { throw "Invalid schema: $id" }
    if (!$file.Directory.Name.StartsWith($id)) { throw "Misplaced record: $id" }
    $record.id=$id; $record.epic=$epic
    $record.status=Field $record.front 'initial_status'
    if ($record.status -notin 'Planned','Active','InProgress','Done','Blocked','Cancelled') { throw 'Unsupported initial status' }
    $record.dependencies=@(IdList (Field $record.front 'initial_dependencies'))
    $record.members=@()
    $record.state_paths=@($file.FullName)
    $record.closure_history=@()
    if ($epic) {
        $record.members=@([regex]::Matches($record.text,'(?m)^- (FDEC-[0-9]{3})\r?$') | ForEach-Object {$_.Groups[1].Value})
    } else {
        $record.parent=Field $record.front 'epic_id'
        if ((Field $record.front 'size') -ne 'medium') { throw "Invalid size: $id" }
        foreach ($key in 'outcomes','packets') {
            $m=[regex]::Match($record.front,"(?m)^  ${key}: \[(.+)\]\r?$")
            if (!$m.Success) { throw "Missing atomicity: $id" }
            $strings=@([regex]::Matches($m.Groups[1].Value,'"(?:[^"\\]|\\.)+"'))
            if (($key -eq 'outcomes' -and $strings.Count -ne 1) -or $strings.Count -lt 1 -or $strings.Count -gt 3) { throw "Invalid atomicity: $id" }
            if ($key -eq 'packets' -and $strings.Count -gt 1 -and $record.front -notmatch '(?m)^  inseparability_reason: .+') { throw "Missing inseparability: $id" }
        }
        if ($record.front -notmatch '(?m)^  independent_acceptance: false\r?$' -or $record.front -notmatch '(?m)^  boundary_reason: .+') { throw "Invalid atomicity boundary: $id" }
        if ($record.text -notmatch '\| AC-01 \|' -or $record.text -notmatch '\| AC-02 \|') { throw "Missing AC matrix: $id" }
    }
    $records[$id]=$record
}
$eventIds=@{}
foreach ($record in $records.Values) {
    $eventDir=Join-Path (Split-Path $record.path) 'events'
    $events=@()
    if (Test-Path $eventDir) { $events=@(Get-ChildItem $eventDir -Filter '*.md' | ForEach-Object { $e=Envelope $_.FullName; $e.date=[DateTimeOffset]::Parse((Field $e.front 'created_at')); $e }) }
    foreach ($event in $events | Sort-Object { $_['date'].UtcTicks }, { if ((Field $_['front'] 'event_type') -eq 'work-started') { 0 } else { 1 } }, { $_['path'] }) {
        $eventId=Field $event.front 'event_id'
        if ($eventIds.ContainsKey($eventId)) { throw 'Duplicate event identity' }
        $eventIds[$eventId]=$true
        if ((Field $event.front 'schema') -ne 'fdtasks-event/v3' -or (Field $event.front 'task_id') -ne $record.id) { throw 'Invalid event envelope' }
        $null=Field $event.front 'actor'; $null=Field $event.front 'base_revision'
        $kind=Field $event.front 'event_type'
        if ($kind -notin 'status-changed','work-started','dependency-added','membership-added','readiness-accepted','scope-amended','membership-replaced','dependency-replaced') { throw "Unsupported event semantics: $kind" }
        $record.state_paths+= $event.path
        if ($kind -in 'status-changed','work-started') {
            $transitions=[regex]::Matches($event.text,'\b(Planned|Active|InProgress|Done|Blocked|Cancelled) -> (Planned|Active|InProgress|Done|Blocked|Cancelled)\b')
            if ($transitions.Count -ne 1) { throw 'Ambiguous status transition' }
            $m=$transitions[0]
            if ($record.status -ne $m.Groups[1].Value) { throw "Conflicting status transition: $($record.id) current=$($record.status) expected=$($m.Groups[1].Value) event=$($event.path)" }
            $record.status=$m.Groups[2].Value
            if ($record.status -eq 'Done') { $record.closure_history+= $event }
        }
        if ($kind -in 'dependency-added','membership-added') {
            $m=[regex]::Match($event.text,'(?m)^Add (?:\*{1,2}|`)?(FDEC-[0-9]{3})\b')
            if (!$m.Success) { throw 'Unsupported relationship amendment' }
            if ($kind -eq 'dependency-added') { $record.dependencies+= $m.Groups[1].Value } else { $record.members+= $m.Groups[1].Value }
        }
        if ($kind -in 'membership-replaced','dependency-replaced') {
            $oldId=Field $event.front 'old_task_id'; $newId=Field $event.front 'new_task_id'
            $owner=if($record.epic){$record.id}else{$record.parent}
            $matching=@($resolutions | Where-Object {$_.old_id -eq $oldId -and $_.new_id -eq $newId -and $_.old_parent -eq $owner})
            if ($matching.Count -ne 1) { throw 'Unbound relationship replacement' }
            $key=if($kind -eq 'membership-replaced'){'members'}else{'dependencies'}
            if ($record[$key] -notcontains $oldId -or $record[$key] -contains $newId) { throw 'Invalid relationship replacement' }
            $record[$key]=@($record[$key] | ForEach-Object {if($_ -eq $oldId){$newId}else{$_}})
        }
    }
}
foreach ($resolution in $resolutions) {
    if (!$records.ContainsKey($resolution.correction_id) -or $records[$resolution.correction_id].parent -ne 'FDEC-EPIC-S001' -or (Field $records[$resolution.correction_id].front 'type') -ne 'Correction' -or !$records.ContainsKey($resolution.new_id)) { throw 'Missing governing identity Correction or replacement' }
}
foreach ($record in $records.Values) {
    foreach ($dependency in $record.dependencies) { if (!$records.ContainsKey($dependency)) { throw "Missing dependency: $dependency" } }
    if (!$record.epic -and (!$records.ContainsKey($record.parent) -or !$records[$record.parent].members.Contains($record.id))) { throw "Missing Epic membership: $($record.id)" }
    foreach ($member in $record.members) { if (!$records.ContainsKey($member) -or $records[$member].parent -ne $record.id) { throw "Invalid Epic member: $member" } }
}
function Visit($id,$stack) {
    if ($stack -contains $id) { throw "Dependency cycle: $id" }
    foreach ($dependency in $records[$id].dependencies) { Visit $dependency (@($stack)+$id) }
}
foreach ($id in $records.Keys) { Visit $id @() }
$active=@($records.Values | Where-Object {$_.epic -and $_.id -match 'EPIC-D' -and $_.status -in 'Active','InProgress'})
if ($active.Count -gt 1) { throw 'Multiple active development Epics' }
foreach ($special in 'FDEC-EPIC-S001','FDEC-EPIC-S002') { if (!$records.ContainsKey($special) -or $records[$special].status -ne 'Active') { throw 'Special Epic must remain Active' } }
$requests=@{}; $closed=@{}
$requestFiles=@(Get-ChildItem "$Root/Tasks/version-requests" -Filter '*.json' -ErrorAction SilentlyContinue)
$requestEntries=@(Get-ResolvedClosureRequests $rootPath $records $requestFiles $gitHead)
$requestBodies=@($requestEntries | ForEach-Object {$_.request})
if (@($requestBodies | Group-Object request_id | Where-Object Count -GT 1).Count) { throw 'Invalid or duplicate version request' }
if (@($requestBodies | Group-Object work_item_id | Where-Object Count -GT 1).Count) { throw 'Invalid closed item request' }
foreach ($entry in $requestEntries) {
    $file=$entry.file
    $r=$entry.request
    if ($r.schema -ne 'fdtasks-version-request/v1' -or !$r.request_id -or $requests.ContainsKey($r.request_id) -or !$r.summary -or !$r.verification) { throw 'Invalid or duplicate version request' }
    $requests[$r.request_id]=$true
    if ($r.type -eq 'epic_closed') {
        $relative=$file.FullName.Substring($rootPath.Length+1).Replace('\','/')
        $accepted=@(git -C $Root ls-tree --name-only $gitHead -- $relative)
        if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve accepted Epic closure baseline' }
        Assert-EpicClosure $rootPath $records $r $gitHead ([bool]$accepted.Count) $requestBodies
        $closed[$r.work_item_id]=$true
        continue
    }
    if ($r.type -notin 'task_closed','bug_closed','correction_closed') { throw 'Release/major requests require a dedicated verified publisher (not implemented at foundation)' }
    if (!$r.work_item_id -or $closed.ContainsKey($r.work_item_id) -or !$records.ContainsKey($r.work_item_id) -or $records[$r.work_item_id].parent -ne $r.epic_id -or !$records[$r.work_item_id].closure_history.Count) { throw 'Invalid closed item request' }
    $target=$records[$r.work_item_id]
    $expectedType=switch (Field $target.front 'type') { 'Task' {'task_closed'} 'Bug' {'bug_closed'} 'Correction' {'correction_closed'} default {throw 'Unsupported closure item type'} }
    if ($r.type -ne $expectedType) { throw 'Closure request type does not match item' }
    $closed[$r.work_item_id]=$true
    foreach ($path in $r.verification) {
        $absolute=[IO.Path]::GetFullPath((Join-Path $Root $path))
        $evidenceRoot=(Join-Path (Split-Path $target.path) 'evidence')+[IO.Path]::DirectorySeparatorChar
        if (!$absolute.StartsWith($evidenceRoot,[StringComparison]::OrdinalIgnoreCase) -or !(Test-Path -LiteralPath $absolute -PathType Leaf) -or !(Get-Item -LiteralPath $absolute).Length) { throw 'Missing or escaping verification reference' }
    }
    # Existing accepted requests remain historical authority. New requests must
    # carry a hash-bound closure brief on the FIRST validated Done transition.
    # Reopen/reclose preserves that identity; current status is intentionally not
    # used as a substitute for verified closure history.
    $relative=$file.FullName.Substring($rootPath.Length+1).Replace('\','/')
    $accepted=@(git -C $Root ls-tree --name-only $gitHead -- $relative)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve accepted closure baseline' }
    $firstClosure=$target.closure_history[0]
    $proofMatch=[regex]::Match($firstClosure.front,'(?m)^closure_proof: ([^\r\n]+)')
    if ($proofMatch.Success) {
        $proofPath=[IO.Path]::GetFullPath((Join-Path (Split-Path $target.path) $proofMatch.Groups[1].Value.Trim()))
        if (!$proofPath.StartsWith($evidenceRoot,[StringComparison]::OrdinalIgnoreCase) -or !(Test-IdentityBinding $Root $proofPath.Substring($rootPath.Length+1) (Field $firstClosure.front 'closure_proof_sha256'))) { throw 'Invalid closure proof binding' }
        $proof=Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
        if (!(Test-IdentityBinding $Root $target.path.Substring($rootPath.Length+1) $proof.task_sha256) -or !$proof.verification) { throw 'Unverified closure proof' }
        if (!$accepted.Count -and $proof.source_sha -ne $gitHead) { throw 'Stale first closure source' }
        foreach ($path in $r.verification) {
            $entries=@($proof.verification | Where-Object path -EQ $path)
            if ($entries.Count -ne 1 -or !(Test-IdentityBinding $Root $path $entries[0].sha256)) { throw 'Unverified closure evidence' }
        }
    } elseif (!$accepted.Count) { throw 'New closure request requires verified first-closure proof' }
}
foreach ($epic in $records.Values | Where-Object {$_.epic -and $_.id -match 'EPIC-D' -and $_.closure_history.Count}) {
    if (!$closed.ContainsKey($epic.id)) { throw 'Missing verified Epic closure request' }
}
# No hosted entrypoints are admitted until their command graph validator arrives
# with FDEC-050. This rejects opaque wrappers as well as direct test steps.
if (Test-Path "$Root/.github/workflows") {
    if (@(Get-ChildItem "$Root/.github/workflows" -File).Count) { throw 'Unreviewed hosted workflow: command graph validation required' }
}
if ($AsObject) { return $records }
Write-Output "PASS: $($records.Count) records, immutable history, graph, requests and hosted publication boundary"
