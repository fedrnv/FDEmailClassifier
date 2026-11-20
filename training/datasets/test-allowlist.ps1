$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../..").Path
$guard=Join-Path $PSScriptRoot 'assert-allowlist.ps1'
. "$PSScriptRoot/../../scripts/validate_tasks/identity.ps1"
$temp=Join-Path ([IO.Path]::GetTempPath()) ('fdec-dataset-audit-'+[guid]::NewGuid())
$files=@('training/datasets/allowlist.json','docs/legal/datasets/audit-2026-11-20.json','docs/legal/datasets/sources-2026-11-20.json','docs/legal/datasets/audit-2026-11-20.md')
$baseline=@{}
foreach($path in $files){$baseline[$path]=[IO.File]::ReadAllBytes((Join-Path $root $path))}
function Restore-Fixture {
    foreach($path in $files){$full=Join-Path $temp $path;$null=New-Item -ItemType Directory (Split-Path $full) -Force;[IO.File]::WriteAllBytes($full,$baseline[$path])}
}
function Snapshot {
    return (($files|ForEach-Object {$full=Join-Path $temp $_;if(Test-Path -LiteralPath $full){(Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash}else{'MISSING'}}) -join ':')
}
function Invoke-ReadOnly($Parameters){
    $before=Snapshot
    try {& $guard -Root $temp @Parameters} finally {if((Snapshot) -ne $before){throw 'Dataset guard mutated its inputs'}}
}
function Json([string]$Path,$Value){$Value|ConvertTo-Json -Depth 30|Set-Content (Join-Path $temp $Path) -Encoding UTF8}
function Edit-Audit([scriptblock]$Change){
    $audit=Get-Content "$temp/docs/legal/datasets/audit-2026-11-20.json" -Raw|ConvertFrom-Json
    & $Change $audit
    Json 'docs/legal/datasets/audit-2026-11-20.json' $audit
    $manifest=Get-Content "$temp/training/datasets/allowlist.json" -Raw|ConvertFrom-Json
    $manifest.audit.sha256=Get-IdentityHash "$temp/docs/legal/datasets/audit-2026-11-20.json"
    Json 'training/datasets/allowlist.json' $manifest
}
function Reject([string]$Label,$Parameters,[scriptblock]$Change,[string]$Pattern){
    Restore-Fixture
    if($Change){& $Change}
    $failed=$false
    try {$null=Invoke-ReadOnly $Parameters} catch {if($_.Exception.Message -match $Pattern){$failed=$true}else{throw}}
    if(!$failed){throw "Expected rejection: $Label"}
    Write-Output "PASS: reject $Label without input mutation"
}
$seed=@{Action='include';DatasetId='weijianzhg/email-triage-action-seed';Revision='8c98baa8b10a1dddd676c860d9e1b86c89141c38';ArtifactPath='data/train.parquet';Purpose='commercial_training';Target='specialized-email-classifier'}
try {
    $null=New-Item -ItemType Directory $temp
    Restore-Fixture
    $null=Invoke-ReadOnly @{}
    $receipt=Invoke-ReadOnly $seed
    if($receipt.schema -cne 'fdec-dataset-inclusion/v1' -or $receipt.sha256 -cne '9ea7c656d016012f7e800a9612d399114ca081bfcbdce4101d1999cb6c293854' -or $receipt.size -ne 1103958 -or $receipt.url -cne 'https://huggingface.co/datasets/weijianzhg/email-triage-action-seed/resolve/8c98baa8b10a1dddd676c860d9e1b86c89141c38/data/train.parquet'){throw 'Unpinned or incorrect approval descriptor'}
    $evaluation=$seed.Clone();$evaluation.Purpose='evaluation';$null=Invoke-ReadOnly $evaluation
    Write-Output 'PASS: complete three-source registry valid; pinned scoped seed training/evaluation descriptor only'
    $parameters=$seed.Clone();$parameters.DatasetId='imnim/multiclass-email-classification';$parameters.Revision='e95090f0bb6dae0b05c9cd6db314dcae1d40db3f';$parameters.ArtifactPath='email_dataset.json'
    Reject 'MIT-tagged source with unresolved provenance' $parameters $null 'inclusion blocked by unresolved rights'
    $parameters=$seed.Clone();$parameters.DatasetId='talby/spamassassin';$parameters.Revision='a1b3371d2df15575f766c081cb329543955d27f6';$parameters.ArtifactPath='spamassassin.py'
    Reject 'unknown-license real-mail corpus' $parameters $null 'inclusion blocked by unresolved rights'
    $parameters=$seed.Clone();$parameters.DatasetId='fixture/unknown';Reject 'unknown source' $parameters $null 'not audited'
    foreach($revision in 'main',('0'*40)){$parameters=$seed.Clone();$parameters.Revision=$revision;Reject "unapproved revision $revision" $parameters $null 'revision is not approved'}
    foreach($path in 'messages.jsonl','../outside.parquet'){$parameters=$seed.Clone();$parameters.ArtifactPath=$path;Reject "unapproved artifact $path" $parameters $null 'artifact is not approved'}
    $parameters=$seed.Clone();$parameters.Purpose='redistribution';Reject 'redistribution' $parameters $null 'target or purpose is not approved'
    $parameters=$seed.Clone();$parameters.Target='general-purpose-chat';Reject 'general model target' $parameters $null 'target or purpose is not approved'
    $parameters=$seed.Clone();$parameters.Remove('Target');Reject 'missing target' $parameters $null 'requires dataset, revision, artifact and target'
    Reject 'selection under validate action' @{DatasetId=$seed.DatasetId} $null 'Use include action'
    Reject 'missing audit' @{} {Remove-Item -LiteralPath "$temp/docs/legal/datasets/audit-2026-11-20.json"} 'evidence changed or missing'
    Reject 'changed report' @{} {[IO.File]::AppendAllText("$temp/docs/legal/datasets/audit-2026-11-20.md",'tamper')} 'evidence changed or missing'
    Reject 'changed observations' @{} {[IO.File]::AppendAllText("$temp/docs/legal/datasets/sources-2026-11-20.json",' ')} 'evidence changed or missing'
    Reject 'escaping audit binding' @{} {$m=Get-Content "$temp/training/datasets/allowlist.json" -Raw|ConvertFrom-Json;$m.audit.path='../outside.json';Json 'training/datasets/allowlist.json' $m} 'binding escapes'
    Reject 'duplicate source' @{} {$m=Get-Content "$temp/training/datasets/allowlist.json" -Raw|ConvertFrom-Json;$m.datasets+=@($m.datasets[0]);Json 'training/datasets/allowlist.json' $m} 'Invalid or duplicate dataset revision'
    Reject 'omitted audit source' @{} {$m=Get-Content "$temp/training/datasets/allowlist.json" -Raw|ConvertFrom-Json;$m.datasets=@($m.datasets|Where-Object id -CNE 'talby/spamassassin');Json 'training/datasets/allowlist.json' $m} 'Incomplete dataset audit coverage'
    Reject 'license substituted in reviewed record' @{} {Edit-Audit {param($a)($a.decisions|Where-Object id -CEQ $seed.DatasetId).declared_license='MIT'}} 'does not match observed source'
    Reject 'artifact checksum substituted in reviewed record' @{} {Edit-Audit {param($a)($a.decisions|Where-Object id -CEQ $seed.DatasetId).artifacts[0].sha256=('0'*64)}} 'Artifact differs from observed source'
    foreach($id in 'imnim/multiclass-email-classification','talby/spamassassin'){
        Reject "promoted unresolved record $id" @{} {Edit-Audit {param($a)$row=$a.decisions|Where-Object id -CEQ $id;$row.status='allowed';$row.scope='specialized-email-classifier';$row.allowed_purposes=@('commercial_training','evaluation')}} 'Unresolved rights cannot be admitted'
    }
    Reject 'unknown decision status' @{} {Edit-Audit {param($a)$a.decisions[0].status='maybe'}} 'Unknown dataset decision'
    Reject 'malformed manifest' @{} {[IO.File]::WriteAllText("$temp/training/datasets/allowlist.json",'{broken')} 'Missing or invalid dataset audit JSON'
    Restore-Fixture
    $null=Invoke-ReadOnly @{}
    $null=Invoke-ReadOnly $seed
    Write-Output 'PASS: positive/negative rights admission complete; no corpus download, training or publication'
} finally {
    $resolved=[IO.Path]::GetFullPath($temp);$parent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if(!$resolved.StartsWith($parent,[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('fdec-dataset-audit-')){throw 'Unsafe cleanup target'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
