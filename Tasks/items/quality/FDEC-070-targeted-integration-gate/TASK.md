---
schema: fdtasks-spec/v3
id: FDEC-070
title: "Targeted integration gate"
type: Task
area: quality
component: community-and-stable-public-release
epic_id: FDEC-EPIC-D010
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-065, FDEC-066, FDEC-067, FDEC-068, FDEC-069]
created_at: 2026-11-20T10:46:00Z
created_by: "project-planning"
atomicity:
  outcomes: ["Verify Epic FDEC-EPIC-D010 changed interfaces and direct interactions with local tests on frozen candidate."]
  packets: ["Implement and verify the single gate contract."]
  independent_acceptance: false
  boundary_reason: "One independently verifiable gate outcome and its direct compatibility checks."
---

# FDEC-070 — Targeted integration gate

## Goal
Verify Epic FDEC-EPIC-D010 changed interfaces and direct interactions with local tests on frozen candidate.

## Inputs and source baseline
New public repository README and upstream FDTasks v5.6 policy. Freeze exact upstream source SHA, relevant dependency versions and current repository commit during readiness admission; task is Planned and not dispatch-ready until that evidence is recorded.

## Scope and allowed paths
tests; scripts; docs/verification (only paths directly needed by this outcome and its focused tests).

## Non-goals
Unrelated Epics, production credentials, raw email/data inclusion, unverified trained weight publication and cross-project repository modifications. No unrelated project-wide regression.

## Boundaries and compatibility
Keep public API/model formats versioned, privacy safe, offline-capable where applicable. Preserve Apache-2.0 project code licensing and third-party licenses. Do not infer multilingual accuracy or phishing reliability without measurements.

## Failure and recovery
Fail closed on licensing, security, incompatible model/API or invalid artifacts; preserve prior accepted release/model and retry only after corrective input. No automatic external deployment or upload.

## Ordered implementation packets
One cohesive packet: Verify Epic FDEC-EPIC-D010 changed interfaces and direct interactions with local tests on frozen candidate.

## Readiness, impact and acceptance matrix
Policy: FDTasks 5.6, upstream linked in root AGENTS.md; pin hash on dispatch. Risk: medium. Direct impact: tests; scripts; docs/verification. Stop on missing trust boundary/credentials/test fixture or failed verification.

| AC ID | Observable criterion | Test level/scenario | Trusted command or steps | Fixture/environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | Verify Epic FDEC-EPIC-D010 changed interfaces and direct interactions with local tests on frozen candidate. | Focused local acceptance | Local Epic-specific changed-area integration gate, documented in DEVELOPMENT.md once implemented | Local checkout with synthetic/non-sensitive fixtures | Contract satisfied with recorded PASS evidence |
| AC-02 | Invalid/missing input does not silently corrupt state or publish unsafe output | Negative/boundary | Run negative input / failure scenario locally | Synthetic invalid fixture | Explicit error and preserved original state |

## Completion evidence and cleanup
Record exact source SHA, policy SHA, commands, environment, expected/actual outcome, compatibility implications, cleanup and any reviewer result. No completion is claimed by this planned record.
