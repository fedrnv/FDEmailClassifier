---
schema: fdtasks-spec/v3
id: FDEC-247
title: "Replay the reviewed Sinabis source through guarded admission"
type: Task
area: ai
component: training-and-evaluation
epic_id: FDEC-EPIC-D003
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-011, FDEC-012]
created_at: 2026-11-27T21:04:18.726Z
created_by: codex
atomicity:
  outcomes: ["Make the reviewed Sinabis projection reproducible through the signed split and guarded trainer inputs."]
  packets: ["Replay the exact source, bind its lineage in grouping and verify the guarded input contract."]
  independent_acceptance: false
  boundary_reason: "The projected source and lineage must survive replay through the consumer boundary."
---

# FDEC-247 — Replay the reviewed Sinabis source through guarded admission

Public baseline `91f83a3ff05f2a71c4075a7d53d3a7bb46ef5160`. Manual publication follows FDTasks 5.7.
The local admission engine retains its qualified policy. This is D003
source compatibility for the existing measurement. The D013 stable release
prerequisite continues to govern second-round model work.

Use only `training/config/sinabis-reviewed-source-v1.json` and its pinned
10K artifact. Rebuild the receipt from the reviewed source and retain exact
component and Oil family lineage during independent grouping. Preserve
ordinary ingestion and signed consent. Scope includes source replay in
`training/augmentation/`, grouping in `training/splits/`, directly
affected `training/finetune/tests/` and task evidence. Other source versions,
training, labels and redistribution are outside this task.

| AC ID | Scenario | Trusted check | Expected result |
| --- | --- | --- | --- |
| AC-01 | Exact reviewed source reaches the signed inventory and guarded input boundary | Run the pinned Parquet preparation and replay locally and run the Sinabis trainer admission fixture | Receipt and projection reproduce and lineage keeps the family in one split. |
| AC-02 | Altered artifact, receipt, lineage, origin or consent | Run the focused source and trainer negative fixtures | Tampered inputs are rejected and existing output survives. |
| AC-03 | Ordinary source receipt and signed split compatibility | Run the local split and trainer software suites | Legacy admission and independent grouping pass. |

Publish aggregate verification and exact commands. Keep source and per-record
material in protected storage.
