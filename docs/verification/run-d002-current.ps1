param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{40}$')][string]$ExpectedSource)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
. "$root/scripts/verification/d002-source.ps1"
. "$PSScriptRoot/d002-current-result.ps1"
$script:currentFrozen=$null
function Current-Frozen {
    $state=Assert-D002Source $root $ExpectedSource $script:currentFrozen
    if(!$script:currentFrozen){$script:currentFrozen=$state}
}
Push-Location $root
try {
    Current-Frozen
    Write-Output 'STAGE: effective outcome and audited source continuity'
    $outcomeLines=@(& powershell -NoProfile -File docs/verification/verify-d002-outcome-v2.ps1 -TestNegatives)
    $outcomeExit=$LASTEXITCODE
    Write-Output $outcomeLines
    if($outcomeExit -ne 0){throw 'Current D002 outcome verification failed'}
    $outcome=($outcomeLines -join "`n")|ConvertFrom-Json
    Current-Frozen
    Write-Output 'COMPONENT: unchanged eight-stage D002 integration'
    $lines=[Collections.Generic.List[string]]::new()
    & powershell -NoProfile -File scripts/verification/D002.ps1 -ExpectedSource $ExpectedSource | ForEach-Object {
        $line=[string]$_;$lines.Add($line)
        # An inner PASS is component evidence, never the current gate result.
        if($line -ceq 'GATE_RESULT_BEGIN'){Write-Output 'COMPONENT_GATE_RESULT_BEGIN'}
        elseif($line -ceq 'GATE_RESULT_END'){Write-Output 'COMPONENT_GATE_RESULT_END'}
        else {Write-Output $line}
    }
    $componentExit=$LASTEXITCODE
    if($componentExit -ne 0){throw 'Current D002 component integration failed'}
    Current-Frozen
    $matches=[regex]::Matches(($lines -join "`n"),'(?ms)^GATE_RESULT_BEGIN\r?\n(.*?)^GATE_RESULT_END\r?$')
    if($matches.Count -ne 1){throw 'Missing or ambiguous component gate result'}
    $component=$matches[0].Groups[1].Value|ConvertFrom-Json
    $expected=@{candidate_sha=$ExpectedSource;candidate_tree=@(D002-Git $root @('rev-parse',($ExpectedSource+'^{tree}')))[0];policy_sha256=(Get-Content Tasks/policy/adoption-5.6.json -Raw|ConvertFrom-Json).policy_sha256;source_state_sha256=$script:currentFrozen}
    $bindings=@('docs/verification/run-d002-current.ps1','docs/verification/d002-current-result.ps1','scripts/verification/D002.ps1','docs/verification/verify-d002-outcome-v2.ps1'|ForEach-Object {@{path=$_;sha256=(Get-IdentityHash (Join-Path $root $_))}})
    $result=New-D002CurrentResult $outcome $component $expected $bindings
    Current-Frozen
    Write-Output 'GATE_RESULT_BEGIN'
    $result|ConvertTo-Json -Depth 20
    Write-Output 'GATE_RESULT_END'
    Write-Output "PASS: current nine-stage D002 gate on $ExpectedSource"
} finally {Pop-Location}
