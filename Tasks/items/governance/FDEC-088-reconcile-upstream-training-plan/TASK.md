---
schema: fdtasks-spec/v3
id: FDEC-088
title: "Reconcile upstream training plan with existing immutable task identities"
type: Correction
area: governance
component: task-identity-and-plan-synchronization
epic_id: FDEC-EPIC-S001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T17:40:00Z
created_by: "codex under owner-requested project synchronization"
atomicity:
  outcomes: ["Integrate the owner's updated GitHub development/training plan while preserving accepted local history, resolving task identity collisions and retaining valid dependency and admission semantics."]
  packets: ["Import the pinned owner plan, append identity resolutions and relationship amendments, and locally verify the resulting task graph and immutable records."]
  independent_acceptance: false
  boundary_reason: "A coherent plan synchronization cannot be accepted with duplicate task IDs, broken dependencies or discarded immutable source records."
---

# FDEC-088 — Reconcile upstream training plan

## Goal

Integrate the owner-requested GitHub plan update with the current development checkout. Retain all existing work, accepted task records and upstream planning requirements. Resolve duplicate identities before resuming development from the updated dependency graph.

## Inputs and source baseline

Owner instruction to update the project and follow the revised development/training plan. Observed upstream main: `0ea1e407e32eb2671226ab9f8430e54e4207d6b7`, including planning commits `977ce837182d612691d5649c80f0aac5ea74c614` and `57da47a419e3031974121518410250483d0dd625`. Pin the actual local source, upstream source and FDTasks policy at readiness. Upstream FDEC-074 through FDEC-083 collide with locally accepted identities; FDEC-084 through FDEC-087 are currently free. Preserve FDEC-087's Mac M4 handoff requirements and D003 relationships. Read the exact upstream plan before selecting replacement IDs.

## Scope and allowed paths

`Tasks/` for imported owner planning, new identity resolutions, relationship events and this correction's evidence; `scripts/validate_tasks/` for narrowly necessary identity/relationship validation and focused regression tests; `README.md`, `docs/` and `training/augmentation/` only for importing owner documentation and reconciling current work/hardware guidance with the new plan. No unrelated functional implementation.

## Non-goals

No model training, source-rights promotion, Mac transition, server purchase, publication, push, changes to existing closed task specifications or modification of another repository. Do not execute the newly planned training or benchmark Epics during synchronization.

## Boundaries and compatibility

Do not overwrite or delete accepted local records or imported owner specifications. Use append-only identity migrations and relationship amendments, preserving exact input identities. New replacement specifications must trace back to the original source and carry its requirements. Any validator extension must keep legacy migration guarantees and reject incomplete or forged migration history. Retain one active development Epic; do not make enhancement Epics dependencies of the baseline release or redefine the active Goal. Owner-approved Mac M4 training is operator-gated and does not permit an automatic machine switch.

## Failure and recovery

Checkpoint current work before integration. Resolve ordinary merge conflicts autonomously using both source histories. On invalid identity bindings or graph, reject admission and repair locally; do not weaken checks or erase history. Retain recoverable Git history, private data and unrelated IDE state.

## Local acceptance matrix

| AC ID | Observable criterion | Test level/scenario | Trusted command or steps | Fixture/environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | The pinned owner development/training plan is integrated with unique task identities, preserved source requirements and correct effective Epic/dependency relationships | Local integration and source comparison | Compare imported source identities, execute repository validation and focused identity tests | Local Git checkout and disposable metadata-only fixtures | Both histories retained; owner Mac/rights/benchmark requirements preserved; no duplicate IDs or broken graph |
| AC-02 | Invalid or incomplete identity migrations cannot change admission and accepted historical records remain intact | Negative migration and compatibility | Exercise missing/tampered migration history, mismatched relationship replacements and existing process checks locally | Disposable synthetic task metadata | Explicit rejection with original source state retained; legacy checks still pass |

## Completion evidence

Record exact local/upstream/policy commits, ID mapping, relationship changes, merge reconciliation, local commands/results and current next dependency-ready task. Close only after the integrated graph and negative checks pass, with a typed immutable closure proof and one correction version request. No training or data admission is implied by plan synchronization.
