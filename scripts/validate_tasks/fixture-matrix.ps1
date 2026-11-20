# Synthetic fixture authoring only; this does not claim real task acceptance.
. "$PSScriptRoot/acceptance-matrix.ps1"
function New-FixtureMatrix([string]$Root,[string]$TaskPath,[string]$Command) {
    $effective=Get-EffectiveCriteria $Root (Join-Path $Root $TaskPath)
    return @($effective.rows|ForEach-Object{@{id=$_.id;criterion_sha256=$_.criterion_sha256;scenario="Exercise fixture admission for $($_.id)";level='local admission contract';command=$Command;environment='Owned synthetic Git fixture';expected='Fixture-specific positive or explicit rejection outcome'}})
}
