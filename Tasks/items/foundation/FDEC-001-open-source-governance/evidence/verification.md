# FDEC-001 verification

Source baseline: 15d0bc8ef96b4e69a8971e65a8565b989ff967a7.
Policy SHA256: ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Windows PowerShell 5.1.26100.33296; cargo 1.98.0; cargo-deny 0.20.2.

AC-01 PASS: powershell -NoProfile -File docs/legal/test-governance.ps1
invokes the standalone verify-governance.ps1 check. Official Apache license
retrieved from https://www.apache.org/licenses/LICENSE-2.0.txt; canonical SHA256
cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30.
Manual diff inspection: all requested governance documents present, English,
original contributions Apache-2.0, safe reporting fallback, no invented private
contact address, contribution rights and redistribution restrictions explicit.
Inventory includes existing third-party FDTasks reference with unresolved rights.
No runtime dependency manifests, models or datasets exist at this source baseline.
Cargo deny: NOT APPLICABLE (no Cargo.toml); validator requires it once workspace
exists. This is not a passing dependency audit for future workspace changes.

AC-02 PASS: missing license, corrupted license, unresolved distribution and
unknown-license approval all rejected explicitly; unrelated input preserved.
Synthetic fixtures only; owned temporary directory removed in finally.
Git diff --check: PASS. Original accepted specifications untouched.
No independent review required at this item; D001 independent review remains FDEC-007.

## Limitations
FDTasks upstream has no LICENSE/COPYING in pinned tracked files. Its snapshot is
not relicensed by this project; external distribution fails closed pending rights
resolution or a reviewed exclusion plan. Local development has no such external
effect. No publishing performed, no authority or credential needed for next task.

## Candidate raw file hashes
- LICENSE: cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30
- NOTICE: f252cfc36865886b4a700cfc08077351c283dce890a735fee68ecdc58630245c
- CONTRIBUTING.md: 2855f3a722916224226669aa65562750b4e85e3a8160248d66139afe061cf8be
- CODE_OF_CONDUCT.md: 5332a6d96ca300aee95d6d46f872ced34c22601cf2569e336e224404bed9f380
- SECURITY.md: de0e63cd9a737d145917b8d6d629fddf8222204987dfbb2a56cf9686c9bff5b0
- docs/legal/inventory.json: 4e29ab4d76837844425bcc0a2c15f5cb6989ff8b14e92adf434fbeb6c40637ab
- docs/legal/test-governance.ps1: 2ac1b3a81b2ecf36c4c0bb4194bb3fa05f3fe357acf643fea4767e56095ccd37
- docs/legal/THIRD_PARTY.md: ac27287c7a234e5a872ca1934a93dc21aefef00cacbd8c21cb491fe4a0d2e5b2
- docs/legal/verify-governance.ps1: 3e312094de6bfb9fc54202cdf690ee28d7954717ea92cd0a6289b6e226b2b460

## Continuation checkpoint
FDEC-001 verified; close with a single task_closed version request. Next fresh
turn: revalidate and admit FDEC-002, bootstrap Rust workspace, and audit its exact
dependency licenses. D001 remains the only Active development Epic. No running
processes; synthetic fixture cleaned. Preserve unrelated untracked .idea files.
Standing user authority covers sequential local development; release/model
publishing still needs explicit operator authorization. Goal remains active.
