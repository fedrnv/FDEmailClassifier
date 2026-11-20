$ErrorActionPreference='Stop'
$candidate='C:/GitHub/FDEmailClassifier-review-D001-R005'
$primary='C:/GitHub/FDEmailClassifier'
$expected='9c4f4ef1a9f8e3746ec1ef5f9b634e5d63f929f6'
$tree='de9417aedf25c107d7de9e6e95bddeabebaffd72'
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
$diff=@(git -C $candidate diff --name-only $expected ad084c200379d0598844370256432004e59bbbe3)
if($LASTEXITCODE -ne 0 -or $diff.Count -ne 9 -or @($diff|Where-Object{$_ -notmatch '^Tasks/items/quality/FDEC-006-targeted-integration-gate/(events|evidence)/'}).Count){throw 'Non-ledger candidate difference'}
if(@(git -C $candidate diff --name-only --diff-filter=MDR 5e44d21 $expected -- Tasks).Count){throw 'Historical Tasks records changed'}
$gate='Tasks/items/quality/FDEC-006-targeted-integration-gate/evidence/R005-gate-result.json'
$gateHash=BlobHash "ad084c200379d0598844370256432004e59bbbe3:$gate"
if($gateHash -ne '43b3dd395d72f7c14c7cba23db24cea492a9259d7289a5e0f345b2718e44211a'){throw 'Wrong ledger gate hash'}
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
$proofPath='Tasks/items/quality/FDEC-006-targeted-integration-gate/evidence/R005-closure-readiness.json'
if((Get-IdentityHash "$primary/$proofPath") -ne '900d99d4622075ad49b639bdd15069bd2ad064a46507bcac93d9d2f48f66131f'){throw 'Latest gate closure proof changed'}
$proof=Get-Content "$primary/$proofPath" -Raw|ConvertFrom-Json
if($proof.source_sha -ne $expected){throw 'Latest gate proof source mismatch'}
foreach($entry in $proof.verification){if(!(Test-IdentityBinding $primary $entry.path $entry.sha256)){throw 'Invalid gate verification binding'}}
if(@($proof.verification|Where-Object {$_.path -ceq $gate -and $_.sha256 -ceq $gateHash}).Count -ne 1){throw 'Gate result is absent from latest closure proof'}
if((Get-FileHash "$candidate/assets/github/social-preview.png").Hash.ToLowerInvariant() -ne 'a0e8acce656ef17ecb9c6699376a40edec3bad1ac3c6add82c22b43da7a6ed1d'){throw 'Changed preview image'}
Write-Output 'PASS: latest gate Done proof binds current candidate and exact verification; recorded preview identity preserved'
