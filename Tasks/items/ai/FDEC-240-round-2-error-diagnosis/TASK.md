---
schema: fdtasks-spec/v3
id: FDEC-240
title: "Diagnose the frozen first-round errors"
type: Task
area: ai
component: post-1-0-second-round-training
epic_id: FDEC-EPIC-D013
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-239]
created_at: 2026-11-27T21:01:44Z
created_by: "project-owner-authorized planning"
atomicity:
  outcomes: ["Diagnose the frozen first-round errors"]
  packets: ["Deliver and verify this single bounded outcome."]
  independent_acceptance: false
  boundary_reason: "One coherent result with its direct acceptance and failure boundaries."
---

# FDEC-240 — Diagnose the frozen first-round errors

## Goal and bounded implementation packet
Produce one reproducible diagnosis of the 2026-11-27 frozen configuration.
Recover private run manifests, exact source/config/model revisions, training
source composition, counts per label/language and all checkpoint selection
results. Distinguish 1,950 unique examples from 6,000 weighted visits; establish
why the newest 1,500-step candidate was not selected. Report confusion matrices
for actions and priority, topic support and both all-12 and supported-label
macro-F1, security raw-score/threshold/abstention distributions and coverage.
Compare always-archive and always-normal baselines and the untrained base on a
permitted development cohort. Never fit to the previous final test or invent
private evidence that cannot be recovered. Classify missing evidence explicitly.
Freeze measurable round-2 objectives on validation before new test admission:
per-head macro-F1/recall, supported per-language outcomes, security precision,
recall/FPR and coverage, and retained baseline behavior. Separate observed
first-round facts from hypotheses and proposed changes.

## Inputs and source baseline
Owner instruction of 2026-11-27 and D013 mandatory ordering. Planning base:
`d262635e3e185a70d7ac5c297e21d850bbc4f7f2`. Pin current source, accepted task/dependency state, policy and exact
private artifact identities again before dispatch. This task does not claim that
its prerequisites are currently complete.

## Scope and allowed paths
docs/training/; training/eval/ diagnostic tooling; own task evidence.

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
| AC-01 | Diagnose the frozen first-round errors, with exact source/artifact and dependency evidence. | Local focused acceptance | Replay aggregate first-round metrics and inspect per-label support and selection records against the frozen private manifests. | Authorized local host and private admitted inputs; pin exact commands at readiness. | Reproducible evidence satisfies the stated outcome; all limitations explicit. |
| AC-02 | Missing prerequisite or invalid input cannot claim completion or corrupt accepted artifacts. | Local negative/boundary verification | Unavailable private evidence remains unavailable; unsupported labels and abstentions cannot become true negatives or confident decisions. | Bounded invalid/missing-input cases, no raw emails in Git. | Explicit failure/blocker; stable release and prior evidence preserved. |

## Completion evidence
Record exact local commands, source/policy hashes, environment, input identities,
expected/actual results, evidence references, cleanup and limitations. Readiness
must bind the two accepted ACs and impact-selected checks before execution. No
claim, completion event, version request or activation is created by this plan.
