---
schema: fdtasks-spec/v3
id: FDEC-080
title: "Preserve valid first-closure requests when work reopens"
type: Correction
area: governance
component: process
epic_id: FDEC-EPIC-S001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T12:10:00Z
created_by: codex
atomicity:
  outcomes: ["Keep first verified closure requests valid across ordinary item reopen and reclose without accepting requests for never-closed work."]
  packets: ["Repair generic immutable closure-ledger projection and test its admission interaction."]
  independent_acceptance: false
  boundary_reason: "One blocking lifecycle ledger contract, not another product feature or D001 finding."
---

# FDEC-080 reopened closure history

## Defect and current evidence
Reopening FDEC-006 after independent ChangesRequired is mandatory under pinned
FDTasks 5.6. Its existing first-closure request must remain immutable and not be
re-emitted. repository.ps1 currently requires every request's target to be Done
now, rather than recognizing verified first closure history. After required
Done -> Planned event the production check exits 1: Invalid closed item request.
This blocks every claim/dispatch/resume/execute/close action, including D001 fixes.

## Rule layer and version
Generic local lifecycle/version-request projection, implementing existing upstream
5.6 canonical first-closure deduplication. No normative successor or rule change;
current/proposed normative version remains 5.6. Record local implementation history
in this task evidence. Ordinary S001 process Correction, not D001 new functionality.

## Scope, baseline and admission
Baseline 868a368; exact review candidate 5e44d21 remains unchanged. Allowed:
scripts/validate_tasks; own immutable task/events/evidence/first request and S001
membership. No accepted record edit, request deletion, extra gate/review request,
version allocation, external push or publication. Bootstrap manually under current
source/policy/rule evidence if production admission remains blocked by this defect.
Checkpoint interrupted FDEC-007/R001 before this necessary process interruption.

## Implementation and recovery
Resolve validated closure history separately from current task state. Preserve the
one-time request and reject duplicates, unsupported members, fabricated/unverified
closure evidence and never-closed targets. Reclosing must not add another request.
Fail closed on invalid transitions/ambiguous history. One cohesive packet. Preserve
all historical bytes; append evidence for changed state, never hide gate findings.

## Acceptance matrix
| AC ID | Observable criterion | Local verification | Fixture | Expected |
| --- | --- | --- | --- | --- |
| AC-01 | Valid first verified closure request survives reopen/reclose with one identity | powershell -NoProfile -File scripts/validate_tasks/test-reopened-requests.ps1 (confirm path at readiness) | Current reopened gate and disposable history fixtures | Shared admission resumes, historical request unchanged and unique |
| AC-02 | Never-closed, wrong-parent, duplicate and invalid-evidence requests remain rejected | Same focused script through repository/admission | Synthetic invalid history | Explicit rejection without ledger mutation |

## Exact continuation checkpoint
FDEC-007 remains Blocked after independent R001 ChangesRequired; FDEC-006 Planned.
D001 findings FDEC-076..079 are queued, not implemented. After bounded repair,
revalidate that exact interrupted review checkpoint and select FDEC-076 first.
Do not run another independent review until all four fixes and current gate pass.
D001 alone Active; S001 permanently Active. No external authority is missing.
