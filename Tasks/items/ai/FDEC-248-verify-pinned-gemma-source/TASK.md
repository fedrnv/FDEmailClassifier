---
schema: fdtasks-spec/v3
id: FDEC-248
title: "Verify the pinned Gemma-generated email source"
type: Task
area: ai
component: dataset-source-audit
epic_id: FDEC-EPIC-D003
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-247]
created_at: 2026-11-27T21:11:21.782Z
created_by: codex
atomicity:
  outcomes: ["Verify the pinned Gemma-generated email artifact and publish the scoped source audit for guarded integration."]
  packets: ["Reproduce the exact identity and screening results and record the source decision."]
  independent_acceptance: false
  boundary_reason: "The source decision must be bound to the exact artifact and its reproduced screening evidence."
---

# FDEC-248 — Verify the pinned Gemma-generated email source

Public baseline `770552e2a1808a9a98c33ea433e431715de6d3a0`. Manual publication follows FDTasks 5.7.
This is D003 source evidence for the existing FDEC-015 measurement.

Reverify the protected JSONL artifact at the pinned dataset revision and
the historical scoped source audit. Confirm publisher-declared provenance
and separate dataset terms from model release rights. Compare the
normalized pairs to the exact earlier reviewed sources. Preserve the
historical sampling limitation. The task scope is this item's audit tools
and aggregate evidence. Production admission, labels, training, publication
of source data or model weights and D013 second-round work are outside scope.

| AC ID | Scenario | Trusted check | Expected result |
| --- | --- | --- | --- |
| AC-01 | Exact pinned input and reproducible scoped source audit | Run the reviewed inspector against the pinned private source and the two admitted prior runs. Confirm pinned publisher metadata. | Exact screened counts and aggregate comparison match the historical audit and the source decision states its limits. |
| AC-02 | Changed exact-size artifact and public evidence boundary | Run the inspector self-test and review the staged evidence. | Changed bytes fail before parsing and public evidence contains only source identity, methodology, counts and hashes. |
