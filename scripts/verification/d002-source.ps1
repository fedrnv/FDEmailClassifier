. "$PSScriptRoot/../validate_tasks/source-state.ps1"
function D002-Git([string]$Root,[string[]]$Arguments) {
    $output=@(& git -C $Root -c core.quotepath=false @Arguments)
    if($LASTEXITCODE -ne 0){throw 'D002 Git source inspection failed'}
    return $output
}
function Assert-D002Source([string]$Root,[string]$ExpectedSource,[string]$FrozenState='') {
    if($ExpectedSource -cnotmatch '^[a-f0-9]{40}$' -or (D002-Git $Root @('rev-parse','HEAD')) -cne $ExpectedSource){throw 'D002 candidate identity mismatch'}
    $index=@(D002-Git $Root @('ls-files','--stage'))
    if(@($index | Where-Object {$_ -cnotmatch '^(100644|100755) [a-f0-9]{40} 0\t[^\x00-\x1f"]+$'}).Count){throw 'D002 unsupported or unmerged index'}
    $flags=@(D002-Git $Root @('ls-files','-v'))
    if(@($flags | Where-Object {$_ -cnotmatch '^H '}).Count){throw 'D002 unsupported index flags'}
    & git -C $Root diff --quiet --no-ext-diff HEAD
    if($LASTEXITCODE -ne 0){throw 'D002 tracked source differs from candidate'}
    & git -C $Root diff --cached --quiet --no-ext-diff HEAD
    if($LASTEXITCODE -ne 0){throw 'D002 staged source differs from candidate'}
    foreach($path in @(D002-Git $Root @('ls-files','--others','--exclude-standard'))){
        $own=$path -match '^Tasks/items/quality/FDEC-013-targeted-integration-gate/(events|evidence)/' -or $path -eq 'Tasks/version-requests/FDEC-013.json'
        $ide=$path -match '^\.idea/(workspace\.xml|vcs\.xml|modules\.xml|misc\.xml|\.gitignore|[^/]+\.iml|inspectionProfiles/[^/]+\.xml)$'
        if(!$own -and !$ide){throw 'D002 untracked source is outside frozen candidate'}
    }
    $state=Get-SourceState $Root 'FDEC-013'
    if($FrozenState -and $state -cne $FrozenState){throw 'D002 actual source state changed'}
    return $state
}
