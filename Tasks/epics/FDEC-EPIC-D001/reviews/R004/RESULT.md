---
schema: fdec-independent-review-result/v1
review_id: R004
review_task_id: FDEC-007
epic_id: FDEC-EPIC-D001
result: ChangesRequired
candidate_sha: ed9cb62bda2856c21f0ff9c4c874a743d0d90a2e
candidate_tree: d3529de9fa1de411519d91f1ca8624ca55e2720b
ledger_sha: a2620ff1c07dff334dd125a4618f92fbc2a3f7b9
policy_sha256: ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403
gate_result_sha256: fe0064cfeddc17eb36a2756d3df9b7e826a1f1b96608b8d76ed90eee09308b49
reviewed_at: 2026-11-20
reviewer: independent-codex-session-review_d001_r004
---

# Independent D001 acceptance result R004

**ChangesRequired.** FDEC-082 resolves the reproduced R003 index-only defect, and
the expanded shared suite passes. One reproducible blocker remains in the directly
interacting committed candidate-to-closure source boundary: rename detection can
hide removal of implementation behind an allowed evidence destination.

## Independence and exact source

This review used a fresh separately instantiated model session assigned only the
review request, repository instructions and scope, without implementation-author
conversation history. I did not author the implementation or its corrections.
The parent executor supplied the detached candidate and ledger and received the
finding. This is model-session separation, not a separate human or model-family
claim. Earlier Accepted results and the current gate were assessed as evidence
for their actual cases, not automatic acceptance of this candidate.

Reviewed `C:/GitHub/FDEmailClassifier-review-D001-R004`. HEAD and tree match the
identities above; status was empty before and after both fixture runs. The
reviewer-owned `verify-boundary.ps1` passes: exactly nine FDEC-006 event/evidence
paths differ between candidate and ledger, with no implementation delta. No
historical Tasks record was modified/deleted/renamed since the R001 candidate.
The original FDEC-006 first-closure request remains byte-identical to ledger
868a368. The gate-result Git blob and primary canonical text identity match the
hash above; the policy's actual raw bytes match its pinned hash. Canonical text
hashing explicitly accounts for Windows CRLF checkout normalization.

## Requirements and evidence assessed

Read root/Tasks agent rules, DEVELOPMENT.md, pinned FDTasks 5.6 review and closure
requirements, D001 specification and effective membership/dependency context,
foundation FDEC-001..007 criteria, presentation FDEC-072 criteria and R001/R002/R003
results. Inspected current workspace manifest/scaffolds, strict Rust schema and
JSON Schema, README, architecture boundary walkthrough, original-source licensing
inventory, adoption/identity documentation, admission and source-state code, and
current gate command graph/result/verification/output. Reviewed the FDEC-081
contract, closure implementation and documentation, shared reopened-item/Epic
fixtures, FDEC-082 immutable specification and completion evidence, and its actual
three-file implementation diff. The direct S001 adoption/identity/first-request
and historical replay boundaries remain in scope; unrelated later Epics do not.

The source retains twelve topics, strict required fields and enums, unique labels,
cross-field unknown/abstained constraints and advisory actions. Rust and JSON
Schema agree on these constraints. Workspace consumers remain scaffolds and the
architecture walkthrough expressly assigns future native lifecycle work to later
tasks. Public presentation and prior readback evidence remain unchanged; no new
live readback or upload was performed. No inference, FFI/PyO3 runtime, REST,
version allocation, distribution approval or public-source synchronization is
claimed. Original-source Apache licensing and the unresolved upstream FDTasks
redistribution restriction remain explicitly declared.

## R003 remedy and fresh verification

The new `Epic-CurrentSourcePaths` independently enumerates index entries/flags,
cached changes, HEAD-to-working changes, index-to-working changes and nonignored
new paths, checking native command exits. New staged Tasks entries must be
additions, with working content matching the inspected index version; accepted
ledger rewrites reject. Unsupported flags and nonregular/unmerged index entries
reject. These checks apply to each new current closure, while historical replay
continues to use its recorded source.

Exact local command from the detached candidate:

```text
powershell -NoProfile -File scripts/validate_tasks/test-reopened-requests.ps1
```

Monitor `1b275d50-de3a-4a4f-8f6c-0ee5a35604f6` completed **exit 0** on Windows
PowerShell 5.1 / Git 2.45.1.windows.1. `focused-output.txt` preserves selected
actual output from the monitor log. The shared entrypoint passed item first-request
preservation and the expanded Epic suite: clean closure, permitted staged evidence,
R003 index-only/restored-working rejection, staged deletion/new implementation,
conflicting evidence, historical ledger rewrite, unsupported flags/unmerged index,
nonzero Git inspection, invalid gate/review/member/rights evidence, historical
reopen/replay, fresh-proof reclosure and index-only rejection at reclosure. Original
first requests remained unchanged and no version was allocated. Expected synthetic
checkout normalization warnings were inspected. This is passing evidence for those
cases, but does not cover the following committed-path case.

## Blocking finding R004-01: committed rename hides implementation removal

Location: `scripts/validate_tasks/epic-closure.ps1:163` and the allowed-path loop
at lines 169-177. The committed source comparison uses
`git diff --name-only $proof.candidate_sha $proof.source_sha` with rename detection
enabled. For an exact rename it returns only the destination path. The separate
Tasks-only history comparison disables renames but sees only a permitted addition
when the original path was outside Tasks. Current index/working checks correctly
see no remaining implementation change relative to the new HEAD.

Reproducible trigger in an otherwise valid synthetic first-closure fixture:

1. Start with the suite's passing candidate and append-only completion ledger.
2. Commit `git mv implementation.txt Tasks/epics/FDEC-EPIC-D001/evidence/moved-implementation.txt`.
3. Set the new closure proof's `source_sha` to this current HEAD; keep the original
   passing candidate, gate and Accepted review bindings unchanged.
4. Append the ordinary closure event/proof/request and invoke the actual candidate
   `repository.ps1` against the fixture.

Exact command:

```text
powershell -NoProfile -File C:/GitHub/FDEmailClassifier/Tasks/epics/FDEC-EPIC-D001/reviews/R004/reproduce-committed-rename.ps1
```

Monitor `cf34ae47-d74e-46a3-bd5a-beb6f2e208d2` completed **exit 0**, meaning the
defect was reproduced. The committed comparison reports:

```text
R100 implementation.txt Tasks/epics/FDEC-EPIC-D001/evidence/moved-implementation.txt
PRODUCTION REPOSITORY VALIDATION AFTER COMMITTED IMPLEMENTATION RENAME:
PASS: 6 records, immutable history, graph, requests and hosted publication boundary
REPRODUCED: current closure accepted after implementation was moved into allowed ledger evidence.
```

Full concise output is retained in `reproduction-output.txt`. The proof script
uses a synthetic fixture based on the candidate suite and calls the actual
candidate validator by absolute path. It does not forge real project evidence or
alter the detached candidate.

Impact: a current Epic can close while implementation present in its passing
gate/review candidate has been removed or relocated outside its build path, with
no new gate/review. This violates FDEC-081's explicit candidate-to-closure
implementation identity and the documented narrow append-only ledger exception.
The FDEC-082 index remedy itself is sound for the reproduced R003 case, but cannot
cover a committed source difference hidden by the earlier comparison.

Bounded remediation outcome: enumerate both sides of committed changes independently
of rename detection and apply the same narrow source/history rules, checking Git
inspection failures. Add a real-validator negative fixture for a committed rename
from implementation into an allowed completion path; preserve clean closure,
historical replay, current reclosure, original requests and the index-only remedy.
Repeat affected gate and independent review on corrected source. No implementation
fix or correction task was created by this reviewer.

## Verification scope and cleanup

From primary, `powershell -NoProfile -File Tasks/epics/FDEC-EPIC-D001/reviews/R004/verify-boundary.ps1`
exited 0; `git diff --check` exited 0. The unchanged full gate and all older suites
were not unnecessarily repeated. Their current command graph and bound result
were inspected; their outcomes remain attributed to the recorded gate.

Both monitors are terminal. Guarded finally cleanup removed each uniquely owned
temporary repository. Candidate status remains empty and its worktree is retained.
Only R004 result/proof artifacts were written in primary; no accepted record,
implementation, settings, task status, version, source publication or artifact
distribution was changed. FDEC-007 cannot close on this ChangesRequired result.
