$ErrorActionPreference='Stop'
$source='C:/GitHub/FDEmailClassifier-review-D001-R001'
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-r001-'+[guid]::NewGuid())
function Bound($path) { @{path=$path;sha256=(Get-FileHash (Join-Path $temp $path) -Algorithm SHA256).Hash.ToLowerInvariant()} }
try {
    New-Item -ItemType Directory $temp | Out-Null
    Copy-Item "$source/Tasks" "$temp/Tasks" -Recurse
    Copy-Item "$source/AGENTS.md","$source/DEVELOPMENT.md" $temp
    # Normalize only the owned fixture to the pinned LF policy bytes, so the
    # independent fresh-checkout failure does not mask admission checks below.
    $policyPath="$temp/Tasks/policy/upstream-5.6.md"
    [IO.File]::WriteAllText($policyPath,([IO.File]::ReadAllText($policyPath) -replace "`r`n","`n"),(New-Object Text.UTF8Encoding($false)))
    $fixtureMigration=Get-Content "$temp/Tasks/migrations/FDEC-074.json" -Raw | ConvertFrom-Json
    foreach ($binding in @($fixtureMigration.retired,$fixtureMigration.retained,$fixtureMigration.replacement,$fixtureMigration.retirement_event)) {
        $p=Join-Path $temp $binding.path
        if ((Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $binding.sha256) {
            # Author checkout retains mixed line endings in these two bindings.
            # Use its exact already hash-bound historical bytes in this fixture.
            Copy-Item -LiteralPath (Join-Path 'C:/GitHub/FDEmailClassifier' $binding.path) -Destination $p
            if ((Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $binding.sha256) { throw 'Fixture cannot reproduce pinned identity bytes' }
        }
    }
    $task='Tasks/items/foundation/FDEC-005-architecture-and-backend-adr'
    $ownedEvents=[IO.Path]::GetFullPath("$temp/$task/events")
    if (!$ownedEvents.StartsWith([IO.Path]::GetFullPath($temp)+[IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe fixture reset' }
    Remove-Item -LiteralPath $ownedEvents -Recurse -Force
    Remove-Item -LiteralPath "$temp/Tasks/version-requests/FDEC-005.json"
    [IO.File]::WriteAllText("$temp/source.txt",'accepted implementation')
    git -C $temp init --quiet
    git -C $temp config core.autocrlf false
    git -C $temp add .
    git -C $temp -c user.name=Reviewer -c user.email=reviewer@example.invalid commit --quiet -m fixture
    if ($LASTEXITCODE -ne 0) { throw 'Fixture baseline failed' }
    $ready=Get-Content "$source/Tasks/items/foundation/FDEC-004-repository-policy-and-fdtasks-adoption/evidence/readiness.json" -Raw | ConvertFrom-Json
    $ready.task_sha256=(Bound "$task/TASK.md").sha256
    $ready.source_sha=git -C $temp rev-parse HEAD
    $ready.epic_state_evidence=@(Get-ChildItem "$temp/Tasks/epics" -Recurse -File | ForEach-Object { Bound $_.FullName.Substring($temp.Length+1).Replace('\','/') })
    $ready.allowed_paths=@('Tasks')
    $migration=Get-Content "$temp/Tasks/migrations/FDEC-074.json" -Raw | ConvertFrom-Json
    $ready | Add-Member migration_revisions @(@('Tasks/migrations/FDEC-074.json',$migration.retired.path,$migration.retained.path,$migration.replacement.path,$migration.retirement_event.path) | ForEach-Object {Bound $_}) -Force
    [IO.File]::WriteAllText("$temp/$task/evidence/reviewer-ready.json",($ready | ConvertTo-Json -Depth 10))
    Write-Output 'CASE 1: no readiness-accepted event exists for fixture target'
    & "$source/scripts/validate_tasks/admission.ps1" -Root $temp -TaskId FDEC-005 -Action execute -ReadinessFile evidence/reviewer-ready.json
    Write-Output 'CASE 2: tracked implementation changes without HEAD change'
    [IO.File]::WriteAllText("$temp/source.txt",'changed implementation')
    git -C $temp diff --stat
    foreach ($action in 'claim','dispatch','resume','execute') {
        & "$source/scripts/validate_tasks/admission.ps1" -Root $temp -TaskId FDEC-005 -Action $action -ReadinessFile evidence/reviewer-ready.json
    }
    Write-Output 'CASE 3: readiness matrix omits AC-02'
    $ready.matrix=@($ready.matrix | Select-Object -First 1)
    [IO.File]::WriteAllText("$temp/$task/evidence/reviewer-ready.json",($ready | ConvertTo-Json -Depth 10))
    & "$source/scripts/validate_tasks/admission.ps1" -Root $temp -TaskId FDEC-005 -Action execute -ReadinessFile evidence/reviewer-ready.json
} finally {
    $resolved=[IO.Path]::GetFullPath($temp)
    $parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if (!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $resolved -Leaf) -notlike 'fdec-r001-*') { throw 'Unsafe fixture cleanup' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
