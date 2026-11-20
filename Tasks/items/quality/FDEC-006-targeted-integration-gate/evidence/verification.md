# FDEC-006 local integration acceptance

Exact passing source: 5e44d2148f510c64a53dc77f8ad1fc8827278ba1. Tree: 510913da47ba2d2b9d18c2d89275198dfc8ce0a3.
Policy SHA256 ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403,
upstream source 00a0d019c1e73d5ecf4c4e75c42c38497c154e50.
Command: powershell -NoProfile -File scripts/verification/D001.ps1 -ExpectedSource 5e44d2148f510c64a53dc77f8ad1fc8827278ba1
Monitor task 6c948a10-e405-4cb4-aeea-a2dc287aeb0b completed exit 0, PASS.
One run on this frozen candidate, no failure retry, no source changes during run.
Gate entrypoint was committed before execution so independent review can target an
exact commit. The later closure commit adds only own task records/evidence/request.

AC-01 PASS: all declared direct D001 integration stages completed. Workspace check,
core/FFI/server/example independent builds, isolated Python build and Rust/server
smokes pass. Four strict Serde tests pass. Ajv accepts all three valid state fixtures
and rejects all nine invalid files. Original-source governance and both exact Cargo
graph license checks pass. Shared task admission/graph, immutable history, scoped
rules, active-Epic invariant, request uniqueness, identity migration and adoption
checks pass. README links and architecture/preview artifact paths resolve.
Compact actual log selections in gate-output-summary.txt; machine result and tool
identities in gate-result.json. First monitor output exceeded its tail window;
full local monitor log was read to extract stage/PASS summaries. Warnings concerned
Git LF/CRLF conversion in disposable fixtures; no functional failure or timeout.

AC-02 PASS: direct child checks reject malformed output, unsafe abstention, duplicate
labels/keys, bad server arguments, missing package, absent/corrupt license, unknown
redistribution approval, stale source/rules/migration, missing dependencies,
duplicate requests/identities and unreviewed hosted workflows. Negative fixtures
preserve original inputs or are reset within their owned disposable trees.
Separate direct gate call with all-zero ExpectedSource rejected before any stage;
tracked candidate still clean. Synthetic fixtures only, no private email/model/data.

Manual direct interaction review: ADR keeps shared schema and advisory-only actions
across planned SDKs; no real inference/native SDK/REST capability claimed. Current
schema is implemented; later contract/ownership tests remain future tasks. Presentation
uses actual red E with neutral background and green check; reuse unchanged PNG hash
and hosted readback evidence from FDEC-072 final-verification.md/readback.json.
Asset SHA256 a0e8acce656ef17ecb9c6699376a40edec3bad1ac3c6add82c22b43da7a6ed1d
matches tested candidate. License declaration covers original code; FDTasks snapshot
redistribution remains blocked pending rights/exclusion review, and negative gate
asserts that block. This is local integration acceptance, not publication clearance.

## Bounds and cleanup
No hosted acceptance, model/dataset transfer, deployment, release, source push or
version allocation. Child fixture scripts cleaned bounded owned directories.
Ignored target and external npm/Cargo caches retained for reuse. Monitor process
terminal; no server/watcher alive. Untracked unrelated .idea preserved. Gate-owned
readiness was renewed after candidate commit; no historical evidence overwritten.
Actual gate source/docs and test selection inspected. git diff --check PASS.

## Next-turn checkpoint
FDEC-006 verified for closure with one task_closed request. Next fresh turn:
admit FDEC-007, create immutable independent review REQUEST/RESULT under D001 and
use a different person or fresh independent model session with disclosed boundary.
Review exact candidate 5e44d2148f510c64a53dc77f8ad1fc8827278ba1, not a later changed implementation. The gate closure
ledger will be a descendant commit with evidence only. Bind its report/request to
this source SHA/tree. Correct findings through new medium tasks/events, invalidate
and rerun affected gate on changed candidate; never edit accepted history.
D001 alone Active. No external blocker for independent review. Goal stays active.
