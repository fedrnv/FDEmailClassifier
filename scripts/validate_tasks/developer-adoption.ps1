# Read-only compatibility for the accepted FDEC-102 records in aac1cc3.
# These identities do not qualify new claim or closure formats.
function Get-AcceptedDeveloperAdoption([string]$Root) {
    $item = 'Tasks/items/governance/FDEC-102-adopt-fdtasks-5-7'
    $membership = 'Tasks/epics/FDEC-EPIC-S001/events/20261121-FDEC-102-member-added.md'
    $request = 'Tasks/version-requests/20261121-FDEC-102-fdtasks57.json'
    $hashes = @{
        "$item/TASK.md" = 'a6cf805eb68ecba5ea4e3907c8b42eccda2a9d5da78c8e1d27efa8d975aaaebf'
        "$item/events/20261121-01-published-claim.md" = 'd907c912f6d1a8d3b1bb2960dbe1e2b04366fbacf615e4751138d3822def96ad'
        "$item/events/20261121-02-verified-done.md" = '2b8d0ab0d51ef9088a402f0e6d75e2b701c970f8df38fc48dda7eb2aa781e52e'
        "$item/evidence/20261121-closure.json" = '964a293084a4feb5a987f63f5de6a8d866519e1cd2f0165b3740aa1caaa77397'
        "$item/evidence/20261121-fdtasks57-verification.json" = '0476c136705e973a6ec2343e0864fe18c6c07134c910b3a8609ae5a00fe977e3'
        $membership = 'a8aa1a12b48642ca2b4b21ef71ee1c55612e5bfd101a2320017133191a86641a'
        $request = '0b1ddd8e4f5dd7e29bab9dcecf4d156f28fb82c5f9cecbdda033d53af5a390de'
    }
    foreach ($relative in $hashes.Keys) {
        $file = Join-Path $Root $relative
        if (!(Test-Path -LiteralPath $file -PathType Leaf) -or (Get-IdentityHash $file) -cne $hashes[$relative]) {
            throw "Accepted developer adoption identity changed: $relative"
        }
    }
    return @{
        (Join-Path $Root "$item/TASK.md") = 'atomicity'
        (Join-Path $Root "$item/events/20261121-01-published-claim.md") = 'status'
        (Join-Path $Root "$item/events/20261121-02-verified-done.md") = 'status'
        (Join-Path $Root $membership) = 'membership'
    }
}

function Convert-AcceptedDeveloperAdoption([hashtable]$Record, [hashtable]$Adoption) {
    switch ($Adoption[$Record.path]) {
        'atomicity' {
            $inline = '(?m)^atomicity: (\{[^\r\n]+\})\r?$'
            $mapping = [regex]::Match($Record.front, $inline).Groups[1].Value | ConvertFrom-Json
            $outcomes = ConvertTo-Json -InputObject $mapping.outcomes -Compress
            $packets = ConvertTo-Json -InputObject $mapping.packets -Compress
            $independent = ConvertTo-Json -InputObject $mapping.independent_acceptance -Compress
            $definition = @"
atomicity:
  outcomes: $outcomes
  packets: $packets
  independent_acceptance: $independent
  boundary_reason: $($mapping.boundary_reason)
"@
            $Record.front = [regex]::Replace($Record.front, $inline, $definition)
        }
        'status' {
            $from = (Field $Record.front 'status_from').Replace('In Progress', 'InProgress')
            $to = (Field $Record.front 'status_to').Replace('In Progress', 'InProgress')
            $Record.front = $Record.front -replace '(?m)^event_type: "completed"\r?$', 'event_type: status-changed'
            $Record.text += "`n$from -> $to`n"
        }
        'membership' {
            $member = Field $Record.front 'work_item_id'
            $Record.text += "`nAdd $member`n"
        }
    }
}

# FDEC-102 superseded three files also tracked by the historical 5.6 pin.
# Recognize the exact previous/current pair without changing either policy pin.
function Test-AcceptedDeveloperAdoptionRule([string]$Root, [string]$Path, [string]$Previous) {
    $rules = @{
        'AGENTS.md' = @(
            '43d73ff4c10734dcf7e7710ea7982783d622c29cdf6b2897975a432b5ba8034c',
            'aaa901406e3c6cffba39c1a4fff062372503bdad6b2202e5206d6a360719a46f'
        )
        'DEVELOPMENT.md' = @(
            '7de6ccfcacd00f54dbdcd071701ad87ef66c20407d4cb16b73c336526c17e2b8',
            '5b9fbf008408938c12bc44c6ebe6ecdb9c4ecb5ca13b5ee9b120796675301813'
        )
        'Tasks/AGENTS.md' = @(
            'cf5e70942475a43772dee0472b0ce6d3c3189c71f3981484fa59d8c53d48582d',
            '3d6bfd005f51e33cd1defeb809e7fd05ee88f5a309a092478c7ee368eb33c16d'
        )
    }
    $pair = $rules[$Path]
    if (!$pair -or $Previous -cne $pair[0]) { return $false }
    $file = Join-Path $Root $Path
    return (Test-Path -LiteralPath $file -PathType Leaf) -and (Get-IdentityHash $file) -ceq $pair[1]
}
