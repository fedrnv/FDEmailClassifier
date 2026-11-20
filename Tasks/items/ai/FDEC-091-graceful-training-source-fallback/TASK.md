---
schema: fdtasks-spec/v3
id: FDEC-091
title: "Graceful training source fallback"
type: Task
area: ai
component: d011-graceful-training-source-fallback
epic_id: FDEC-EPIC-D011
size: medium
initial_priority: P2
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T16:45:00Z
created_by: "project-planning"
atomicity:
  outcomes: ["Implement rights-aware dataset selection that skips unresolved SpamAssassin, Enron or external LLM output with a clear report, and can train on project-authored cleared examples if other sources are absent."]
  packets: ["Deliver and locally verify the single graceful-training-source-fallback contract."]
  independent_acceptance: false
  boundary_reason: "One independently testable graceful-training-source-fallback outcome with direct negative and compatibility checks."
---

# FDEC-091 — Graceful training source fallback

## Goal
Implement rights-aware dataset selection that skips unresolved SpamAssassin, Enron or external LLM output with a clear report, and can train on project-authored cleared examples if other sources are absent.

## Inputs and source baseline
Upstream FDTasks v5.6, FDEC-EPIC-D011, D002/D003 approved sources, current public repository state. Pin upstream policy SHA, source SHA, and authorized inputs in a fresh readiness event before dispatch.

## Scope and allowed paths
training/datasets; training/config; training/scripts; directly affected local tests and documentation only.

## Non-goals
No automatic download, training or publication of sources without documented rights; no forced real-corpus access; no rewriting accepted D002/D003 tasks; no unauthorized external uploads; no copying private email into public git.

## Boundaries and compatibility
Commercial model training and distribution rights are separate checks. Treat a source as optional until license/consent audit admits it. Exclude denied/unknown sources and report precisely; infrastructure can complete on synthetic permitted fixtures. A trained model release requires source and quality gates; absence of real-world data must be disclosed and must not create an unsupported verified-quality claim. Public benchmark artifacts include only redistributable content and derived aggregate metrics. No credential/personal data disclosure.

## Failure and recovery
Fail closed for any unapproved dataset or corpus; keep safe fallback and evidence of skipped sources. If no permitted data exists, report insufficient_data and do not fabricate successful training or benchmark. Do not hold other independent tasks hostage to optional source approval. No silent data leakage or destructive overwrite.

## Ordered implementation packets
One cohesive outcome: Implement rights-aware dataset selection that skips unresolved SpamAssassin, Enron or external LLM output with a clear report, and can train on project-authored cleared examples if other sources are absent.

## Readiness, impact and acceptance matrix
Policy SHA pinned before execution; risk medium/high for training rights and private benchmark cohorts. Allowed paths as above; stop and escalate only source-specific incompatible rights, consent or genuine safety failures.

| AC ID | Observable criterion | Test level and scenario | Trusted command or manual steps | Fixture/environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | Implement rights-aware dataset selection that skips unresolved SpamAssassin, Enron or external LLM output with a clear report, and can train on project-authored cleared examples if other sources are absent. | Local focused acceptance | Test no-source, optional-source-denied, fallback-present and all-denied cases; all-denied reports insufficient_data and never invents an approved source. | Local checkout / owned synthetic fixtures | Documented deterministic passing outcome or explicit honest unavailable-status where source-dependent |
| AC-02 | Unknown rights or sensitive data cannot enter training/public artifacts | Negative source-boundary test | Inject missing/denied source and scan generated artifacts and logs | Synthetic rejected-source fixture | Admission rejected with reason; safe work remains available |

## Completion evidence and cleanup
Record exact commands, source SHA, policy SHA, environment, fixture identity, verification results, cohort rights, and clean-up. No rights or achieved model accuracy are asserted by this planning specification.
