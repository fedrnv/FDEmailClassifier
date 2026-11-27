---
schema: fdtasks-spec/v3
id: FDEC-251
title: "Authenticate compact inventories through guarded model consumers"
type: Task
area: ai
component: compact-training-input-replay
epic_id: FDEC-EPIC-D003
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-250]
created_at: 2026-11-27T21:30:40.769Z
created_by: codex
atomicity:
  outcomes: ["Replay one authenticated compact inventory consistently through guarded model consumers and their provenance chain."]
  packets: ["Bind compact source replay and one inventory identity through existing consumers."]
  independent_acceptance: false
  boundary_reason: "A mismatch between consumers would break the shared signed-input and provenance contract."
---

# FDEC-251 — Authenticate compact inventories through guarded model consumers

Start from public source `73453cd0b4a746ee78229ea442ee8f742ea1959e`. Manual publication follows FDTasks 5.7.
Reuse FDEC-250 and the existing source rights, current consent, signed split
and independent review checks. Match both recomputed record metadata and
every full-width fingerprint against an authenticated snapshot. Keep train
and held-out roles separate and propagate the same inventory digest through
checkpoint, handoff, report, export and calibration. Keep v1 callers working.

Scope covers existing source readers and directly affected tests in
`training/splits/`, `training/finetune/`, `training/baseline/`,
`training/eval/`, `training/calibration/`, and `training/export/`.
No new permissions, label creation, actual training, model publication or
D013 work is included.

| AC ID | Scenario | Trusted check | Expected result |
| --- | --- | --- | --- |
| AC-01 | Compact guarded input and identity propagation | Run the local compact fixture and guarded finetune and baseline suites | Train and test rows remain isolated and provenance uses the same digest. |
| AC-02 | Mutated packed input, stale consent or disallowed role | Run actual admission entry points on negative software fixtures | Changed input fails before reaching the model and prior outputs remain safe. |
| AC-03 | Keep existing v1 and compact consumer contracts | Run affected split, evaluation, calibration, export and MLX handoff software checks | Existing legacy and new compact readers preserve behavior and candidate identity. |

Record commands, exact source, policy, digest binding and limitations.
