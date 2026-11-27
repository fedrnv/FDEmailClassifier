---
schema: fdtasks-spec/v3
id: FDEC-245
title: "Evaluate the frozen round-2 model and library integration"
type: Task
area: quality
component: post-1-0-second-round-training
epic_id: FDEC-EPIC-D013
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-239, FDEC-240, FDEC-241, FDEC-242, FDEC-243, FDEC-244]
created_at: 2026-11-27T21:01:44Z
created_by: "project-owner-authorized planning"
atomicity:
  outcomes: ["Evaluate the frozen round-2 model and library integration"]
  packets: ["Deliver and verify this single bounded outcome."]
  independent_acceptance: false
  boundary_reason: "One coherent result with its direct acceptance and failure boundaries."
---

# FDEC-245 — Evaluate the frozen round-2 model and library integration

## Goal and bounded implementation packet
Run the single targeted local D013 integration gate on the frozen candidate.
Open the new held-out cohort once after selection and reproduce metrics through
independent aggregate replay. Report per-topic support/F1, supported/all-topic
macro-F1, action and priority confusion/baselines, high-priority recall, security
precision/recall/FPR/coverage/abstentions with sample counts and uncertainty, and
per-language results. Do not tune on test failures: preserve the result and use
a new development/final cohort for subsequent selection. Verify exported model
numerics and install/load/classify through the stable 1.0 library API with versioned
model compatibility, explicit rejection of incompatible artifacts and rollback
to the retained 1.0 model. Recheck the exact successful GitHub-built release
prerequisite. Integration tests run locally, never hosted. The report compares
against 1.0 and the first-round configuration; no aggregate metric hides a
regression in a declared acceptance objective.

## Inputs and source baseline
Owner instruction of 2026-11-27 and D013 mandatory ordering. Planning base:
`d262635e3e185a70d7ac5c297e21d850bbc4f7f2`. Pin current source, accepted task/dependency state, policy and exact
private artifact identities again before dispatch. This task does not claim that
its prerequisites are currently complete.

## Scope and allowed paths
tests/ direct model/API integration; docs/training/; own task evidence.

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
| AC-01 | Evaluate the frozen round-2 model and library integration, with exact source/artifact and dependency evidence. | Local focused acceptance | Run the declared local held-out evaluation, independent metric replay, export parity and released-package model load/classify/rollback checks on the exact candidate. | Authorized local host and private admitted inputs; pin exact commands at readiness. | Reproducible evidence satisfies the stated outcome; all limitations explicit. |
| AC-02 | Missing prerequisite or invalid input cannot claim completion or corrupt accepted artifacts. | Local negative/boundary verification | Any unmet frozen objective, leakage, artifact mismatch or broken 1.0 API/rollback fails the gate; do not publish a successful improvement claim. | Bounded invalid/missing-input cases, no raw emails in Git. | Explicit failure/blocker; stable release and prior evidence preserved. |

## Completion evidence
Record exact local commands, source/policy hashes, environment, input identities,
expected/actual results, evidence references, cleanup and limitations. Readiness
must bind the two accepted ACs and impact-selected checks before execution. No
claim, completion event, version request or activation is created by this plan.
