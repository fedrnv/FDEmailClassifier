---
schema: fdtasks-spec/v3
id: FDEC-242
title: "Prepare a balanced reviewed round-2 corpus"
type: Task
area: ai
component: post-1-0-second-round-training
epic_id: FDEC-EPIC-D013
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-239, FDEC-240, FDEC-241]
created_at: 2026-11-27T21:01:44Z
created_by: "project-owner-authorized planning"
atomicity:
  outcomes: ["Prepare a balanced reviewed round-2 corpus"]
  packets: ["Deliver and verify this single bounded outcome."]
  independent_acceptance: false
  boundary_reason: "One coherent result with its direct acceptance and failure boundaries."
---

# FDEC-242 — Prepare a balanced reviewed round-2 corpus

## Goal and bounded implementation packet
Produce one private, versioned and reviewed corpus with frozen grouped
train/validation/final-test manifests. Reuse prior TRAIN rows, mix new diverse
examples and retain old skills; prior validation/test never become training by
accident. Deduplicate across every source and the first-round cohort using exact
and near-duplicate checks; keep threads, source/template families and translations
in one partition. Cross-corpus overlap must be reported. Label mappings must
preserve independent spam/phishing and unknown masks; action labels need explicit
recipient-context guidelines and independent review. Add rare topics, actions,
high priority, hard benign security examples, long and short messages and target
languages. Aim initially at 10,000-20,000 reviewed training examples, adjusting
only with a documented coverage/rights reason, never by counting repeated visits.
Reserve an independent security test with a target of at least 300 positives per
security head and 3,000 reviewed benign emails overall; report unmet support and
per-language gaps instead of a blanket multilingual claim. These are planned
sample targets, not accuracy guarantees. Do not open final test labels during
training or threshold selection; exclude attacker URLs/attachments from execution.

## Inputs and source baseline
Owner instruction of 2026-11-27 and D013 mandatory ordering. Planning base:
`d262635e3e185a70d7ac5c297e21d850bbc4f7f2`. Pin current source, accepted task/dependency state, policy and exact
private artifact identities again before dispatch. This task does not claim that
its prerequisites are currently complete.

## Scope and allowed paths
training/datasets/; training/augmentation/; private corpus manifests; docs/training/; own task evidence.

## Execution and recovery
Planning only; no claim, completed release, dataset admission or training is implied.
Before execution refresh main, reconstruct dependencies and ownership, pin FDTasks
5.7 and applicable rule/source identities, publish readiness and the exclusive
claim using the supported repository workflow. All tasks are medium and have one
outcome. Local checks precede publication; hosted Actions are workflow_dispatch
build/package/publish only, never acceptance or integration tests. Keep datasets,
PII, weights and checkpoints private; public artifacts need exact rights and
integrity review. Preserve accepted specs and prior evidence. Stop on missing
rights, resources, credentials or failed acceptance; retain recoverable artifacts.
Reuse existing tooling and accepted tasks; do not implement a duplicate SDK,
trainer or release pipeline. Actual device switching follows FDEC-087.

## Acceptance matrix
| AC ID | Observable criterion | Test level/scenario | Trusted command or steps | Fixture/environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | Prepare a balanced reviewed round-2 corpus, with exact source/artifact and dependency evidence. | Local focused acceptance | Run existing local ingestion, annotation and grouped-split validators; inspect sampled mappings and coverage with independent reviewed labels. | Authorized local host and private admitted inputs; pin exact commands at readiness. | Reproducible evidence satisfies the stated outcome; all limitations explicit. |
| AC-02 | Missing prerequisite or invalid input cannot claim completion or corrupt accepted artifacts. | Local negative/boundary verification | Train/validation/test overlap, shared translated/template families, unreviewed remapping or a blocked source rejects the corpus; preserve the prior frozen cohort. | Bounded invalid/missing-input cases, no raw emails in Git. | Explicit failure/blocker; stable release and prior evidence preserved. |

## Completion evidence
Record exact local commands, source/policy hashes, environment, input identities,
expected/actual results, evidence references, cleanup and limitations. Readiness
must bind the two accepted ACs and impact-selected checks before execution. No
claim, completion event, version request or activation is created by this plan.
