---
schema: fdtasks-spec/v3
id: FDEC-083
title: "Reject committed implementation renames at Epic closure"
type: Correction
area: quality
component: foundation-admission
epic_id: FDEC-EPIC-D001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-082]
created_at: 2026-11-20T14:20:00Z
created_by: codex
atomicity:
  outcomes: ["Preserve both source and destination paths when validating committed candidate-to-closure changes."]
  packets: ["Repair and verify the single R004-01 committed-rename source-boundary finding."]
  independent_acceptance: false
  boundary_reason: "One reproduced Epic closure-admission defect and its direct compatibility checks."
---

# FDEC-083 committed source paths

## Goal and evidence
Resolve R004-01 in Tasks/epics/FDEC-EPIC-D001/reviews/R004/RESULT.md.
Candidate ed9cb62bda2856c21f0ff9c4c874a743d0d90a2e compares committed
candidate-to-source paths with rename detection enabled. Committing an exact
rename of implementation.txt into an allowed Epic evidence path hides removal
of the original implementation path from that name-only result. Tasks-only
history sees an addition and current index/working checks see clean new HEAD.
The review's reproduce-committed-rename.ps1 produces incorrect validator PASS.
Reproduce before changing code; preserve the immutable proof and actual output.

## Scope and readiness
Allowed: scripts/validate_tasks; docs/verification only if needed to explain the
source boundary. Own task/events/evidence and first request are bookkeeping.
Pin current source, policy, governing rules, FDEC-082 completion and effective AC
before dispatch. D001 stays the only active development Epic. This implements
existing pinned FDTasks 5.6; no normative change or new functionality is intended.

## Contract, failure and compatibility
Enumerate committed changes without hiding either side of renames; apply the
same narrow append-only ledger exceptions and check Git inspection failures.
Moving implementation into an allowed completion path must require a new tested
candidate, even when HEAD/index/working bytes are mutually clean. Preserve the
FDEC-082 index-only remedy, legitimate append-only completion, historical proof
replay, current reclosure proof requirements and immutable first requests.
Do not introduce an allocator, publication, unrelated refactor, future product
behavior or accepted-record rewrite. Stop closure on invalid source evidence.

## Local acceptance matrix
| AC ID | Observable criterion | Local verification | Fixture/environment | Expected |
| --- | --- | --- | --- | --- |
| AC-01 | Current Epic closure rejects committed relocation of implementation into an allowed completion path despite a clean new HEAD/index/worktree | powershell -NoProfile -File scripts/validate_tasks/test-epic-closure.ps1; confirm exact real-validator cases against R004 reproduction at readiness | Owned disposable Windows Git fixtures with rename detection enabled and changed proof source_sha | Original source path is checked and invalid closure rejects without mutation |
| AC-02 | Clean append-only completion, historical replay and current valid reclosure remain admissible while first requests and index-only rejection are preserved | Same focused suite and shared reopened-request interaction | Synthetic positive, negative and historical compatibility cases | Correct acceptance/rejection; no allocation, publication or duplicate request |

## Completion and continuation
Record exact source/policy/environment/commands, observed rename reproduction,
corrected outcomes, Git failure handling and guarded cleanup. Preserve all prior
rounds and gate/review requests. After this correction repeat FDEC-006 on the
corrected frozen candidate, then request a fresh independent FDEC-007 round.
Neither prior gate PASS nor executor checks authorize D001 closure by themselves.
