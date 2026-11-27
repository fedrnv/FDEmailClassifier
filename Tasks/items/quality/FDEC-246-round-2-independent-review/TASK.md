---
schema: fdtasks-spec/v3
id: FDEC-246
title: "Independently review the evaluated round-2 candidate"
type: Task
area: quality
component: post-1-0-second-round-training
epic_id: FDEC-EPIC-D013
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-239, FDEC-245]
created_at: 2026-11-27T21:01:44Z
created_by: "project-owner-authorized planning"
atomicity:
  outcomes: ["Independently review the evaluated round-2 candidate"]
  packets: ["Deliver and verify this single bounded outcome."]
  independent_acceptance: false
  boundary_reason: "One coherent result with its direct acceptance and failure boundaries."
---

# FDEC-246 — Independently review the evaluated round-2 candidate

## Goal and bounded implementation packet
Obtain an independent acceptance review of the exact gate-tested candidate,
release-before-training evidence, dataset rights and partition independence,
validation-only selection, measured quality, export/API compatibility and recovery.
Use a different person or fresh independent model session and disclose that boundary.
Store immutable REQUEST.md/RESULT.md under this Epic reviews/<round> with source,
policy, model/data/configuration and gate evidence hashes. Only Accepted for the
current passing candidate completes this item. Findings become bounded correction
items in D013; append events to reopen gate/review and retain prior rounds.
Public release of improved weights is a separate artifact-specific rights and
publication decision; it never overwrites stable 1.0 implicitly.

## Inputs and source baseline
Owner instruction of 2026-11-27 and D013 mandatory ordering. Planning base:
`d262635e3e185a70d7ac5c297e21d850bbc4f7f2`. Pin current source, accepted task/dependency state, policy and exact
private artifact identities again before dispatch. This task does not claim that
its prerequisites are currently complete.

## Scope and allowed paths
Tasks/epics/FDEC-EPIC-D013/reviews/; own task events/evidence.

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
| AC-01 | Independently review the evaluated round-2 candidate, with exact source/artifact and dependency evidence. | Local focused acceptance / independent review | Independent reviewer checks the bound gate result and exact source/artifact identities and records an explicit Accepted or Rejected result. | Authorized local host and private admitted inputs; pin exact commands at readiness. | Reproducible evidence satisfies the stated outcome; all limitations explicit. |
| AC-02 | Missing prerequisite or invalid input cannot claim completion or corrupt accepted artifacts. | Local negative/boundary verification | Same-author self-review, stale candidate, missing release proof or unresolved blocking finding cannot be Accepted. | Bounded invalid/missing-input cases, no raw emails in Git. | Explicit failure/blocker; stable release and prior evidence preserved. |

## Completion evidence
Record exact local commands, source/policy hashes, environment, input identities,
expected/actual results, evidence references, cleanup and limitations. Readiness
must bind the two accepted ACs and impact-selected checks before execution. No
claim, completion event, version request or activation is created by this plan.
