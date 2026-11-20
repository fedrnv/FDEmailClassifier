---
schema: fdtasks-spec/v3
id: FDEC-077
title: "Reject stale readiness after tracked source changes"
type: Correction
area: quality
component: foundation-admission
epic_id: FDEC-EPIC-D001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-076]
created_at: 2026-11-20T12:07:20Z
created_by: codex
atomicity:
  outcomes: ["Bind actual source state to accepted readiness across claim, dispatch, resume, execute and closure with explicit task-owned progress handling."]
  packets: ["Implement and verify this single admission contract."]
  independent_acceptance: false
  boundary_reason: "One independently verifiable finding with direct failure and compatibility checks."
---

# FDEC-077

## Goal and evidence
Bind actual source state to accepted readiness across claim, dispatch, resume, execute and closure with explicit task-owned progress handling.
Independent finding R001-02: Tasks/epics/FDEC-EPIC-D001/reviews/R001/RESULT.md.
Baseline 868a36872ac32c41f87c023e0711064e478c41dc; tested candidate 5e44d2148f510c64a53dc77f8ad1fc8827278ba1.
Pin current source, policy, dependencies and rules at dispatch. Inspect that
finding and reproduce before changing the implementation. D001 remains sole Active.

## Scope
scripts/validate_tasks; task-specific readiness evidence. Own immutable records/events/evidence and first closure request.
No other finding, product feature, external publication or accepted-record rewrite.
This implements the existing pinned FDTasks 5.6 contract; no normative change.

## Failure, compatibility and recovery
Fail closed on stale, missing or ambiguous evidence. Preserve all original accepted
specifications, events, policy pins and version requests; use append-only successor
bindings where required. No credentials or private fixtures. Keep one cohesive
packet; do not add unrelated refactors. Record the exact source/commands/outcomes
and clean only proven-owned disposable fixtures. A changed candidate invalidates
the affected gate; independent review is separate, never self-approved here.

## Acceptance matrix
| AC ID | Observable criterion | Local verification | Fixture | Expected |
| --- | --- | --- | --- | --- |
| AC-01 | Bind actual source state to accepted readiness across claim, dispatch, resume, execute and closure with explicit task-owned progress handling. | powershell -NoProfile -File scripts/validate_tasks/test-source-readiness.ps1 (confirm exact path at readiness) | Local supported Windows checkout and owned synthetic fixtures | Correct current contract accepted with preserved history |
| AC-02 | Tracked source mutation under unchanged HEAD rejects each applicable action; authorized current source can be admitted. | Same targeted test through actual admission entrypoints | Synthetic invalid/compatibility cases | Explicit rejection; prior state preserved |

## Completion
Hash-bound evidence, policy/source/tool/environment identities and one first closure
request. No automatic acceptance based on model text. Re-run affected D001 gate and
new independent review after the correction chain; do not rewrite R001.
