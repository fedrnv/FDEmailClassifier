# Offline validation of the repository's deliberately restricted FDTasks envelope.
param([string]$Root = (Resolve-Path "$PSScriptRoot/../..").Path, [switch]$AsObject)
$ErrorActionPreference = 'Stop'
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
    if ($line -match '^[MDRCTU]' -and $line -match '(TASK\.md|EPIC\.md|/events/|/evidence/|/reviews/|/decisions/|/version-requests/|/policy/)') { throw "Immutable record changed: $line" }
}
$records = @{}
foreach ($file in Get-ChildItem "$Root/Tasks/items","$Root/Tasks/epics" -Recurse -File | Where-Object Name -In 'TASK.md','EPIC.md') {
    $record = Envelope $file.FullName
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
        if ($kind -notin 'status-changed','work-started','dependency-added','membership-added','readiness-accepted','scope-amended') { throw "Unsupported event semantics: $kind" }
        $record.state_paths+= $event.path
        if ($kind -in 'status-changed','work-started') {
            $transitions=[regex]::Matches($event.text,'\b(Planned|Active|InProgress|Done|Blocked|Cancelled) -> (Planned|Active|InProgress|Done|Blocked|Cancelled)\b')
            if ($transitions.Count -ne 1) { throw 'Ambiguous status transition' }
            $m=$transitions[0]
            if ($record.status -ne $m.Groups[1].Value) { throw "Conflicting status transition: $($record.id) current=$($record.status) expected=$($m.Groups[1].Value) event=$($event.path)" }
            $record.status=$m.Groups[2].Value
        }
        if ($kind -in 'dependency-added','membership-added') {
            $m=[regex]::Match($event.text,'(?m)^Add \*{0,2}(FDEC-[0-9]{3})\b')
            if (!$m.Success) { throw 'Unsupported relationship amendment' }
            if ($kind -eq 'dependency-added') { $record.dependencies+= $m.Groups[1].Value } else { $record.members+= $m.Groups[1].Value }
        }
    }
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
foreach ($file in Get-ChildItem "$Root/Tasks/version-requests" -Filter '*.json' -ErrorAction SilentlyContinue) {
    $r=Get-Content $file.FullName -Raw | ConvertFrom-Json
    if ($r.schema -ne 'fdtasks-version-request/v1' -or !$r.request_id -or $requests.ContainsKey($r.request_id) -or !$r.summary -or !$r.verification) { throw 'Invalid or duplicate version request' }
    $requests[$r.request_id]=$true
    if ($r.type -notin 'task_closed','bug_closed','correction_closed') { throw 'Release/Epic requests require a dedicated verified publisher (not implemented at foundation)' }
    if (!$r.work_item_id -or $closed.ContainsKey($r.work_item_id) -or !$records.ContainsKey($r.work_item_id) -or $records[$r.work_item_id].parent -ne $r.epic_id -or $records[$r.work_item_id].status -ne 'Done') { throw 'Invalid closed item request' }
    $closed[$r.work_item_id]=$true
    foreach ($path in $r.verification) {
        $absolute=[IO.Path]::GetFullPath((Join-Path $Root $path))
        if (!$absolute.StartsWith($rootPath+[IO.Path]::DirectorySeparatorChar) -or !(Test-Path -LiteralPath $absolute -PathType Leaf)) { throw 'Missing or escaping verification reference' }
    }
}
# No hosted entrypoints are admitted until their command graph validator arrives
# with FDEC-050. This rejects opaque wrappers as well as direct test steps.
if (Test-Path "$Root/.github/workflows") {
    if (@(Get-ChildItem "$Root/.github/workflows" -File).Count) { throw 'Unreviewed hosted workflow: command graph validation required' }
}
if ($AsObject) { return $records }
Write-Output "PASS: $($records.Count) records, immutable history, graph, requests and hosted publication boundary"
