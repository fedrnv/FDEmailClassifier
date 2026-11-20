---
schema: fdec-independent-review-result/v1
review_id: R003
review_task_id: FDEC-007
epic_id: FDEC-EPIC-D001
result: ChangesRequired
candidate_sha: a65f26c5dee5ecc23c0c2e7c07eec6cf2e9a25c5
candidate_tree: 307b2a2a8e5912f50164d4c679e8fd66c15b4ff7
ledger_sha: a3092b1e3af72d7f3c92b9002d24454e3bf5381d
policy_sha256: ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403
gate_result_sha256: b8a6287f087f442bdc175d14a0b448e56199a02c93296071386933fb59d768f7
reviewed_at: 2026-11-20
reviewer: independent-codex-session-review_d001_r003
---

# Independent D001 acceptance result R003

**ChangesRequired.** One reproducible blocking defect remains in the new Epic
closure source boundary. The existing focused closure suite passes, but does not
exercise an index-only mutation with restored working bytes.

## Independence and source boundary

This review was performed by a fresh separately instantiated model session assigned
the review request and repository instructions, without implementation-author
conversation history. I did not author the implementation or its corrections.
The parent executor supplied the detached candidate and ledger and received the
finding. This is model-session separation, not a claim of a different human or
model family. Neither R002 acceptance nor the gate PASS was treated as acceptance
of the new implementation.

Reviewed the exact detached candidate at
`C:/GitHub/FDEmailClassifier-review-D001-R003`. Candidate HEAD, tree and clean status
were checked before and after local reproduction. `verify-boundary.ps1` confirms
that its diff to the requested ledger contains exactly thirteen FDEC-006
event/evidence paths, with no implementation differences. Historical Tasks records
were not modified/deleted between the R001 candidate and this candidate. The
original FDEC-006 first-closure request remains byte-identical to its original
ledger blob. The pinned policy raw SHA256 matches the request. The gate-result
Git blob and primary canonical text identity both match the request hash; this
explicitly accounts for Windows CRLF checkout normalization.

## Requirements and evidence assessed

Read root AGENTS.md, DEVELOPMENT.md, Tasks/AGENTS.md, the pinned FDTasks 5.6
independent-review and closure rules, D001 specification, immutable FDEC-001..007
and FDEC-072 acceptance matrices, and R001/R002 results. Inspected current source
and completion evidence for the R001 remedies: checkout identity catalog and
canonical hashing, actual source/index readiness, exact accepted readiness events,
and effective base/amended acceptance criteria. The new closure validator is an
additional consumer; the existing item admission source-state implementation does
bind the index separately and does not resolve the finding below automatically.

Inspected workspace manifests, Rust strict schema implementation and JSON Schema,
README, architecture boundary walkthrough, legal inventory and governance scope,
and the D001 gate command graph. The contract retains twelve labels, strict fields,
cross-field unknown/abstained restrictions and advisory actions. No inference,
FFI/PyO3 runtime, REST service, model/data redistribution, version allocation or
live public-source synchronization is claimed by this review. Original-source
licensing and the unresolved FDTasks redistribution restriction remain declared.
Unchanged product/presentation work is assessed through current source and bound
prior evidence; no new remote readback or asset upload was performed.

Read FDEC-081's immutable contract, verification, documentation and production
repository/Epic-closure code. Inspected historical snapshots, member/dependency
completion, first-request preservation, typed gate/review identities and evidence,
latest review selection, topology, candidate ancestry/tree, own-ledger source
exceptions, special-Epic exclusion and unsupported publication rejection. Its
existing synthetic suite exercises these boundaries and passes on this candidate.
Mechanical evidence remains subject to the documented authorized-writer and
semantic-review boundary; no separate signing requirement is invented here.

The preserved first R003 gate attempt records exit 1 on 0a0e247 at the copied
source-readiness fixture's stale Epic-state evidence. The successful full rerun
records the current candidate and tree above. Independently inspected commit
a65f26c: it adds exactly two setup lines to each of source-readiness,
readiness-events and acceptance-matrix fixtures, rebuilding their current copied
Epic bindings. It does not weaken production admission or rewrite failed evidence.
The passing full gate is evidence of the cases it runs, but misses the case below.

## Blocking finding R003-01: index-only implementation bypasses Epic closure admission

Location: `scripts/validate_tasks/epic-closure.ps1:142`, and the incomplete staged
case at `scripts/validate_tasks/test-epic-closure.ps1:179`.

For a new current closure, the validator combines committed candidate-to-source
paths with `git diff --name-only $GitHead` and untracked paths. `git diff HEAD`
compares HEAD to the working tree. It does not expose staged content that differs
from HEAD when the working file has subsequently been restored to HEAD content.
The code does not independently inspect `git diff --cached` or the index state.

Reproducible trigger in an otherwise valid synthetic closure fixture:

1. Start from the suite's accepted candidate and append-only completion ledger.
2. Write an unreviewed implementation change and stage `implementation.txt`.
3. Restore only its working bytes to `Synthetic frozen implementation.` using the
   fixture writer, leaving the staged change intact.
4. Run the production `repository.ps1 -Root <owned fixture>` for the new Epic
   closure and request.

Exact command, run from the detached candidate:

```text
powershell -NoProfile -File C:/GitHub/FDEmailClassifier/Tasks/epics/FDEC-EPIC-D001/reviews/R003/reproduce-staged-closure.ps1
```

Monitor `62f5c5e1-eb9e-47e0-85ee-934ee6561ed3` completed exit 0. Selected exact output:

```text
INDEX DIFF:
 implementation.txt | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
HEAD TO WORKTREE DIFF:
PRODUCTION REPOSITORY VALIDATION WITH UNREVIEWED INDEX:
PASS: 6 records, immutable history, graph, requests and hosted publication boundary
REPRODUCED: new Epic closure accepted while staged implementation differs from tested candidate.
```

Exit 0 means the defect was reproduced, not that acceptance passed. The proof
script derives its valid fixture prefix from the pinned closure suite, calls the
actual candidate validator by absolute path, and removes its checked, uniquely
owned temporary repository in `finally`. It does not modify candidate code or
accepted repository records.

Impact: the documented precommit repository validation can admit a current Epic
closure while the Git index contains implementation that was never covered by
the passing candidate gate/review. A subsequent ordinary commit can include that
staged implementation. This contradicts FDEC-081's current-source boundary and
its claimed staged-source rejection. The ordinary staged test passes because it
also leaves different working bytes, so the working-tree check catches it.

Bounded remediation: inspect and validate index changes independently of working
changes, applying the same narrow ledger rules and checking Git command failures.
Add an explicit index-only/restored-working-file negative case through the real
repository validator. Preserve historical proof behavior and first requests;
repeat affected gate and independent review on the corrected candidate. This
review performs no implementation fix and creates no correction task.

## Local verification and cleanup

Windows PowerShell 5.1 and Git 2.45.1.windows.1. Read command-monitor skill and used
its available monitor tools for the fixture runs.

```text
powershell -NoProfile -File scripts/validate_tasks/test-epic-closure.ps1
```

Monitor `fe0e6fb2-3fb4-4d76-aa4b-3e97e59097c6` completed exit 0: valid first closure,
all existing rejection cases, historical reopen/current reclosure and preserved
request checks passed. Expected Git LF/CRLF warnings were inspected. This clean
suite result does not cover the additional failed contract above.

From the primary workspace:

```text
powershell -NoProfile -File Tasks/epics/FDEC-EPIC-D001/reviews/R003/verify-boundary.ps1
```

Exit 0: candidate/tree/cleanliness, thirteen-path ledger boundary, historical
record preservation, gate/policy hashes and original gate request verified.
The unchanged full gate and older admission suites were not unnecessarily
repeated; their implementation and recorded current evidence were inspected.

Only this round's result and proof scripts were written in primary. Both monitors
are terminal; disposable fixtures were removed by guarded cleanup. Detached
candidate remains clean and retained for reconciliation; unrelated primary IDE
and executor bookkeeping were untouched. No accepted record was edited, no task
or Epic was closed, and no remote setting, source push, allocation or publication
was performed. FDEC-007 cannot close on this ChangesRequired result.
