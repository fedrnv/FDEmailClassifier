---
schema: fdtasks-spec/v3
id: FDEC-243
title: "Train reproducible round-2 LoRA candidates"
type: Task
area: ai
component: post-1-0-second-round-training
epic_id: FDEC-EPIC-D013
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-239, FDEC-240, FDEC-241, FDEC-242]
created_at: 2026-11-27T21:01:44Z
created_by: "project-owner-authorized planning"
atomicity:
  outcomes: ["Train reproducible round-2 LoRA candidates"]
  packets: ["Deliver and verify this single bounded outcome."]
  independent_acceptance: false
  boundary_reason: "One coherent result with its direct acceptance and failure boundaries."
---

# FDEC-243 — Train reproducible round-2 LoRA candidates

## Goal and bounded implementation packet
Execute a bounded second training experiment with the existing Qwen3-0.6B
pipeline. Compare continuation from the best first-round adapter with a fresh
adapter from the same pinned base, using the same admitted corpus and controlled
budget. Freeze seeds, sampling weights, learning rates, rank, effective batch,
sequence/truncation handling, checkpoint cadence and numeric stop conditions before
starting. Budget at most two candidate runs of up to 1,500 optimizer updates each
and one resume verification; widen only through an explicit documented scope
change. Retain prior-data replay and balance by task/language, monitor validation
macro-F1/rare-topic/action/security behavior and stop on deterioration or nonfinite
loss. Keep checkpoint/resume and input provenance. Training must check the exact
published FDEC-239 release proof before launch and resume. Preserve the stable
1.0 release and first-round adapters; do not silently substitute its model.

## Inputs and source baseline
Owner instruction of 2026-11-27 and D013 mandatory ordering. Planning base:
`d262635e3e185a70d7ac5c297e21d850bbc4f7f2`. Pin current source, accepted task/dependency state, policy and exact
private artifact identities again before dispatch. This task does not claim that
its prerequisites are currently complete.

## Scope and allowed paths
training/config/; training/finetune/; docs/training/; private checkpoints; own task evidence.

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
| AC-01 | Train reproducible round-2 LoRA candidates, with exact source/artifact and dependency evidence. | Local focused acceptance | Run admitted real training locally on the confirmed host and verify checkpoint resume, input hashes and release-proof admission. | Authorized local host and private admitted inputs; pin exact commands at readiness. | Reproducible evidence satisfies the stated outcome; all limitations explicit. |
| AC-02 | Missing prerequisite or invalid input cannot claim completion or corrupt accepted artifacts. | Local negative/boundary verification | Absent 1.0 proof, changed/unapproved corpus, final-test access, nonfinite training or missing checkpoint integrity stops the run with recoverable state. | Bounded invalid/missing-input cases, no raw emails in Git. | Explicit failure/blocker; stable release and prior evidence preserved. |

## Completion evidence
Record exact local commands, source/policy hashes, environment, input identities,
expected/actual results, evidence references, cleanup and limitations. Readiness
must bind the two accepted ACs and impact-selected checks before execution. No
claim, completion event, version request or activation is created by this plan.
