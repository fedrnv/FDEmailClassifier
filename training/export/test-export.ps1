param([string]$Python)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
if(-not $Python){$Python=Join-Path $root '.venv/export/Scripts/python.exe'}
& $Python -m unittest discover -s "$PSScriptRoot/tests" -p 'test_*.py' -v
if($LASTEXITCODE -ne 0){throw 'Export software checks failed'}
$fixture=Join-Path $root ('training/outputs/export-sbom-check-'+[guid]::NewGuid().ToString('N'))
& $Python "$PSScriptRoot/export_cli.py" software-check --output-dir $fixture
if($LASTEXITCODE -ne 0){throw 'Numerical export/SBOM generation failed'}
& $Python "$PSScriptRoot/verify-schema-inputs.py"
if($LASTEXITCODE -ne 0){throw 'Official SBOM schema binding changed'}
Push-Location $root
try {
    & npm exec --offline --yes --package=ajv-cli@5.0.0 -- ajv validate --strict=false -s training/data/export-sbom-schema-v2/bom-1.6.schema.json -r training/data/export-sbom-schema-v2/spdx.schema.json -r training/data/export-sbom-schema-v2/jsf-0.82.schema.json -d "$fixture/sbom.cdx.json"
    if($LASTEXITCODE -ne 0){throw 'SBOM schema rejected generated metadata'}
} finally {Pop-Location}
Write-Output 'EXPORT_SOFTWARE_CHECKS=PASS; TRAINED_MODEL_GGUF_LOAD=NOT_VERIFIED; PUBLIC_WEIGHTS=NOT_CLEARED'
