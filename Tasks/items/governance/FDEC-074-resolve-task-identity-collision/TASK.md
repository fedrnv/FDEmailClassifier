---
schema: fdtasks-spec/v3
id: FDEC-074
title: "Resolve duplicate accepted task identity without rewriting history"
type: Correction
area: governance
component: process
epic_id: FDEC-EPIC-S001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T11:45:00Z
created_by: codex
atomicity:
  outcomes: ["Restore unambiguous task admission after merged website FDEC-073 collided with completed adoption FDEC-073."]
  packets: ["Publish replacement-first identity migration and validate all admission consumers."]
  independent_acceptance: false
  boundary_reason: "One identity and dependency projection repair; no website implementation."
---

# FDEC-074 identity collision repair

## Defect and rule layer
Local admission cannot resolve duplicate FDEC-073 after merge d88ae7c. Completed
S001 adoption and its closure request must retain their identity; Planned D009
website branding needs a new unused identity. FDTasks 5.6 replacement-first
migration already authorizes immutable supersession. This implements that existing
contract in local projection, not a normative change (5.6 remains 5.6).

## Scope and baseline
Baseline 844ad9a. Allowed: scripts/validate_tasks; Tasks/migrations; this record;
new replacement FDEC-075 with the website outcome unchanged; append-only events
under old web FDEC-073, D009, FDEC-063 and S001; own version request/evidence.
Do not edit accepted specs/events/evidence, reparent adoption, execute website
work, activate D009, or publish externally. One cohesive recovery packet.

## Admission and recovery
Bootstrap manual readiness is necessary because the production entrypoint fails
closed on the exact defect this Correction repairs. Preserve both source hashes,
publish replacement before retiring only the path-qualified colliding web record,
replace D009/gate-063 relationships, and require hash-bound migration evidence.
No arbitrary duplicate IDs become valid. Corrupt/incomplete migration fails closed.
Accepted repair changes only through later append-only correction. No upstream
normative successor is needed; history entry is Tasks/migrations/README-074.md.

## Acceptance matrix
| AC ID | Criterion | Local test | Fixture | Expected |
| --- | --- | --- | --- | --- |
| AC-01 | Adoption unchanged, branding preserved as FDEC-075, D009/063 references repaired | powershell -NoProfile -File scripts/validate_tasks/test-identity.ps1 | Local repository and owned disposable copies | Unique active projection, original files byte-stable, all admission actions use same projection |
| AC-02 | Incomplete, stale or ambiguous migration cannot authorize execution | Same focused script | Missing replacement, altered retired hash, unrelated duplicate and stale mappings | Explicit rejection, original checkout unchanged |

## Completion
Record original/replacement hashes, exact commands, source/policy identity, cleanup,
and one correction_closed request. Resume FDEC-072 on next turn after local checks.
