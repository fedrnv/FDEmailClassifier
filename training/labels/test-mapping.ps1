$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Push-Location $root
$fixture=Join-Path $root ("training/outputs/mapping-schema-"+[guid]::NewGuid().ToString('N'))
try {
    & py -3.14 -m unittest discover -s training/labels -p test_mapping.py -v
    if($LASTEXITCODE -ne 0){throw 'Synthetic annotation mapping tests failed'}
    & py -3.14 training/labels/test_mapping.py --fixtures $fixture
    if($LASTEXITCODE -ne 0){throw 'Synthetic schema fixture generation failed'}
    & npm exec --offline --yes --package=ajv-cli@5.0.0 -- ajv validate --spec=draft2020 --strict=false -s schemas/annotation-mapping-v1.schema.json -r schemas/classification-v1.schema.json -d "$fixture/mapping-*.json"
    if($LASTEXITCODE -ne 0){throw 'Mapping schema rejected valid synthetic metadata'}
    & npm exec --offline --yes --package=ajv-cli@5.0.0 -- ajv validate --spec=draft2020 --strict=false -s schemas/classification-v1.schema.json -d "$fixture/classification-*.json"
    if($LASTEXITCODE -ne 0){throw 'Classification v1 rejected generated projection'}
    & npm exec --offline --yes --package=ajv-cli@5.0.0 -- ajv test --spec=draft2020 --strict=false -s schemas/annotation-mapping-v1.schema.json -r schemas/classification-v1.schema.json -d "$fixture/invalid-*.json" --invalid
    if($LASTEXITCODE -ne 0){throw 'Mapping schema accepted invalid synthetic metadata'}
    Write-Output 'PASS: annotation semantics, ambiguity/abstention, private metadata schema and existing v1 projection'
} finally {
    if(Test-Path -LiteralPath $fixture){
        $resolved=(Resolve-Path -LiteralPath $fixture).Path
        $boundary=(Join-Path $root 'training/outputs')+[IO.Path]::DirectorySeparatorChar
        $item=Get-Item -LiteralPath $resolved
        if(!$resolved.StartsWith($boundary,[StringComparison]::OrdinalIgnoreCase) -or $item.Name -notmatch '^mapping-schema-[a-f0-9]{32}$' -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unsafe synthetic fixture cleanup'}
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    Pop-Location
}
