$ErrorActionPreference='Stop'
. "$PSScriptRoot/d002-source.ps1"
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('fdec-d002-source-'+[guid]::NewGuid())
function Reject([scriptblock]$Run,[string]$Expected){
    $failed=$false
    try{& $Run}catch{if($_.Exception.Message -match $Expected){$failed=$true}else{throw}}
    if(!$failed){throw "Expected source rejection: $Expected"}
    Write-Output "PASS: reject $Expected"
}
try{
    $null=New-Item -ItemType Directory $fixture
    git -C $fixture init --quiet
    git -C $fixture config core.autocrlf false
    [IO.File]::WriteAllText((Join-Path $fixture 'implementation.txt'),'accepted software fixture')
    git -C $fixture add implementation.txt
    git -C $fixture -c user.name=Fixture -c user.email=fixture@example.invalid commit --quiet -m fixture
    if($LASTEXITCODE -ne 0){throw 'Source fixture baseline failed'}
    $head=git -C $fixture rev-parse HEAD
    $state=Assert-D002Source $fixture $head
    Reject {Assert-D002Source $fixture ('0'*40)} 'candidate identity mismatch'
    $file=Join-Path $fixture 'implementation.txt'
    [IO.File]::WriteAllText($file,'changed working fixture')
    Reject {Assert-D002Source $fixture $head} 'tracked source differs'
    git -C $fixture add implementation.txt
    [IO.File]::WriteAllText($file,'accepted software fixture')
    Reject {Assert-D002Source $fixture $head} 'staged source differs'
    git -C $fixture restore --staged -- implementation.txt
    foreach($flag in '--assume-unchanged','--skip-worktree'){
        git -C $fixture update-index $flag implementation.txt
        Reject {Assert-D002Source $fixture $head} 'unsupported index flags'
        $undo=if($flag -eq '--assume-unchanged'){'--no-assume-unchanged'}else{'--no-skip-worktree'}
        git -C $fixture update-index $undo implementation.txt
    }
    [IO.File]::WriteAllText((Join-Path $fixture 'untracked.py'),'software fixture')
    Reject {Assert-D002Source $fixture $head} 'untracked source'
    Remove-Item -LiteralPath (Join-Path $fixture 'untracked.py')
    $own=Join-Path $fixture 'Tasks/items/quality/FDEC-013-targeted-integration-gate/evidence'
    $null=New-Item -ItemType Directory -Force $own
    [IO.File]::WriteAllText((Join-Path $own 'fixture.json'),'{}')
    $null=New-Item -ItemType Directory (Join-Path $fixture '.idea')
    [IO.File]::WriteAllText((Join-Path $fixture '.idea/workspace.xml'),'<fixture/>')
    if((Assert-D002Source $fixture $head $state) -cne $state){throw 'Owned metadata or known IDE state changed source identity'}
    [IO.File]::WriteAllText((Join-Path $fixture '.idea/other.txt'),'unrecognized fixture')
    Reject {Assert-D002Source $fixture $head} 'untracked source'
    Remove-Item -LiteralPath (Join-Path $fixture '.idea/other.txt')
    Reject {Assert-D002Source $fixture $head ('0'*64)} 'actual source state changed'
    $null=Assert-D002Source $fixture $head $state
    Write-Output 'PASS: exact candidate, independent working/index checks, hidden flags, untracked implementation and frozen-state protection'
}finally{
    $absolute=[IO.Path]::GetFullPath($fixture)
    if(!$absolute.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()),[StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $absolute -Leaf).StartsWith('fdec-d002-source-')){throw 'Unsafe source fixture cleanup'}
    if(Test-Path -LiteralPath $absolute){Remove-Item -LiteralPath $absolute -Recurse -Force}
}
