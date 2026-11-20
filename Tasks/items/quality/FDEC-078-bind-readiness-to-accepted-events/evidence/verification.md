# FDEC-078 accepted readiness history verification

Baseline 4b248987a01ce2ca934b509612e5c6411b28729d plus exact working candidate file identities below.
Actual source-state fdec-source-state/v1: 2cfd31fba105331e89dc5b5bc8cc4daa653fa5e93e334bc86c8f0cca753fd6f7.
Policy SHA256 ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403;
upstream 00a0d019c1e73d5ecf4c4e75c42c38497c154e50. Windows PowerShell 5.1/Git.

AC-01 PASS: powershell -NoProfile -File scripts/validate_tasks/test-readiness-events.ps1
Monitor 093abf0d-05f7-47df-8a8d-1d4e1add7611 completed exit 0. Every claim,
dispatch, resume, execute and close requires the latest accepted task event with
exact evidence path and canonical hash. Fresh current accepted decision admits.
Accepted byte-equivalent alternate path is still another decision; newer accepted
brief supersedes earlier authorization. No boolean/name-only readiness admission.

AC-02 PASS: same script rejects on all five actions: no accepted event, unaccepted
alternate path, changed accepted JSON, superseded earlier brief, tied latest decision
timestamps, and legacy prose-only event lacking exact evidence fields. Restore a
valid new accepted event and all actions admit again. Owned fixture resets are
explicitly synthetic, not edits to accepted primary history. Duplicate/missing
binding fields also fail closed in the event reader. A new helper records the
executor's decision; it does not perform semantic review or invent authority.

Direct interactions PASS: test-validation.ps1, monitor
3e1d1ecc-5de7-4ade-aedf-45edb5eace71 exit 0; test-identity.ps1, monitor
e5bb3881-263d-4add-9359-c983ee01cd88 exit 0. Updated fixtures append actual acceptance
events for each intended positive/negative brief, preserving downstream source,
rule, dependency and migration checks rather than bypassing the new guard.
Source-state integration test-source-readiness.ps1, monitor
31512cfe-1a71-42df-994b-535f50e74eb6 exit 0: recorded acceptance does not admit
stale tracked/staged/deleted/new code, and renewed state plus explicit accepted
brief admits authorized current progress. Broad unchanged gate not rerun.

Initial unbound draft dispatch was still running when the new mandatory guard
became available and was rejected Missing accepted readiness event. No PASS is
claimed for that draft. Published fresh source-bound evidence via typed accepted
event, then production dispatch PASS. No failed candidate accepted or unchanged
functional retry. git diff --check PASS; actual implementation diff inspected.

## Protocol and limits
Latest task-local readiness-accepted event binds readiness_file under evidence and
readiness_sha256. Canonical hashing preserves supported checkout normalization.
Ambiguous latest times and duplicate/missing binding fields fail closed. All actions
use the same reader. Old events remain immutable history and cannot independently
authorize new work; no accepted historical record rewritten. This is repository
provenance under the authorized writer boundary, not actor cryptographic signing.
Source/rule/dependency checks still run; complete AC coverage remains FDEC-079.
No normative version change, new human approval loop, source push or publication.

## Exact canonical source identities
- scripts/validate_tasks/readiness-events.ps1: a03d59b21888736918c201012ef933a64834e673abce1607e61c6533b827a25a
- scripts/validate_tasks/admission.ps1: 233b3e7a25c6757d49471fc49ebc0a534f8fdd5c0210915cf04a43be951b6827
- scripts/validate_tasks/test-readiness-events.ps1: f4f2c76980c696bbca68338a42a6455f97cefe3daade196de3ffbdb7fbd22c66
- scripts/validate_tasks/test-source-readiness.ps1: 197d818c19aa98d00c074e73d66c9e6d2780c07aeee45d6378b30fe4f358301b
- scripts/validate_tasks/test-validation.ps1: 5de1a7ef0670ebfd5a34951ac9f529616a86e1ce3f56b2cb8e955369fa2a3a8b
- scripts/validate_tasks/test-identity.ps1: 841c5bacfafa56a8d3b84d7a1c42e2c8348bf855f7e6d0584f9b98ebf2e4eb4f
- scripts/validate_tasks/README.md: 3ed370e4c6d23f13c4251ccfadfe58816998d2e9cea770d896f37abcc00cc185

## Cleanup and checkpoint
All monitors terminal, owned fixture repositories cleaned through checked finally
blocks, no watcher/server. Unrelated .idea untouched. FDEC-078 verified for first
closure. Next fresh turn owns FDEC-079, then targeted FDEC-006 on corrected frozen
candidate and independent R002. FDEC-007 stays Blocked and gate Planned until then.
D001 sole Active, no external blocker. Goal active. Future task readiness must call
Write-ReadinessAcceptance before admission, including direct closure, without
rewriting prior accepted decisions or evidence.
