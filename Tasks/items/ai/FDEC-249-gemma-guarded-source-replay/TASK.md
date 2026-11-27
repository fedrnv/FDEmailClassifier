---
schema: fdtasks-spec/v3
id: FDEC-249
title: "Replay the audited Gemma source through guarded inputs"
type: Task
area: ai
component: training-and-evaluation
epic_id: FDEC-EPIC-D003
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-247, FDEC-248]
created_at: 2026-11-27T21:16:06.528Z
created_by: codex
atomicity:
  outcomes: ["Integrate the exact audited Gemma source into the signed split and guarded input contract."]
  packets: ["Replay the exact source, preserve source-wide grouping and verify guarded consumers."]
  independent_acceptance: false
  boundary_reason: "Replay without signed grouping and consent does not safely admit the source."
---

# FDEC-249 — Replay the audited Gemma source through guarded inputs

Public baseline `4f83dd15abcea96a71a79c4bb9648e57191aaba0`. Manual publication follows FDTasks 5.7.
Use only the artifact and published audit from FDEC-248. Verify artifact
identity and the audit evidence before decoding. Use screened candidate
subject and body fields only. Retain source-row lineage, group the entire
Gemma source in one partition and enforce the existing current consent
and full grouping checks. The source replay creates no supervision.

Scope covers `training/augmentation/`, `training/splits/`, focused guarded
input tests and this task's evidence. Preserve ordinary ingestion and the
Sinabis route. This is a D003 input prerequisite for FDEC-015. It does not
start D013, train a model, or authorize distribution of source or weights.

| AC ID | Scenario | Trusted check | Expected result |
| --- | --- | --- | --- |
| AC-01 | Exact audited source and complete guarded input admission | Run the source CLI on the pinned private artifact, replay its receipt, and run the Gemma signed split and trainer fixture | The projection matches the audit and source-wide grouping remains indivisible. |
| AC-02 | Changed source or audit, malformed data, or revoked consent | Run the direct negative Gemma fixtures | Tampered or revoked inputs are rejected before model access. |
| AC-03 | Existing Sinabis, ordinary ingestion and stock evaluation software | Run the affected split, trainer and baseline fixture suites locally | Existing signed inputs and evaluated-role protections still pass. |

Record exact source, environment, counts and hashes without committing
private records, labels, credentials or model material.
