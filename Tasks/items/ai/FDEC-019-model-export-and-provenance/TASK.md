---
schema: fdtasks-spec/v3
id: FDEC-019
title: "Model export and provenance"
type: Task
area: ai
component: training-and-evaluation
epic_id: FDEC-EPIC-D003
size: medium
initial_priority: P2
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T10:46:00Z
created_by: "project-planning"
atomicity:
  outcomes: ["Export supported GGUF and adapter variants, tokenizer/chat-template metadata, SBOM, dataset manifest and model cards; release only cleared weights."]
  packets: ["Implement and verify the single implementation contract."]
  independent_acceptance: false
  boundary_reason: "One independently verifiable implementation outcome and its direct compatibility checks."
---

# FDEC-019 — Model export and provenance

## Goal
Export supported GGUF and adapter variants, tokenizer/chat-template metadata, SBOM, dataset manifest and model cards; release only cleared weights.

## Inputs and source baseline
New public repository README and upstream FDTasks v5.6 policy. Freeze exact upstream source SHA, relevant dependency versions and current repository commit during readiness admission; task is Planned and not dispatch-ready until that evidence is recorded.

## Scope and allowed paths
training/export; models; docs/models (only paths directly needed by this outcome and its focused tests).

## Non-goals
Unrelated Epics, production credentials, raw email/data inclusion, unverified trained weight publication and cross-project repository modifications. 

## Boundaries and compatibility
Keep public API/model formats versioned, privacy safe, offline-capable where applicable. Preserve Apache-2.0 project code licensing and third-party licenses. Do not infer multilingual accuracy or phishing reliability without measurements.

## Failure and recovery
Fail closed on licensing, security, incompatible model/API or invalid artifacts; preserve prior accepted release/model and retry only after corrective input. No automatic external deployment or upload.

## Ordered implementation packets
One cohesive packet: Export supported GGUF and adapter variants, tokenizer/chat-template metadata, SBOM, dataset manifest and model cards; release only cleared weights.

## Readiness, impact and acceptance matrix
Policy: FDTasks 5.6, upstream linked in root AGENTS.md; pin hash on dispatch. Risk: medium. Direct impact: training/export; models; docs/models. Stop on missing trust boundary/credentials/test fixture or failed verification.

| AC ID | Observable criterion | Test level/scenario | Trusted command or steps | Fixture/environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | Export supported GGUF and adapter variants, tokenizer/chat-template metadata, SBOM, dataset manifest and model cards; release only cleared weights. | Focused local acceptance | Local executable check: Test GGUF load/round trip and release manifest license gate. | Local checkout with synthetic/non-sensitive fixtures | Contract satisfied with recorded PASS evidence |
| AC-02 | Invalid/missing input does not silently corrupt state or publish unsafe output | Negative/boundary | Run negative input / failure scenario locally | Synthetic invalid fixture | Explicit error and preserved original state |

## Completion evidence and cleanup
Record exact source SHA, policy SHA, commands, environment, expected/actual outcome, compatibility implications, cleanup and any reviewer result. No completion is claimed by this planned record.
