$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$PSScriptRoot/identity.ps1"
$candidate=git -C $root rev-parse HEAD
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-checkout-'+[guid]::NewGuid())
function Admission($checkout,[bool]$Reject=$false) {
    $output=& powershell -NoProfile -File "$checkout/scripts/validate_tasks/admission.ps1" -Root $checkout 2>&1
    if($Reject){if($LASTEXITCODE -eq 0){throw 'Tampered checkout admitted'}}elseif($LASTEXITCODE -ne 0){throw ($output -join "`n")}
}
try {
    New-Item -ItemType Directory $temp|Out-Null
    foreach($mode in 'true','false') {
        $checkout=Join-Path $temp "checkout-$mode"
        & git clone --quiet --shared --no-checkout $root $checkout
        if($LASTEXITCODE -ne 0){throw 'Fixture clone failed'}
        & git -C $checkout config core.autocrlf $mode
        & git -C $checkout checkout --quiet --detach $candidate
        if($LASTEXITCODE -ne 0){throw 'Fixture checkout failed'}
        Admission $checkout
        & git -C $checkout diff --quiet HEAD
        if($LASTEXITCODE -ne 0){throw 'Fresh checkout source differs'}
        $policy=Join-Path $checkout 'Tasks/policy/upstream-5.6.md'
        $bytes=[IO.File]::ReadAllBytes($policy)
        [IO.File]::AppendAllText($policy,'tamper')
        # Native stderr from expected failures must not terminate the host early.
        $saved=$ErrorActionPreference;$ErrorActionPreference='Continue'
        try{Admission $checkout $true}finally{$ErrorActionPreference=$saved}
        [IO.File]::WriteAllBytes($policy,$bytes)
        $migration=Get-Content "$checkout/Tasks/migrations/FDEC-074.json" -Raw|ConvertFrom-Json
        $retained=Join-Path $checkout $migration.retained.path
        $original=[IO.File]::ReadAllBytes($retained)
        [IO.File]::AppendAllText($retained,'tamper')
        if(Test-IdentityBinding $checkout $migration.retained.path $migration.retained.sha256){throw 'Text mutation matched legacy alias'}
        [IO.File]::WriteAllBytes($retained,$original)
        $binary='assets/github/social-preview.png'
        $binaryPath=Join-Path $checkout $binary
        $original=[IO.File]::ReadAllBytes($binaryPath)
        $hash=Get-IdentityHash $binaryPath
        $mutated=$original.Clone();$mutated[100]=$mutated[100] -bxor 1
        [IO.File]::WriteAllBytes($binaryPath,$mutated)
        if(Test-IdentityBinding $checkout $binary $hash){throw 'Binary mutation accepted'}
        [IO.File]::WriteAllBytes($binaryPath,$original)
        Admission $checkout
        Write-Output "PASS: clean core.autocrlf=$mode checkout, legacy proof replay and text/binary rejection on $candidate"
        # One disposable verification checkout at a time.
        $resolved=[IO.Path]::GetFullPath($checkout)
        if(!$resolved.StartsWith([IO.Path]::GetFullPath($temp)+[IO.Path]::DirectorySeparatorChar)){throw 'Unsafe fixture cleanup'}
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
} finally {
    $resolved=[IO.Path]::GetFullPath($temp);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-checkout-')){throw 'Unsafe cleanup target'}
    if(Test-Path $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
