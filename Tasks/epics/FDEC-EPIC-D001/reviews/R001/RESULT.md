---
schema: fdec-independent-review-result/v1
review_id: R001
review_task_id: FDEC-007
epic_id: FDEC-EPIC-D001
result: ChangesRequired
candidate_sha: 5e44d2148f510c64a53dc77f8ad1fc8827278ba1
candidate_tree: 510913da47ba2d2b9d18c2d89275198dfc8ce0a3
policy_sha256: ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403
gate_result_sha256: c40e6beb4b166a840ef17745ee91c8afc8b5c6cfce6c09cd62310308c4b5caea
reviewed_at: 2026-11-20
reviewer: independent-codex-session-review_d001_r001
---

# D001 independent acceptance result

**ChangesRequired.** The current implementation has reproducibility and admission
gaps that contradict the adopted readiness contract. These findings concern
FDEC-004 and its direct S001 adoption/migration interactions; they do not require
future inference, ABI, REST or publication features.

## Independence and source boundary

This review was performed by a separately instantiated model session assigned
only the review request, repository instructions and review scope. I did not
author the implementation, did not rely on an earlier agent's acceptance, and
did not change candidate source or accepted records. The parent implementing
agent supplied the frozen checkout and gate ledger, and received findings. This
is model-session separation, not a claim of a separate human or model family.

`git rev-parse HEAD` and `git rev-parse 'HEAD^{tree}'` in
`C:/GitHub/FDEmailClassifier-review-D001-R001` matched the candidate and tree above.
`git status --short` was empty before and after review. The diff to gate ledger
commit `868a36872ac32c41f87c023e0711064e478c41dc` contains eleven FDEC-006
event/evidence/version-request files, with no implementation differences. The
actual gate-result JSON hash matches the request. The original gate's reported
PASS is authentic evidence for its author's working copy, but does not establish
fresh-checkout reproducibility, as demonstrated below.

## Inspected requirements and evidence

Read root AGENTS.md, DEVELOPMENT.md, Tasks/AGENTS.md, pinned upstream 5.6 policy,
policy adoption/implementation documentation, D001 membership, immutable task
AC matrices for FDEC-001..007 and FDEC-072, and migration FDEC-074 bindings.
Inspected actual FDEC-006 result, output summary and verification rather than
relying only on the request. Reviewed workspace manifests, Rust schema and its
tests, JSON Schema and documented contract, FFI/Python/server scaffolds, README,
ADR-0001 and boundary walkthrough, governance files, license inventories and
dependency audit, admission/repository/adoption validation scripts and their
fixtures. Inspected presentation verification and the actual PNG visually; its
SHA256 is `a0e8acce656ef17ecb9c6699376a40edec3bad1ac3c6add82c22b43da7a6ed1d`.

Schema constraints and advisory-only semantics agree between Rust, JSON Schema
and documentation. Public documentation clearly qualifies planned SDKs, inference
and unmeasured language/security performance. No runtime email input or model/data
distribution was introduced. Existing unresolved FDTasks redistribution rights
remain a declared distribution block, not an undisclosed completed feature.
No external publication or account mutation was performed during review.

## Blocking findings

### R001-01 — Fresh checkout cannot validate its pinned policy and migration bytes

Location: `scripts/validate_tasks/admission.ps1:15`,
`scripts/validate_tasks/repository.ps1:36`, raw-byte bindings in
`Tasks/policy/adoption-5.6.json` and `Tasks/migrations/FDEC-074.json`; no repository
`.gitattributes` protects the relevant bytes.

In the clean frozen checkout, `git config --get core.autocrlf` returns `true`.
`Get-FileHash Tasks/policy/upstream-5.6.md` returns
`8c5fcf84fb50ecceaaa1ecc92f99ac6dadb82666d3b63f3d0b5c2f05bbea4682`, while the
required policy hash is `ddb4f...`. Direct command
`powershell -NoProfile -File scripts/validate_tasks/admission.ps1` exits 1 with
`Policy hash mismatch`, despite `git diff --quiet HEAD` exiting 0.
Two migration-bound files also differ in raw bytes: the adoption FDEC-073 TASK
hash is `d6d686a280a272ef8c97e01cb5093b5e0abe88863a68c21c40a73cfa0a86406e`
instead of `cf631520b8491140e74613ff22a1d504acff888ad5db4b4cc64375027ab6c1d1`;
the website supersession event is
`4ff0d4958c7ddabcefef1b24e45bf02f5fbe073c7062545f08c782efe1290b15` instead
of `d83d4820c058aa95d0f317ff49657cd52976da2ab82ae300f2b4725df4e7802d`.

Impact: standard Windows checkout normalization makes the advertised offline
admission and gate fail before useful validation. The original gate did not cover
the fresh-checkout boundary required by the reproducible foundation outcome.

Bounded remediation: make byte identities and checkout behavior consistent for
all pinned artifacts, including the migration's existing mixed-ending/BOM files,
without silently weakening hash checks or rewriting accepted records. Verify from
a new checkout with `core.autocrlf=true` and the supported alternate checkout
configuration, then rerun affected gate stages on the corrected frozen candidate.

### R001-02 — Changed tracked implementation reuses stale source readiness

Location: `scripts/validate_tasks/admission.ps1:25-26` and
`scripts/validate_tasks/repository.ps1:21-26`.

Readiness compares `source_sha` only with HEAD. Repository dirty checking covers
immutable Tasks paths, not implementation. In the owned reproduction fixture,
after readiness is recorded, changing tracked `source.txt` leaves HEAD unchanged
and produces a real Git diff. All four `claim`, `dispatch`, `resume` and `execute`
actions still print PASS. This contradicts the pinned policy's requirement that
a source change invalidate readiness before queued dispatch/resume/execution.

Impact: an executor can be admitted against implementation different from the
source that readiness accepted. Existing all-zero-SHA tests cannot detect this.

Bounded remediation: bind the relevant actual source state and revalidate it at
admission, with an explicit treatment of permitted task-owned ledger changes and
in-progress work. Add a real tracked-source mutation case for each applicable
action so queued work cannot reuse stale authorization merely because HEAD did
not move.

### R001-03 — Readiness JSON need not correspond to accepted readiness history

Location: `scripts/validate_tasks/admission.ps1:20-24` and
`Tasks/policy/README.md` ("Before dispatch, append accepted readiness").

The reproduction resets only disposable FDEC-005 event history to Planned,
creates a JSON brief, and calls `-Action execute`. No readiness-accepted event
exists for that target, yet admission prints PASS. The script checks JSON contents
and `semantic_review: accepted`, but never resolves an accepted event establishing
that particular brief. Its name or self-declared boolean establishes acceptance.

Impact: missing acceptance history does not fail closed. An arbitrary alternate
JSON can present itself as accepted readiness, bypassing the adopted append-only
readiness decision boundary.

Bounded remediation: resolve and validate the target's accepted readiness event
and exact associated evidence identity, preserving accepted historical records.
Reject missing, mismatched and superseded decisions through all equivalent
admission actions, including direct closure.

### R001-04 — Readiness may omit an accepted acceptance criterion

Location: `scripts/validate_tasks/admission.ps1:29-30`.

The script checks only that some matrix rows have id/command/expected values.
Deleting AC-02 from the fixture's readiness matrix still allows execute admission,
although the immutable target task explicitly requires AC-01 and AC-02. Unknown
or duplicate criterion IDs are likewise not compared with the task's matrix.

Impact: admission does not establish acceptance completeness; an executor can
receive a ready matrix that drops required negative/failure verification.

Bounded remediation: check exact required criterion coverage and unique stable
IDs against the effective immutable task plus accepted amendments, preserving
the full scenario/test/environment/expected-result contract. Add rejection cases
for omitted, duplicate and unknown IDs without inventing replacement criteria.

## Local reproduction and outcomes

Commands above were run on Windows PowerShell 5.1. Additional exact command:

```text
powershell -NoProfile -File Tasks/epics/FDEC-EPIC-D001/reviews/R001/reproduce-admission.ps1
```

Run from the primary workspace; final exit code 0 means reproduction completed,
not acceptance. Actual output:

```text
CASE 1: no readiness-accepted event exists for fixture target
PASS: immutable baseline and execute admission inputs
CASE 2: tracked implementation changes without HEAD change
 source.txt | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
PASS: immutable baseline and claim admission inputs
PASS: immutable baseline and dispatch admission inputs
PASS: immutable baseline and resume admission inputs
PASS: immutable baseline and execute admission inputs
CASE 3: readiness matrix omits AC-02
PASS: immutable baseline and execute admission inputs
```

The proof script copies Tasks into an owned disposable repository, sets its own
Git baseline, and supplies matching policy/migration bytes only inside that copy
to isolate findings 02-04 from finding 01. Two migration originals are copied from
the primary checkout only after validating their existing manifest hashes. An
initial unadjusted run failed at the policy hash; policy-only normalization then
failed at migration bindings. Neither failure was masked in the frozen checkout.
The proof script cleans only its checked, generated temporary directory.

The full existing build/gate was not repeated: the clean-checkout admission failure
is already concrete, and focused reproductions expose checks absent from that
gate. Existing Rust/schema/license results were inspected as prior gate evidence,
not relabeled as reviewer reruns. No fixes or correction identities were created.
Candidate remains unchanged and its reviewer checkout is retained. Only this
round's result and proof script were written in the primary workspace. D001 and
FDEC-007 must remain unaccepted until corrections and current gate/review evidence
resolve these findings.
