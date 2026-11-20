. "$PSScriptRoot/identity.ps1"
function Get-SourceState([string]$Root,[string]$TaskId) {
    if ($TaskId -notmatch '^FDEC-[0-9]{3}$') { throw 'Invalid source-state task identity' }
    $rootFull=[IO.Path]::GetFullPath($Root).TrimEnd('\','/')
    $tracked=@(git -C $Root -c core.quotepath=false ls-files --cached)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate tracked source' }
    $other=@(git -C $Root -c core.quotepath=false ls-files --others --exclude-standard)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate new source' }
    $trackedSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($path in $tracked) { $null=$trackedSet.Add($path) }
    $paths=[string[]]@(@($tracked)+@($other) | Select-Object -Unique)
    [Array]::Sort($paths,[StringComparer]::Ordinal)
    $records=[Text.StringBuilder]::new()
    $index=@(git -C $Root -c core.quotepath=false ls-files --stage)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate source index' }
    foreach ($entry in $index) {
        if ($entry -notmatch '^(100644|100755|120000) ([a-f0-9]{40}) 0\t(.+)$') { throw 'Unsupported or unmerged source index entry' }
        $path=$matches[3]
        if ($path -match "^Tasks/items/[^/]+/$TaskId-[^/]+/(events|evidence)/" -or $path -eq "Tasks/version-requests/$TaskId.json") { continue }
        $null=$records.Append('index:').Append($entry).Append("`n")
    }
    foreach ($path in $paths) {
        # Only this task's append-only bookkeeping and unrelated untracked IDE
        # state are excluded. No caller-supplied arbitrary exclusion list exists.
        if ($path -match "^Tasks/items/[^/]+/$TaskId-[^/]+/(events|evidence)/" -or $path -eq "Tasks/version-requests/$TaskId.json") { continue }
        if (!$trackedSet.Contains($path) -and $path -match '^\.idea/(workspace\.xml|vcs\.xml|modules\.xml|misc\.xml|\.gitignore|[^/]+\.iml|inspectionProfiles/[^/]+\.xml)$') { continue }
        if ($path -match '[\x00-\x1f]' -or $path.StartsWith('"')) { throw 'Unsupported source path encoding' }
        $absolute=[IO.Path]::GetFullPath((Join-Path $rootFull $path))
        if (!$absolute.StartsWith($rootFull+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Source path escapes root' }
        $parent=$absolute
        while ($parent.Length -gt $rootFull.Length) {
            if (Test-Path -LiteralPath $parent) {
                if ((Get-Item -LiteralPath $parent -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Source reparse points require explicit support' }
            }
            $parent=Split-Path $parent
        }
        $hash=if(Test-Path -LiteralPath $absolute -PathType Leaf){Get-IdentityHash $absolute}else{'MISSING'}
        $null=$records.Append($path).Append([char]0).Append($hash).Append("`n")
    }
    $sha=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($records.ToString())))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
}
