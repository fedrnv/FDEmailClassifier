---
schema: fdtasks-spec/v3
id: FDEC-244
title: "Select and calibrate round-2 candidates on validation"
type: Task
area: ai
component: post-1-0-second-round-training
epic_id: FDEC-EPIC-D013
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-239, FDEC-243]
created_at: 2026-11-27T21:01:44Z
created_by: "project-owner-authorized planning"
atomicity:
  outcomes: ["Select and calibrate round-2 candidates on validation"]
  packets: ["Deliver and verify this single bounded outcome."]
  independent_acceptance: false
  boundary_reason: "One coherent result with its direct acceptance and failure boundaries."
---

# FDEC-244 — Select and calibrate round-2 candidates on validation

## Goal and bounded implementation packet
Select one candidate configuration and calibrate per-head/per-label thresholds
using validation only. Compare first-round frozen configuration, fresh and
continued adapters under identical eligible labels and sampling. Analyze security
recall/FPR jointly with decision coverage and abstentions; retain unknown when
unsupported rather than lowering thresholds blindly. Choose the operating point
against objectives frozen by FDEC-240; keep natural-prevalence and balanced
challenge results separate. Record threshold stability and uncertainty; no
confidence claims from tiny pure tails. Freeze exact model, adapter, calibration,
input prompt, tokenizer and runtime contract hashes before the gate opens the
new final test. A candidate that misses objectives remains rejected; a valid
negative experiment may retain 1.0 but cannot claim improved quality.

## Inputs and source baseline
Owner instruction of 2026-11-27 and D013 mandatory ordering. Planning base:
`d262635e3e185a70d7ac5c297e21d850bbc4f7f2`. Pin current source, accepted task/dependency state, policy and exact
private artifact identities again before dispatch. This task does not claim that
its prerequisites are currently complete.

## Scope and allowed paths
training/calibration/; training/eval/; docs/training/; private selection manifests; own task evidence.

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
| AC-01 | Select and calibrate round-2 candidates on validation, with exact source/artifact and dependency evidence. | Local focused acceptance | Replay validation-only selection/calibration against immutable candidate scores and confirm first-round comparison and frozen final configuration hashes. | Authorized local host and private admitted inputs; pin exact commands at readiness. | Reproducible evidence satisfies the stated outcome; all limitations explicit. |
| AC-02 | Missing prerequisite or invalid input cannot claim completion or corrupt accepted artifacts. | Local negative/boundary verification | Any final-test-derived threshold/model selection, unsupported confidence or changed selected artifact rejects selection. | Bounded invalid/missing-input cases, no raw emails in Git. | Explicit failure/blocker; stable release and prior evidence preserved. |

## Completion evidence
Record exact local commands, source/policy hashes, environment, input identities,
expected/actual results, evidence references, cleanup and limitations. Readiness
must bind the two accepted ACs and impact-selected checks before execution. No
claim, completion event, version request or activation is created by this plan.
