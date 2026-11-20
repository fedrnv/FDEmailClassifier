param([Parameter(Mandatory=$true)][string]$ExpectedSource)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
. "$root/scripts/verification/d002-source.ps1"
Set-Location $root
$state=Assert-D002Source $root $ExpectedSource
$requestHash=(Get-FileHash Tasks/version-requests/FDEC-013.json -Algorithm SHA256).Hash
$worktrees=@(D002-Git $root @('worktree','list','--porcelain')) -join "`n"
& powershell -NoProfile -File docs/verification/test-d002-current-result.ps1
if($LASTEXITCODE -ne 0){throw 'Current gate composition preflight failed'}
# Capture the deliberately failing native process without treating stderr as a
# terminating parent error; require its actual exit and expected early failure.
$ErrorActionPreference='Continue'
$rejected=@(& powershell -NoProfile -File docs/verification/run-d002-current.ps1 -ExpectedSource ('0'*40) 2>&1)
$code=$LASTEXITCODE
$ErrorActionPreference='Stop'
$text=($rejected|ForEach-Object {$_.ToString()}) -join "`n"
if($code -eq 0 -or !$text.Contains('D002 candidate identity mismatch') -or $text.Contains('GATE_RESULT_BEGIN')){throw 'Wrong candidate did not reject before gate output'}
if((Assert-D002Source $root $ExpectedSource $state) -cne $state -or (Get-FileHash Tasks/version-requests/FDEC-013.json -Algorithm SHA256).Hash -cne $requestHash -or ((@(D002-Git $root @('worktree','list','--porcelain')) -join "`n") -cne $worktrees)){throw 'Preflight changed source, original request or worktrees'}
Write-Output 'PASS: wrong actual candidate rejects before outcome/component execution; source, original request and worktrees unchanged'
Write-Output "SOURCE: $ExpectedSource; STATE: $state"
