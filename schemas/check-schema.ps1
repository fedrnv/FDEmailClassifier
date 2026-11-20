$ErrorActionPreference = 'Stop'
Push-Location (Resolve-Path "$PSScriptRoot/..").Path
try {
    & npm exec --yes --package=ajv-cli@5.0.0 -- ajv validate --spec=draft2020 --strict=false -s schemas/classification-v1.schema.json -d 'schemas/examples/*.json'
    if ($LASTEXITCODE -ne 0) { throw 'Valid JSON Schema fixture rejected' }
    & npm exec --yes --package=ajv-cli@5.0.0 -- ajv test --spec=draft2020 --strict=false -s schemas/classification-v1.schema.json -d 'schemas/invalid/*.json' --invalid
    if ($LASTEXITCODE -ne 0) { throw 'Invalid JSON Schema fixture accepted' }
} finally { Pop-Location }
