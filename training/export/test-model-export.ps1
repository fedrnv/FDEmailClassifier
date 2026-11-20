param([Parameter(Mandatory=$true)][string]$OutputDirectory,[string]$LlamaCppDirectory,[switch]$ReuseObservedBuild,[string]$Python)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
if(-not $Python){$Python=Join-Path $root '.venv/export/Scripts/python.exe'}
if(-not $LlamaCppDirectory){$LlamaCppDirectory=Join-Path $root 'training/data/export-llama-cpp-29b52d3'}
$arguments=@("$PSScriptRoot/export_cli.py",'software-model-check','--output-dir',$OutputDirectory,'--llama-cpp-dir',$LlamaCppDirectory)
if($ReuseObservedBuild){$arguments+='--reuse-observed-build'}
& $Python @arguments
if($LASTEXITCODE -ne 0){throw 'Complete numerical model export/load rejected'}
& $Python "$PSScriptRoot/verify-model-check.py" --candidate-dir $OutputDirectory
if($LASTEXITCODE -ne 0){throw 'Complete numerical model provenance/release denial rejected'}
& $Python "$PSScriptRoot/verify-schema-inputs.py"
if($LASTEXITCODE -ne 0){throw 'Official schema binding changed'}
Push-Location $root
try {
    & npm exec --offline --yes --package=ajv-cli@5.0.0 -- ajv validate --strict=false -s training/data/export-sbom-schema-v2/bom-1.6.schema.json -r training/data/export-sbom-schema-v2/spdx.schema.json -r training/data/export-sbom-schema-v2/jsf-0.82.schema.json -d "$OutputDirectory/sbom.cdx.json"
    if($LASTEXITCODE -ne 0){throw 'Numerical-model SBOM schema rejected'}
} finally {Pop-Location}
Write-Output 'COMPLETE_NUMERICAL_MODEL_GGUF_EXPORT_LOAD=PASS; EMAIL_TRAINING=NOT_PERFORMED; PUBLIC_WEIGHTS=NOT_CLEARED'
