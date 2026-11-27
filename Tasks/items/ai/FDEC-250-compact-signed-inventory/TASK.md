---
schema: fdtasks-spec/v3
id: FDEC-250
title: "Build and verify signed splits from compact private inventories"
type: Task
area: ai
component: grouped-training-inventory
epic_id: FDEC-EPIC-D003
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-012, FDEC-249]
created_at: 2026-11-27T21:21:24.939Z
created_by: codex
atomicity:
  outcomes: ["Verify one private compact inventory through consent signing and exact grouped split build and replay."]
  packets: ["Implement the packed inventory and bind it to exact grouping and existing split entry points."]
  independent_acceptance: false
  boundary_reason: "Accounts for full leakage protection from the stored fingerprint data through the signed split."
---

# FDEC-250 — Build and verify signed splits from compact private inventories

Public baseline `f86c781426aff944115b8ba30381afdb3e7bee87`. Manual publication follows FDTasks 5.7.
Reconcile the existing local compact-inventory implementation for exact
global grouping at a Jaccard threshold of 0.80, with at least 30 million
packed fingerprints. Preserve content, source, thread and family edges,
deterministic assignment, signed current consent, source rights, rollback
and compatibility with existing v1 receipts.

Scope covers `training/splits/`, `training/manifests/sign_consent.py` and
this task's evidence. Data stays in protected storage. Model-consumer
integration, new source rights, labels, model training and publication
of data or weights are outside this task. This is a D003 dependency for
FDEC-015 and does not start D013.

| AC ID | Scenario | Trusted check | Expected result |
| --- | --- | --- | --- |
| AC-01 | Exact grouping with the private projected workload and 30 million fingerprints | Run the compact unit suite, private unsigned replay and isolated synthetic scale check | Exact fixture parity, all 33,131 public-line projected records grouped, and 30 million fingerprints accepted within the defined limit. |
| AC-02 | Signed split and failures | Run local compact build and replay fixtures | Signed current consent and exact bytes are required. Incomplete, altered and out-of-budget inputs and revoked consent fail closed. |
| AC-03 | Legacy signed inventory compatibility | Run the existing split and relevant trainer fixture suites | v1 readers, receipts and consumer behavior remain compatible. |

Record exact commands, source, outcomes and digests. Remove owned private
scale copies after verification.
