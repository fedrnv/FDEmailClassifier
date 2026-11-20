param(
    [string]$Root=(Resolve-Path "$PSScriptRoot/../..").Path,
    [ValidateSet('validate','include')][string]$Action='validate',
    [string]$DatasetId,
    [string]$Revision,
    [string]$ArtifactPath,
    [ValidateSet('commercial_training','evaluation','redistribution')][string]$Purpose='commercial_training',
    [string]$Target
)
$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/validate_tasks/identity.ps1"
$rootPath=[IO.Path]::GetFullPath($Root).TrimEnd('\','/')
function Read-Json([string]$Path){try{return Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}catch{throw 'Missing or invalid dataset audit JSON'}}
function Fields($Value,[string[]]$Names){
    if(!$Value -or @($Value.PSObject.Properties.Name|Where-Object {$_ -cnotin $Names}).Count -or @($Names|Where-Object {$Value.PSObject.Properties.Name -cnotcontains $_}).Count){throw 'Unsupported dataset audit fields'}
}
function Read-Bound($Binding,[string]$Extension){
    Fields $Binding @('path','sha256')
    if($Binding.path -isnot [string] -or $Binding.path -cnotmatch '^docs/legal/datasets/[^/]+\.(json|md)$' -or ! $Binding.path.EndsWith($Extension,[StringComparison]::Ordinal)){throw 'Audit binding escapes its scope'}
    $absolute=[IO.Path]::GetFullPath((Join-Path $rootPath $Binding.path))
    $parent=$absolute
    while($parent.Length -gt $rootPath.Length){
        if((Test-Path -LiteralPath $parent) -and ((Get-Item -LiteralPath $parent -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Audit reparse points are unsupported'}
        $parent=Split-Path $parent
    }
    if(!(Test-Path -LiteralPath $absolute -PathType Leaf) -or !(Get-Item -LiteralPath $absolute).Length -or $Binding.sha256 -cnotmatch '^[a-f0-9]{64}$' -or (Get-IdentityHash $absolute) -cne $Binding.sha256){throw 'Dataset audit evidence changed or missing'}
    return $absolute
}
function Index-Rows($Rows){
    $index=@{}
    foreach($row in $Rows){
        if($row.id -isnot [string] -or $row.id -cnotmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' -or $index.ContainsKey($row.id) -or $row.revision -cnotmatch '^[a-f0-9]{40}$'){throw 'Invalid or duplicate dataset revision'}
        $index[$row.id]=$row
    }
    if(!$index.Count){throw 'Dataset audit is empty'}
    return $index
}
$manifest=Read-Json (Join-Path $rootPath 'training/datasets/allowlist.json')
Fields $manifest @('schema','audit','datasets')
if($manifest.schema -cne 'fdec-dataset-allowlist/v1'){throw 'Unsupported allowlist schema'}
$audit=Read-Json (Read-Bound $manifest.audit '.json')
Fields $audit @('schema','reviewed_at','reviewer','observations','report','decisions')
if($audit.schema -cne 'fdec-dataset-audit/v1' -or !$audit.reviewer -or !$audit.reviewed_at){throw 'Unreviewed dataset audit'}
$null=[DateTimeOffset]::Parse($audit.reviewed_at)
$null=Read-Bound $audit.report '.md'
$observations=Read-Json (Read-Bound $audit.observations '.json')
if($observations.schema -cne 'fdec-dataset-observations/v1'){throw 'Unsupported observation schema'}
$observed=Index-Rows $observations.datasets
$decisions=Index-Rows $audit.decisions
$selected=Index-Rows $manifest.datasets
if($observed.Count -ne $decisions.Count -or $selected.Count -ne $decisions.Count){throw 'Incomplete dataset audit coverage'}
foreach($id in $decisions.Keys){
    $decision=$decisions[$id]
    Fields $decision @('id','revision','declared_license','status','scope','allowed_purposes','artifacts','reason')
    if(!$observed.ContainsKey($id) -or !$selected.ContainsKey($id)){throw 'Unobserved dataset selection'}
    Fields $selected[$id] @('id','revision')
    $source=$observed[$id]
    if($source.revision -cne $decision.revision -or $selected[$id].revision -cne $decision.revision -or $source.declared_license -cne $decision.declared_license -or !$decision.reason){throw 'Dataset decision does not match observed source'}
    if($decision.status -cnotin 'allowed','blocked'){throw 'Unknown dataset decision'}
    if($decision.status -ceq 'blocked'){
        if(@($decision.allowed_purposes).Count -or $decision.scope){throw 'Blocked dataset contains an inclusion grant'}
    }else{
        if($decision.declared_license -cnotin 'MIT','Apache-2.0' -or $source.provenance -cne 'uploader-declared-synthetic' -or $decision.scope -cne 'specialized-email-classifier' -or !@($decision.artifacts).Count){throw 'Unresolved rights cannot be admitted'}
        if(@($decision.allowed_purposes).Count -ne 2 -or @($decision.allowed_purposes|Select-Object -Unique).Count -ne 2 -or @($decision.allowed_purposes|Where-Object {$_ -cnotin 'commercial_training','evaluation'}).Count){throw 'Unsupported dataset purpose grant'}
    }
    $seen=@{}
    foreach($artifact in $decision.artifacts){
        Fields $artifact @('path','git_blob_sha1','sha256','size')
        if($artifact.path -isnot [string] -or $artifact.path -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._/-]*$' -or @($artifact.path.Split('/')|Where-Object {$_ -in '.','..',''}).Count -or $seen.ContainsKey($artifact.path) -or $artifact.git_blob_sha1 -cnotmatch '^[a-f0-9]{40}$' -or ($artifact.size -isnot [int] -and $artifact.size -isnot [long]) -or $artifact.size -le 0){throw 'Invalid dataset artifact'}
        $seen[$artifact.path]=$true
        $observedArtifacts=@($source.artifacts|Where-Object path -CEQ $artifact.path)
        if($observedArtifacts.Count -ne 1 -or $observedArtifacts[0].git_blob_sha1 -cne $artifact.git_blob_sha1 -or $observedArtifacts[0].sha256 -cne $artifact.sha256 -or $observedArtifacts[0].size -ne $artifact.size){throw 'Artifact differs from observed source'}
        if($decision.status -ceq 'allowed' -and $artifact.sha256 -cnotmatch '^[a-f0-9]{64}$'){throw 'Allowed artifact lacks byte checksum'}
    }
}
if($Action -ceq 'validate'){
    if($DatasetId -or $Revision -or $ArtifactPath -or $Target -or $PSBoundParameters.ContainsKey('Purpose')){throw 'Use include action for dataset selection'}
    Write-Output 'PASS: dataset allowlist and bound rights evidence valid; blocked records remain excluded'
    return
}
if(!$DatasetId -or !$Revision -or !$ArtifactPath -or !$Target){throw 'Inclusion requires dataset, revision, artifact and target'}
if(!$decisions.ContainsKey($DatasetId)){throw 'Dataset is not audited'}
$decision=$decisions[$DatasetId]
if($DatasetId -cne $decision.id -or $Revision -cne $decision.revision){throw 'Dataset revision is not approved'}
if($decision.status -cne 'allowed'){throw 'Dataset inclusion blocked by unresolved rights'}
if($Target -cne $decision.scope -or $decision.allowed_purposes -cnotcontains $Purpose){throw 'Dataset target or purpose is not approved'}
$artifact=@($decision.artifacts|Where-Object path -CEQ $ArtifactPath)
if($artifact.Count -ne 1){throw 'Dataset artifact is not approved'}
# Return a pinned descriptor only. A later opt-in loader must verify downloaded
# bytes and content/privacy constraints before parsing or training.
[pscustomobject]@{schema='fdec-dataset-inclusion/v1';dataset_id=$DatasetId;revision=$Revision;artifact=$ArtifactPath;sha256=$artifact[0].sha256;size=$artifact[0].size;url="https://huggingface.co/datasets/$DatasetId/resolve/$Revision/$ArtifactPath";license=$decision.declared_license;purpose=$Purpose;target=$Target;attribution="https://huggingface.co/datasets/$DatasetId/tree/$Revision";audit_sha256=$manifest.audit.sha256}
