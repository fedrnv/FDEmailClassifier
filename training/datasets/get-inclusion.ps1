param([string]$Root=(Resolve-Path "$PSScriptRoot/../..").Path,[string]$DatasetId,[string]$Revision,[string]$ArtifactPath,[string]$Purpose,[string]$Target)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$receipt=& "$PSScriptRoot/assert-allowlist.ps1" -Root $Root -Action include -DatasetId $DatasetId -Revision $Revision -ArtifactPath $ArtifactPath -Purpose $Purpose -Target $Target
$receipt|ConvertTo-Json -Depth 8 -Compress
