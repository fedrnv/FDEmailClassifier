# Canonical text identity preserves UTF-8 BOM and all content except CRLF -> LF.
# Binary files and text containing NUL remain exact byte identities.
function Get-IdentityHash([string]$Path) {
    $bytes=[IO.File]::ReadAllBytes($Path)
    $textFile=([IO.Path]::GetExtension($Path) -in '.md','.json','.ps1','.toml','.svg','.rs','.txt','.yml','.yaml','.c','.h','.hpp','.cpp','.js','.ts','.css','.html','.lock','.sh','.cmd','.bat') -or ((Split-Path $Path -Leaf) -in 'LICENSE','NOTICE','.gitattributes','.gitignore')
    if ($textFile) {
        $utf8=[Text.UTF8Encoding]::new($false,$true)
        $text=$utf8.GetString($bytes)
        if (!$text.Contains([string][char]0)) { $bytes=$utf8.GetBytes($text.Replace("`r`n","`n")) }
    }
    $sha=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally {$sha.Dispose()}
}
function Test-IdentityBinding([string]$Root,[string]$Path,[string]$Expected) {
    if (!$Path -or $Expected -notmatch '^[a-fA-F0-9]{64}$') { return $false }
    $rootFull=[IO.Path]::GetFullPath($Root).TrimEnd('\','/')
    $absolute=[IO.Path]::GetFullPath((Join-Path $rootFull $Path))
    if (!$absolute.StartsWith($rootFull+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or !(Test-Path -LiteralPath $absolute -PathType Leaf)) { return $false }
    $raw=(Get-FileHash -LiteralPath $absolute -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($raw -eq $Expected) { return $true }
    $canonical=Get-IdentityHash $absolute
    if ($canonical -eq $Expected) { return $true }
    $catalogPath=Join-Path $rootFull 'Tasks/policy/checkout-identities-076.json'
    if (!(Test-Path -LiteralPath $catalogPath)) { return $false }
    $catalog=Get-Content -LiteralPath $catalogPath -Raw | ConvertFrom-Json
    if ($catalog.schema -ne 'fdec-checkout-identities/v1' -or $catalog.correction_id -ne 'FDEC-076') { throw 'Invalid checkout identity catalog' }
    $relative=$absolute.Substring($rootFull.Length+1).Replace('\','/')
    $entries=@($catalog.bindings | Where-Object {$_.path -eq $relative -and $_.legacy_sha256 -eq $Expected})
    return $entries.Count -eq 1 -and $entries[0].canonical_sha256 -eq $canonical
}
