---
schema: fdtasks-spec/v3
id: FDEC-095
title: "Independent benchmark data specification"
type: Task
area: quality
component: d012-independent-benchmark-data-specification
epic_id: FDEC-EPIC-D012
size: medium
initial_priority: P2
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T16:45:00Z
created_by: "project-planning"
atomicity:
  outcomes: ["Define frozen test corpus schema, sample provenance, author/legal rights, consent, 12-label annotations, priority/security/action and disjointness from all training sources; explicitly separate synthetic and real-world cohorts."]
  packets: ["Deliver and locally verify the single independent-benchmark-data-specification contract."]
  independent_acceptance: false
  boundary_reason: "One independently testable independent-benchmark-data-specification outcome with direct negative and compatibility checks."
---

# FDEC-095 — Independent benchmark data specification

## Goal
Define frozen test corpus schema, sample provenance, author/legal rights, consent, 12-label annotations, priority/security/action and disjointness from all training sources; explicitly separate synthetic and real-world cohorts.

## Inputs and source baseline
Upstream FDTasks v5.6, FDEC-EPIC-D012, D002/D003 approved sources, current public repository state. Pin upstream policy SHA, source SHA, and authorized inputs in a fresh readiness event before dispatch.

## Scope and allowed paths
benchmark/spec; benchmark/fixtures; docs/benchmark; directly affected local tests and documentation only.

## Non-goals
No automatic download, training or publication of sources without documented rights; no forced real-corpus access; no rewriting accepted D002/D003 tasks; no unauthorized external uploads; no copying private email into public git.

## Boundaries and compatibility
Commercial model training and distribution rights are separate checks. Treat a source as optional until license/consent audit admits it. Exclude denied/unknown sources and report precisely; infrastructure can complete on synthetic permitted fixtures. A trained model release requires source and quality gates; absence of real-world data must be disclosed and must not create an unsupported verified-quality claim. Public benchmark artifacts include only redistributable content and derived aggregate metrics. No credential/personal data disclosure.

## Failure and recovery
Fail closed for any unapproved dataset or corpus; keep safe fallback and evidence of skipped sources. If no permitted data exists, report insufficient_data and do not fabricate successful training or benchmark. Do not hold other independent tasks hostage to optional source approval. No silent data leakage or destructive overwrite.

## Ordered implementation packets
One cohesive outcome: Define frozen test corpus schema, sample provenance, author/legal rights, consent, 12-label annotations, priority/security/action and disjointness from all training sources; explicitly separate synthetic and real-world cohorts.

## Readiness, impact and acceptance matrix
Policy SHA pinned before execution; risk medium/high for training rights and private benchmark cohorts. Allowed paths as above; stop and escalate only source-specific incompatible rights, consent or genuine safety failures.

| AC ID | Observable criterion | Test level and scenario | Trusted command or manual steps | Fixture/environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | Define frozen test corpus schema, sample provenance, author/legal rights, consent, 12-label annotations, priority/security/action and disjointness from all training sources; explicitly separate synthetic and real-world cohorts. | Local focused acceptance | Validate schema, leakage rejection, consent/rights blocks and cohort separation on synthetic fixtures. | Local checkout / owned synthetic fixtures | Documented deterministic passing outcome or explicit honest unavailable-status where source-dependent |
| AC-02 | Unknown rights or sensitive data cannot enter training/public artifacts | Negative source-boundary test | Inject missing/denied source and scan generated artifacts and logs | Synthetic rejected-source fixture | Admission rejected with reason; safe work remains available |

## Completion evidence and cleanup
Record exact commands, source SHA, policy SHA, environment, fixture identity, verification results, cohort rights, and clean-up. No rights or achieved model accuracy are asserted by this planning specification.
