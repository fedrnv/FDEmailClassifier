# FDEC-076 checkout identity acceptance

Exact tested source 91f0522159947cee46b2b9ca63cebe7cf8369c61. Parent implementation baseline 11d18c0.
Policy source 00a0d019c1e73d5ecf4c4e75c42c38497c154e50;
SHA256 ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Environment Windows PowerShell 5.1, Git 2.45.1.windows.1; local clones only.

R001-01 reproduced before repair in original frozen reviewer worktree:
admission exits 1 Policy hash mismatch on clean core.autocrlf=true checkout.
Native stderr terminated that diagnostic host as expected; no failed corrected
candidate was accepted. Source implementation committed before fresh checkout tests.

AC-01 PASS: powershell -NoProfile -File scripts/validate_tasks/test-checkout-identities.ps1
Monitor ae106f56-7699-487c-8104-5940f9cfce5f exit 0. Two fresh local clones of exact
candidate with core.autocrlf=true and false pass actual admission (policy/adoption
inventory, migration and historic closure-proof replay). Both git diff checks clean.
Owned clones run sequentially and are removed within validated temp boundaries.

AC-02 PASS: same test mutates policy text (actual admission rejects), migration-bound
text (exact identity rejects), and one PNG byte (binary identity rejects). Files
restored and admission succeeds again. No accepted source Git blob rewritten.
New .gitattributes stabilizes declared text checkout; no renormalize of accepted
history performed. New helper normalizes only UTF-8 CRLF to LF, preserving BOM,
lone CR and other content. Binary/NUL-bearing data remain byte-exact. Legacy raw
hashes are preserved; path/hash-specific equivalents in the new immutable catalog
were generated from clean source at its recorded 11d18c0 baseline. No generic
ignore-hash switch, arbitrary encoding conversion or silent pin rewrite introduced.

Direct integration PASS: scripts/validate_tasks/test-identity.ps1, monitor
dec5e6c0-77b8-47b8-b76d-c0914af3a666 exit 0, all five actual admission actions and
mapping negatives; scripts/validate_tasks/test-reopened-requests.ps1, monitor
89f3d3e1-39b6-4645-9fb3-f1c48b9dae22 exit 0, first closure preservation and invalid
new proof/duplicate/foreign evidence rejection. Fixture governing rule lists now
bind the catalog. Corrected candidate dispatch PASS; git diff --check PASS.
No broad unchanged suites rerun; full D001 gate waits for remaining corrections.

## Binding model and compatibility
New readiness should use Get-IdentityHash from scripts/validate_tasks/identity.ps1.
All root admission, migration and closure-proof consumers share Test-IdentityBinding.
New readiness must bind Tasks/policy/checkout-identities-076.json as a governing
identity source. Its current raw SHA256 is
77bcddf098ac834142f74af6e15b83e1dccd4e22440687aeca514feb60bbc451;
use canonical identity when creating portable new bindings. Accepted raw pins,
TASK/EPIC/events/evidence/proofs and requests were not edited. No normative 5.6
successor or root-rule change. Existing public asset bytes unchanged.

## Cleanup and continuation
Clean R001 detached worktree was verified to contain no unique changes and removed
with git worktree remove before creating fixture clones (one at a time). Review
artifacts remain committed in primary; original source is recoverable by SHA.
No live monitor, server or owned clone remains. Unrelated .idea preserved.
FDEC-076 verified for closure with one correction_closed request. Next fresh turn
owns FDEC-077: actual source-state binding. Then 078 accepted readiness-event binding,
079 complete AC coverage, renewed FDEC-006 gate and independent R002. No claim that
these other defects are fixed here. FDEC-007 remains Blocked, gate Planned, D001
sole Active. No external blocker, push, release or version allocation. Goal active.
