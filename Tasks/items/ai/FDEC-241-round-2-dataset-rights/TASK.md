---
schema: fdtasks-spec/v3
id: FDEC-241
title: "Audit additional round-2 data sources"
type: Task
area: ai
component: post-1-0-second-round-training
epic_id: FDEC-EPIC-D013
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-239, FDEC-240]
created_at: 2026-11-27T21:01:44Z
created_by: "project-owner-authorized planning"
atomicity:
  outcomes: ["Audit additional round-2 data sources"]
  packets: ["Deliver and verify this single bounded outcome."]
  independent_acceptance: false
  boundary_reason: "One coherent result with its direct acceptance and failure boundaries."
---

# FDEC-241 — Audit additional round-2 data sources

## Goal and bounded implementation packet
Publish exact-version inclusion/exclusion decisions and provenance/notice
requirements for candidate datasets. Prioritize MeAJOR v2 (Zenodo 18471483),
SpaPhish v5 (Mendeley hz2d6gz7pc/5), SpamShield-Datasets and
ParakweetLabs/EmailIntentDataSet. Reuse existing approved training sources only
within their permitted purpose; evaluate Sinabis subsets for missing themes,
priority and action supervision. Check primary-source content rights, generator
terms, privacy, commercial classifier training/inference and model distribution
separately. A permissive mirror tag is not a primary-content license. Exclude
PhishFuzzer CC BY-NC from commercial training absent a separate grant; preserve
current SpamAssassin/imnim exclusions until evidence resolves them. Record exact
revision, artifact hash, source family, label semantics and notices. In particular,
do not equate generic spam with phishing in aggregated datasets. No purchase or
author contact is authorized by this task. Conclude which sources are admitted;
blocked optional sources are excluded, not silently approved.

## Inputs and source baseline
Owner instruction of 2026-11-27 and D013 mandatory ordering. Planning base:
`d262635e3e185a70d7ac5c297e21d850bbc4f7f2`. Pin current source, accepted task/dependency state, policy and exact
private artifact identities again before dispatch. This task does not claim that
its prerequisites are currently complete.

## Scope and allowed paths
docs/legal/datasets/; training/datasets/; own task evidence.

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
| AC-01 | Audit additional round-2 data sources, with exact source/artifact and dependency evidence. | Local focused acceptance | Run existing dataset registry/inclusion checks locally against pinned admitted and explicitly rejected source descriptors. | Authorized local host and private admitted inputs; pin exact commands at readiness. | Reproducible evidence satisfies the stated outcome; all limitations explicit. |
| AC-02 | Missing prerequisite or invalid input cannot claim completion or corrupt accepted artifacts. | Local negative/boundary verification | Unknown provenance, incompatible restrictions, changed bytes/revision or generic spam mislabeled as phishing fails admission for that source. | Bounded invalid/missing-input cases, no raw emails in Git. | Explicit failure/blocker; stable release and prior evidence preserved. |

## Completion evidence
Record exact local commands, source/policy hashes, environment, input identities,
expected/actual results, evidence references, cleanup and limitations. Readiness
must bind the two accepted ACs and impact-selected checks before execution. No
claim, completion event, version request or activation is created by this plan.
