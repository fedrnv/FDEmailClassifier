param([switch]$CheckoutOnly,[switch]$ValidationOnly)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../../../..").Path
Push-Location $root
try{
    if($CheckoutOnly -and $ValidationOnly){throw 'Select one verification phase'}
    if($CheckoutOnly){$checks=@('test-checkout-identities.ps1')}elseif($ValidationOnly){$checks=@('test-validation.ps1','test-epic-closure.ps1')}else{$checks=@('test-plan-sync.ps1','test-identity.ps1','test-validation.ps1','test-epic-closure.ps1')}
    if(!$CheckoutOnly -and !$ValidationOnly){
        & py -3.14 "$PSScriptRoot/verify-owner-plan.py"
        if($LASTEXITCODE -ne 0){throw 'Pinned upstream/source comparison failed'}
    }
    foreach($check in $checks){
        & powershell -NoProfile -File "$root/scripts/validate_tasks/$check"
        if($LASTEXITCODE -ne 0){throw "Local process verification failed: $check"}
    }
    Write-Output 'PASS: FDEC-088 selected local checks completed'
}finally{Pop-Location}
