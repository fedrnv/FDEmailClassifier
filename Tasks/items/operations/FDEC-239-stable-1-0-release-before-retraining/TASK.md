---
schema: fdtasks-spec/v3
id: FDEC-239
title: "Publish and verify stable 1.0 before retraining"
type: Task
area: operations
component: post-1-0-second-round-training
epic_id: FDEC-EPIC-D013
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-EPIC-D010, FDEC-050, FDEC-053, FDEC-059, FDEC-066, FDEC-033]
created_at: 2026-11-27T21:01:44Z
created_by: "project-owner-authorized planning"
atomicity:
  outcomes: ["Publish and verify stable 1.0 before retraining"]
  packets: ["Deliver and verify this single bounded outcome."]
  independent_acceptance: false
  boundary_reason: "One coherent result with its direct acceptance and failure boundaries."
---

# FDEC-239 — Publish and verify stable 1.0 before retraining

## Goal and bounded implementation packet
Deliver the stable 1.0 release using the already implemented library, API,
SDKs, documentation and publication pipeline. This is the mandatory entry milestone,
not a second implementation of D004-D010. A beta, source scaffold, draft release,
workflow file or successful source compilation alone does not satisfy it.
User-facing release is 1.0 (stable SemVer 1.0.0); retain FDTasks four-integer
allocation and its documented package mapping. Never hand-edit version history;
if publisher/version support is missing, complete that dependency first.

Required evidence: accepted D004-D010 API/SDK/library/documentation and review
outcomes, real local inference through released Rust/C/C++/Python interfaces and
the documented REST API, independent package install/use acceptance, an explicit
manually dispatched successful GitHub Actions build of the exact release source
for every supported target, and a published non-draft non-prerelease GitHub
Release with versioned downloadable packages, notices, checksums and usable
installation/API examples. Record run URL/ID/attempt, source SHA, tag, release URL,
asset identities and local acceptance evidence. Verify the release uses the
pre-round-2 model and reports its measured quality/abstentions honestly. Working
inference requires a legally accessible documented model path; a placeholder or
unavailable private model is insufficient for a usable release. Publication must
retain artifact-specific rights checks; this plan authorizes the requested stable
release outcome, not disclosure of unapproved weights, data or credentials.

No round-2 optimizer updates, real training/validation inference or new model
selection may run before this milestone is Done with the published evidence.
All later tasks directly depend on it. Existing historical training is preserved.

## Inputs and source baseline
Owner instruction of 2026-11-27 and D013 mandatory ordering. Planning base:
`d262635e3e185a70d7ac5c297e21d850bbc4f7f2`. Pin current source, accepted task/dependency state, policy and exact
private artifact identities again before dispatch. This task does not claim that
its prerequisites are currently complete.

## Scope and allowed paths
docs/release/; existing scripts/publish and .github/workflows publication entrypoints; own task evidence.

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
| AC-01 | Publish and verify stable 1.0 before retraining, with exact source/artifact and dependency evidence. | Local focused acceptance | Install the exact GitHub-built published 1.0 packages in a clean local environment and run the documented real inference examples; record URLs, hashes and outputs without raw emails. | Authorized local host and private admitted inputs; pin exact commands at readiness. | Reproducible evidence satisfies the stated outcome; all limitations explicit. |
| AC-02 | Missing prerequisite or invalid input cannot claim completion or corrupt accepted artifacts. | Local negative/boundary verification | Missing/failed build, wrong SHA, draft/beta release, absent package/model/docs or failed API example keeps the milestone incomplete and blocks every round-2 task. | Bounded invalid/missing-input cases, no raw emails in Git. | Explicit failure/blocker; stable release and prior evidence preserved. |

## Completion evidence
Record exact local commands, source/policy hashes, environment, input identities,
expected/actual results, evidence references, cleanup and limitations. Readiness
must bind the two accepted ACs and impact-selected checks before execution. No
claim, completion event, version request or activation is created by this plan.
