. "$PSScriptRoot/identity.ps1"
function Readiness-Field($Front,$Name) {
    $matches=[regex]::Matches($Front,"(?m)^$([regex]::Escape($Name)): ([^\r\n]+)")
    if ($matches.Count -ne 1) { throw 'Ambiguous or missing readiness event field' }
    return $matches[0].Groups[1].Value
}
function Read-ReadinessEvents([string]$TaskDirectory) {
    $events=Join-Path $TaskDirectory 'events'
    if (!(Test-Path -LiteralPath $events)) { return @() }
    return @(Get-ChildItem -LiteralPath $events -Filter '*.md' | ForEach-Object {
        $text=[IO.File]::ReadAllText($_.FullName)
        $front=[regex]::Match($text,'\A(?:\uFEFF)?---\r?\n(.*?)\r?\n---\r?\n','Singleline').Groups[1].Value
        if ($front -match '(?m)^event_type: readiness-accepted\r?$') {
            $null=Readiness-Field $front 'event_type'
            $date=Readiness-Field $front 'created_at'
            [pscustomobject]@{path=$_.FullName;front=$front;date=[DateTimeOffset]::Parse($date)}
        }
    })
}
function Assert-AcceptedReadiness([string]$TaskDirectory,[string]$TaskId,[string]$ReadyPath) {
    $events=@(Read-ReadinessEvents $TaskDirectory | Sort-Object date -Descending)
    if (!$events.Count) { throw 'Missing accepted readiness event' }
    if ($events.Count -gt 1 -and $events[0].date -eq $events[1].date) { throw 'Ambiguous accepted readiness events' }
    $front=$events[0].front
    $id=Readiness-Field $front 'task_id'
    $file=Readiness-Field $front 'readiness_file'
    $hash=Readiness-Field $front 'readiness_sha256'
    if ($id -ne $TaskId -or !$file -or $hash -notmatch '^[a-f0-9]{64}$') { throw 'Accepted readiness event lacks exact evidence binding' }
    $bound=[IO.Path]::GetFullPath((Join-Path $TaskDirectory $file))
    $prefix=(Join-Path $TaskDirectory 'evidence')+[IO.Path]::DirectorySeparatorChar
    if (!$bound.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -or $bound -ne $ReadyPath) { throw 'Readiness is not the current accepted decision' }
    if ((Get-IdentityHash $bound) -ne $hash) { throw 'Accepted readiness evidence hash mismatch' }
}
function Write-ReadinessAcceptance([string]$Root,[string]$TaskPath,[string]$ReadinessFile,[string]$Actor='codex') {
    # This records the authorized executor's reviewed decision; it does not
    # perform semantic review or replace any admission validation.
    $rootFull=[IO.Path]::GetFullPath($Root).TrimEnd('\','/')
    $task=[IO.Path]::GetFullPath((Join-Path $rootFull $TaskPath))
    if (!$task.StartsWith($rootFull+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $Actor -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Invalid readiness authoring path or actor' }
    $spec=[IO.File]::ReadAllText((Join-Path $task 'TASK.md'))
    $id=[regex]::Match($spec,'(?m)^id: (FDEC-[0-9]{3})\r?$').Groups[1].Value
    if (!$id) { throw 'Invalid readiness target' }
    $ready=[IO.Path]::GetFullPath((Join-Path $task $ReadinessFile))
    if (!$ready.StartsWith((Join-Path $task 'evidence')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or !(Test-Path -LiteralPath $ready -PathType Leaf)) { throw 'Readiness authoring evidence escapes task or is missing' }
    $now=[DateTimeOffset]::UtcNow
    $prior=@(Read-ReadinessEvents $task | Sort-Object date -Descending)
    if ($prior.Count -and $now.ToUnixTimeMilliseconds() -le $prior[0].date.ToUnixTimeMilliseconds()) { $now=$prior[0].date.AddMilliseconds(1) }
    $uid=[guid]::NewGuid().ToString()
    $hash=Get-IdentityHash $ready
    $base=git -C $Root rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Readiness authoring baseline missing' }
    $relative=$ready.Substring($task.Length+1).Replace('\','/')
    $directory=Join-Path $task 'events'
    $null=New-Item -ItemType Directory -Force $directory
    $output=Join-Path $directory "$($now.ToString('yyyyMMddTHHmmssfffZ'))-$Actor-readiness-accepted-$($uid.Substring(0,8)).md"
    @"
---
schema: fdtasks-event/v3
event_id: $uid
task_id: $id
event_type: readiness-accepted
created_at: $($now.ToString('yyyy-MM-ddTHH:mm:ss.fffZ'))
actor: $Actor
base_revision: "$base"
server_revision: null
readiness_file: $relative
readiness_sha256: $hash
---

Accept the exact task-scoped readiness evidence under standing executor authority.
All production actions must still validate source, rules, dependencies and criteria.
"@ | Set-Content -LiteralPath $output -Encoding UTF8
}
