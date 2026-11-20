param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{40}$')][string]$ExpectedSource)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
Push-Location $root
function Frozen {
    $head=git rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $head -ne $ExpectedSource) { throw 'Gate source identity mismatch' }
    git diff --quiet HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Gate tracked source changed' }
}
function Run-Local([string]$Path) {
    Write-Output "STAGE: $Path"
    & powershell -NoProfile -File $Path
    if ($LASTEXITCODE -ne 0) { throw "Gate stage failed: $Path" }
    Frozen
}
try {
    Frozen
    Run-Local 'crates/check-bootstrap.ps1'
    Write-Output 'STAGE: strict core contract'
    & cargo test --locked --offline -p fdemailclassifier-core schema
    if ($LASTEXITCODE -ne 0) { throw 'Core contract tests failed' }
    Run-Local 'schemas/check-schema.ps1'
    Run-Local 'docs/legal/test-governance.ps1'
    & cargo deny --offline --manifest-path bindings/python/Cargo.toml --config deny.toml check licenses
    if ($LASTEXITCODE -ne 0) { throw 'Isolated binding license audit failed' }
    Run-Local 'scripts/validate_tasks/test-validation.ps1'
    Run-Local 'scripts/validate_tasks/test-identity.ps1'
    Run-Local 'scripts/validate_tasks/check-adoption.ps1'
    $readme=[IO.File]::ReadAllText((Join-Path $root 'README.md'))
    foreach ($match in [regex]::Matches($readme,'\]\(([^)]+)\)')) {
        $link=$match.Groups[1].Value
        if ($link -notmatch '^https?://' -and !(Test-Path -LiteralPath (Join-Path $root $link))) { throw "Broken README link: $link" }
    }
    foreach ($path in 'Tasks/decisions/ADR-0001-local-inference-and-sdk-boundaries.md','docs/architecture/boundary-review.md','assets/github/social-preview.png') {
        if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing foundation artifact: $path" }
    }
    Frozen
    Write-Output "PASS: D001 changed-area integration on $ExpectedSource"
} finally { Pop-Location }
