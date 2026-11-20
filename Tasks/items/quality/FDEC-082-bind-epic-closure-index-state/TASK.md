---
schema: fdtasks-spec/v3
id: FDEC-082
title: "Reject index-only implementation changes at Epic closure"
type: Correction
area: quality
component: foundation-admission
epic_id: FDEC-EPIC-D001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-081]
created_at: 2026-11-20T13:55:00Z
created_by: codex
atomicity:
  outcomes: ["Bind the Git index independently of working bytes when validating a current development Epic closure."]
  packets: ["Repair and verify the single R003-01 Epic source-boundary finding."]
  independent_acceptance: false
  boundary_reason: "One reproduced closure-admission defect with its direct historical compatibility checks."
---

# FDEC-082 index state at Epic closure

## Goal and evidence
Resolve independent finding R003-01 in
Tasks/epics/FDEC-EPIC-D001/reviews/R003/RESULT.md.
Passing gate candidate a65f26c5dee5ecc23c0c2e7c07eec6cf2e9a25c5 misses
index-only implementation changes when working bytes are restored to HEAD.
The review's reproduce-staged-closure.ps1 produces a nonempty cached diff,
empty HEAD-to-worktree diff and erroneous production validator PASS.
The existing staged negative case leaves changed working bytes and therefore
does not exercise this bypass. Reproduce before editing the implementation.

## Scope and readiness
Allowed: scripts/validate_tasks; docs/verification only if needed to explain this
source-boundary correction. Own immutable task/events/evidence and first request
are bookkeeping. Pin current source, policy, governing rules, FDEC-081 completion
and exact effective criteria at dispatch. D001 remains the only active development
Epic. This implements existing pinned FDTasks 5.6, with no normative change.

## Contract, failure and compatibility
Inspect the index independently of the working tree for every new current Epic
Done proof, including reclosure. Apply the same narrow append-only completion
ledger exceptions and fail closed on Git inspection errors or unsupported states.
Do not hide staged implementation behind restored working bytes. Preserve valid
historical proof replay, original first-closure request identities, normal clean
closure and current proof requirements. Do not add an allocator, publication,
future product behavior, unrelated admission refactor or historical record edit.

## Local acceptance matrix
| AC ID | Observable criterion | Local verification | Fixture/environment | Expected |
| --- | --- | --- | --- | --- |
| AC-01 | Current Epic closure rejects staged implementation even when working bytes equal the tested source | powershell -NoProfile -File scripts/validate_tasks/test-epic-closure.ps1; confirm exact cases at readiness against R003 reproduction | Owned disposable Windows Git fixtures with nonempty cached diff and restored working files | Real repository validator rejects index-only changes without mutating source or proof |
| AC-02 | Clean and permitted append-only completion state remains admissible, while current reclosure uses a new proof and historical first requests remain unchanged | Same focused suite and existing item/Epic reopened-request interaction | Synthetic positive, negative and historical compatibility cases | Correct acceptance/rejection with no version allocation, publication or request duplication |

## Completion and continuation
Record exact source/policy/commands/environment, positive and negative outcomes,
Git failure handling and guarded fixture cleanup. Preserve all R001/R002/R003
artifacts and the original gate/review requests. After this correction, repeat
FDEC-006 on the corrected frozen candidate and request fresh independent review;
do not treat either the prior gate PASS or this task's executor checks as approval.
