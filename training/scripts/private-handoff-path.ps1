param([Parameter(Mandatory=$true)][string]$Path,[ValidateSet('Assert','Protect')][string]$Action='Assert',[string]$OwnerToken)
$ErrorActionPreference='Stop'
$stage='inspect'
try {
    $item=Get-Item -LiteralPath $Path -Force
    if(-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Invalid private directory'}
    $user=[Security.Principal.WindowsIdentity]::GetCurrent().User
    if($Action -eq 'Protect'){
        $stage='ownership'
        if($OwnerToken -notmatch '^[a-f0-9]{64}$' -or [IO.File]::ReadAllText((Join-Path $item.FullName '.owner')) -cne $OwnerToken){throw 'Ownership token mismatch'}
        $children=@(Get-ChildItem -LiteralPath $item.FullName -Force)
        if($children.Count -ne 1 -or $children[0].Name -cne '.owner' -or $children[0].PSIsContainer -or ($children[0].Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Protect only a newly owned empty directory'}
        $acl=[Security.AccessControl.DirectorySecurity]::new()
        $acl.SetOwner($user);$acl.SetAccessRuleProtection($true,$false)
        foreach($sid in @($user,[Security.Principal.SecurityIdentifier]::new('S-1-5-18'))){
            $rule=[Security.AccessControl.FileSystemAccessRule]::new($sid,[Security.AccessControl.FileSystemRights]::FullControl,([Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit),[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
            $acl.AddAccessRule($rule)
        }
        $stage='protect'
        Set-Acl -LiteralPath $item.FullName -AclObject $acl
        # Python's Windows 0700 creation can leave an explicit OWNER RIGHTS
        # entry on the already-created marker. Replace only this new owned
        # marker ACL; retain its bytes and keep the strict principal verifier.
        $fileAcl=[Security.AccessControl.FileSecurity]::new()
        $fileAcl.SetOwner($user);$fileAcl.SetAccessRuleProtection($true,$false)
        foreach($sid in @($user,[Security.Principal.SecurityIdentifier]::new('S-1-5-18'))){
            $fileAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.AccessControlType]::Allow))
        }
        Set-Acl -LiteralPath $children[0].FullName -AclObject $fileAcl
    }
    $allowed=@($user.Value,'S-1-5-18','S-1-5-32-544')
    $pending=[Collections.Generic.Stack[object]]::new();$pending.Push($item)
    while($pending.Count){
        $current=$pending.Pop()
        $stage=if($current.PSIsContainer){'directory-access'}else{'file-access'}
        if($current.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked private artifact'}
        foreach($entry in (Get-Acl -LiteralPath $current.FullName).Access){
            if($entry.AccessControlType -ne 'Allow' -or ($entry.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly)){continue}
            if($entry.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -notin $allowed){throw 'Private path grants another principal access'}
        }
        if($current.PSIsContainer){foreach($child in Get-ChildItem -LiteralPath $current.FullName -Force){$pending.Push($child)}}
    }
    Write-Output '{"private_directory_verified":true}'
} catch {
    Write-Output "private_directory_rejected:$stage"
    exit 2
}
