# FDEC-238 adoption record compatibility verification

Verified exact published implementation
`2c332e1ef1c1dfdf1cc20565a40f13f225175bd9` on macOS with PowerShell
7.7.0. Developer policy 5.7 governs manual publication. The existing local
admission engine remains pinned to its qualified policy.

| Criterion | Local result |
| --- | --- |
| AC-01 | `pwsh -NoProfile -File scripts/validate_tasks/repository.ps1 -Root .` passed 117 records. The focused test confirmed one Done closure for FDEC-102, its S001 membership and validation of the original closure request. FDEC-087 still projects as Blocked. |
| AC-02 | `pwsh -NoProfile -File Tasks/items/governance/FDEC-238-fdtasks-adoption-record-compatibility/evidence/verify-adoption-compatibility.ps1 -Root .` passed. The actual repository validator rejected an unsupported FDEC-238 completion envelope and a changed FDEC-102 closure manifest committed into a disposable fixture. |

The compatibility mapping authenticates seven exact accepted files from
`aac1cc3` and normalizes only the historical specification and three known
events in memory. The closure admission check also passed against the exact three rule-file replacements accepted by FDEC-102. The direct admission fixture rejected an unexpected change to AGENTS.md. The original accepted records remained unchanged. The
focused check removed its owned local fixture. No hosted tests ran.
