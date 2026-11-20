$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
Set-Location $root
& "$root/docs/verification/verify-d002-outcome.ps1" -TestNegatives
$records=& "$root/scripts/validate_tasks/repository.ps1" -Root $root -AsObject
if($records['FDEC-099'].status -ne 'InProgress' -or $records['FDEC-013'].status -ne 'InProgress' -or $records['FDEC-014'].status -ne 'InProgress'){throw 'Invalid current correction/gate/review state'}
if($records['FDEC-013'].dependencies -notcontains 'FDEC-099' -or $records['FDEC-EPIC-D002'].members -notcontains 'FDEC-099'){throw 'Correction not integrated into required lifecycle'}
$active=@($records.Values|Where-Object {$_.epic -and $_.id -match '^FDEC-EPIC-D' -and $_.status -eq 'Active'})
if($active.Count -ne 1 -or $active[0].id -ne 'FDEC-EPIC-D002'){throw 'Invalid active development Epic'}
git -C $root diff --check
if($LASTEXITCODE -ne 0){throw 'Whitespace check failed'}
Write-Output "PASS: $($records.Count) records, immutable history, correction membership, reopened gate dependency, independent review pending and one active D002"
Write-Output "SOURCE: $(git -C $root rev-parse HEAD)"
