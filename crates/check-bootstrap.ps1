$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/..").Path
Push-Location $root
function Invoke-Cargo([string[]]$Arguments) {
    & cargo @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Cargo command failed: $Arguments" }
}
try {
    Invoke-Cargo @('check','--workspace','--locked','--offline')
    foreach ($package in 'fdemailclassifier-core','fdemailclassifier-ffi','fdemailclassifier-server','fdemailclassifier-example') {
        Invoke-Cargo @('build','--locked','--offline','-p',$package)
    }
    Invoke-Cargo @('build','--locked','--offline','--manifest-path','bindings/python/Cargo.toml','--target-dir','target/python')
    Invoke-Cargo @('run','--locked','--offline','--quiet','-p','fdemailclassifier-example')
    $server = Join-Path $root 'target/debug/fdemailclassifier-server.exe'
    if ($env:OS -ne 'Windows_NT') { $server = Join-Path $root 'target/debug/fdemailclassifier-server' }
    & $server --help
    if ($LASTEXITCODE -ne 0) { throw 'Server help failed' }
    & $server --version
    if ($LASTEXITCODE -ne 0) { throw 'Server version failed' }
    foreach ($invalid in @(@(), @('--serve'), @('--help','unexpected'))) {
        & $server @invalid
        if ($LASTEXITCODE -ne 2) { throw 'Invalid server invocation did not fail closed' }
    }
    $before = (Get-FileHash Cargo.lock).Hash
    $ErrorActionPreference = 'Continue'
    & cargo check --locked --offline -p fdec-nonexistent-fixture 2>$null
    $ErrorActionPreference = 'Stop'
    if ($LASTEXITCODE -eq 0) { throw 'Missing package was accepted' }
    if ((Get-FileHash Cargo.lock).Hash -ne $before) { throw 'Negative build mutated lockfile' }
    Invoke-Cargo @('deny','--manifest-path','Cargo.toml','--offline','check','licenses')
    Invoke-Cargo @('fmt','--all','--','--check')
    Write-Output 'PASS: workspace, individual crates, isolated binding, sample, negative inputs and licenses'
} finally { Pop-Location }
