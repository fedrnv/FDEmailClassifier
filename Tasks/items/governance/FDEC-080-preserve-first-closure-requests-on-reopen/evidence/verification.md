# FDEC-080 verified first-closure history repair

Baseline cc217884c2bdc32e3326791bb500473fae3d185d. Policy source 00a0d019c1e73d5ecf4c4e75c42c38497c154e50;
SHA256 ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Windows PowerShell 5.1 and local Git; synthetic owned fixtures only.

Original actual failure reproduced: powershell -NoProfile -File
scripts/validate_tasks/repository.ps1 => Invalid closed item request for reopened
gate with preserved first-closure request. After repair same command PASS (92
records). Historical Done transition is separate from current state. Duplicate
request/item identity precheck is order-independent. Request parent/type and owned
nonempty evidence checked. New first requests require exact hash-bound closure
proof on first Done transition; recorded legacy requests retain immutable authority.

AC-01 PASS: powershell -NoProfile -File scripts/validate_tasks/test-reopened-requests.ps1
Monitor 5292f426-4c5c-405d-acea-824b7bf264ef exit 0. Reopen/reclose/reopen succeeds
without changing original gate request. Valid new hash-bound proof accepted.
AC-02 PASS: same script rejects never-closed work, duplicate request, fabricated
Done without proof, modified proof evidence, wrong parent and foreign evidence.
Initial candidate diagnostic exposed duplicate directory-order handling (new
unverified duplicate rejected before existing request); made duplicate identity
validation order-independent, then passed. No unchanged failing candidate accepted.

Direct affected integration: powershell -NoProfile -File
scripts/validate_tasks/test-identity.ps1, monitor aac27e47-ee25-41aa-9a1b-2998f245edc1,
exit 0. All five claim/dispatch/resume/execute/close paths PASS on current valid
fixture despite reopened gate request; invalid mappings still reject. The fixture
now commits its historical requests explicitly rather than passing them as new
unverified claims. No broad unchanged suite selected. Repaired actual FDEC-080
dispatch PASS, current root repository PASS. Git diff --check PASS.

Original FDEC-006 request raw SHA256 remains
bad997f4843a2063b0a2884ac1b2173309187c9bf3adc9c3ec1aa363ab8a406b.
No second gate/review request, version allocation, external push, release or policy
rewrite. Source diff manually inspected. Proof mechanical provenance does not
replace actual focused acceptance or independent Epic review. Known R001 findings
remain; none is claimed fixed by this separate process repair.

## Candidate source hashes
- scripts/validate_tasks/repository.ps1: 3a61510493758f4ada44dbbec7e3f79b5b9bd5c3e40f0a1fb51ebc33cac58b15
- scripts/validate_tasks/test-reopened-requests.ps1: 97a5f909be04ae29d8bfdcb31ad5a49f54e0549559c5f848c5454be60089233a
- scripts/validate_tasks/test-identity.ps1: cf6e64eb5853899191395173ce59255d25ea7d0139426d43ee51b9eea77974e1
- scripts/validate_tasks/README.md: 99b2bcc084f7a7ff7ae52670e18aae17b869c325c1fba4eba651e3c722fd33c2

## Exact interrupted-work continuation
FDEC-080 verified for closure with one correction_closed request. Revalidated
interrupted FDEC-007 checkpoint: R001 ChangesRequired unchanged; FDEC-006 Planned;
D001 findings 076..079 queued and implementation not accepted. Next fresh turn
owns FDEC-076, now dependency-ready after this process repair. Continue 077, 078,
079 separately, rerun targeted gate, then new independent R002. Do not close D001
or start D002. D001 sole Active; S001 remains Active. Goal active, no external block.
Resources: primary plus clean detached R001 reviewer checkout; reuse/clean that
owned checkout before adding another. Monitor tasks terminal; child fixture dirs
cleaned via checked finally blocks; no server or watcher. Unrelated .idea untouched.
