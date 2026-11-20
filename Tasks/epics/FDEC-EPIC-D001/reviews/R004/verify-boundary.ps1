$ErrorActionPreference='Stop'
$candidate='C:/GitHub/FDEmailClassifier-review-D001-R004'
$primary='C:/GitHub/FDEmailClassifier'
$expected='ed9cb62bda2856c21f0ff9c4c874a743d0d90a2e'
$tree='d3529de9fa1de411519d91f1ca8624ca55e2720b'
function BlobHash([string]$Spec) {
    $start=New-Object Diagnostics.ProcessStartInfo
    $start.FileName='git'; $start.Arguments="-C $candidate show $Spec"
    $start.UseShellExecute=$false; $start.RedirectStandardOutput=$true
    $process=[Diagnostics.Process]::Start($start)
    $bytes=New-Object IO.MemoryStream
    try {
        $process.StandardOutput.BaseStream.CopyTo($bytes); $process.WaitForExit()
        if($process.ExitCode -ne 0){throw 'Cannot read pinned Git blob'}
        $sha=[Security.Cryptography.SHA256]::Create()
        try{return ([BitConverter]::ToString($sha.ComputeHash($bytes.ToArray()))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
    } finally {$bytes.Dispose();$process.Dispose()}
}
if((git -C $candidate rev-parse HEAD) -ne $expected){throw 'Wrong candidate'}
if((git -C $candidate rev-parse 'HEAD^{tree}') -ne $tree){throw 'Wrong tree'}
if(@(git -C $candidate status --porcelain).Count){throw 'Candidate is dirty'}
$diff=@(git -C $candidate diff --name-only $expected a2620ff)
if($LASTEXITCODE -ne 0 -or $diff.Count -ne 9 -or @($diff|Where-Object{$_ -notmatch '^Tasks/items/quality/FDEC-006-targeted-integration-gate/(events|evidence)/'}).Count){throw 'Non-ledger candidate difference'}
if(@(git -C $candidate diff --name-only --diff-filter=MDR 5e44d21 $expected -- Tasks).Count){throw 'Historical Tasks records changed'}
$gate='Tasks/items/quality/FDEC-006-targeted-integration-gate/evidence/R004-gate-result.json'
$gateHash=BlobHash "a2620ff:$gate"
if($gateHash -ne 'fe0064cfeddc17eb36a2756d3df9b7e826a1f1b96608b8d76ed90eee09308b49'){throw 'Wrong ledger gate hash'}
. "$candidate/scripts/validate_tasks/identity.ps1"
if((Get-IdentityHash "$primary/$gate") -ne $gateHash){throw 'Primary gate differs from ledger'}
$policy=(Get-FileHash "$candidate/Tasks/policy/upstream-5.6.md").Hash.ToLowerInvariant()
if($policy -ne 'ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403'){throw 'Wrong policy'}
$request='Tasks/version-requests/FDEC-006.json'
if((BlobHash "868a368:$request") -ne (BlobHash "$($expected):$request")){throw 'First closure request changed'}
Write-Output "PASS: candidate $expected tree $tree; clean candidate"
Write-Output 'PASS: ledger diff is nine FDEC-006 events/evidence paths; historical Tasks records preserved'
Write-Output "PASS: ledger gate blob and canonical primary identity $gateHash"
Write-Output "PASS: policy raw bytes $policy; original gate first-closure request preserved"
