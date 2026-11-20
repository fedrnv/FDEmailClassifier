param([Parameter(Mandatory=$true)][string]$ExpectedSource)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
. "$root/scripts/validate_tasks/source-state.ps1"
Set-Location $root
$head=git rev-parse HEAD
if($LASTEXITCODE -ne 0 -or $head -cne $ExpectedSource){throw 'Wrong FDEC-099 verification source'}
$sourceState=Get-SourceState $root 'FDEC-099'
$requestHash=(Get-FileHash Tasks/version-requests/FDEC-099.json -Algorithm SHA256).Hash
& "$root/docs/verification/verify-d002-outcome-v2.ps1" -TestNegatives
$records=& "$root/scripts/validate_tasks/repository.ps1" -Root $root -AsObject
if($records['FDEC-099'].status -cne 'InProgress' -or $records['FDEC-100'].status -cne 'Done' -or $records['FDEC-013'].status -cne 'InProgress' -or $records['FDEC-014'].status -cne 'InProgress'){throw 'Invalid current correction/gate/review states'}
if($records['FDEC-099'].dependencies -notcontains 'FDEC-100' -or $records['FDEC-013'].dependencies -notcontains 'FDEC-099'){throw 'Missing required correction dependency'}
$active=@($records.Values|Where-Object {$_.epic -and $_.id -match '^FDEC-EPIC-D' -and $_.status -ceq 'Active'})
if($active.Count -ne 1 -or $active[0].id -cne 'FDEC-EPIC-D002'){throw 'Invalid active development Epic'}
if((git rev-parse HEAD) -cne $ExpectedSource -or (Get-SourceState $root 'FDEC-099') -cne $sourceState -or (Get-FileHash Tasks/version-requests/FDEC-099.json -Algorithm SHA256).Hash -cne $requestHash){throw 'Source or original request changed during verification'}
git diff --check
if($LASTEXITCODE -ne 0){throw 'Whitespace check failed'}
Write-Output "PASS: $($records.Count) records, immutable original request, accepted process dependency, pending gate/review and one active D002"
Write-Output "SOURCE: $ExpectedSource; STATE: $sourceState"
