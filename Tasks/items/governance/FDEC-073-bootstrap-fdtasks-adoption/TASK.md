---
schema: fdtasks-spec/v3
id: FDEC-073
title: "Bootstrap explicit FDTasks 5.6 adoption"
type: Correction
area: governance
component: process
epic_id: FDEC-EPIC-S001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T12:20:00Z
created_by: codex
atomicity:
  outcomes: ["Establish hash-bound local FDTasks 5.6 adoption and shared admission preflight."]
  packets: ["Pin policy, inventory immutable history and verify admission inputs."]
  independent_acceptance: false
  boundary_reason: "One adoption trust boundary required before product dispatch."
---

# Bootstrap explicit FDTasks 5.6 adoption

## Defect and policy identity
Root rules declare 5.6 but no S001 adoption Correction, source pin or accepted-record
inventory exists. Upstream 5.6 requires these before enforcement. This adopts the
existing upstream version; it does not modify normative rules. Current local state
is a declaration; proposed state is explicit adoption of 5.6 at source commit
00a0d019c1e73d5ecf4c4e75c42c38497c154e50. History entry: Tasks/policy/README.md.

## Scope and baseline
Baseline 40972439bad1e6b0da875e07486cb79a15455891. Allowed: this task record,
S001 membership events, Tasks/policy, scripts/validate_tasks/admission.ps1 and first
closure version request. No product work, allocator implementation or publication.
Inventory original accepted records without rewriting them. Existing special Epics
remain active. No development Epic starts in this bootstrap turn.

## Execution and recovery
Pin source bytes and hashes, inventory existing task/Epic/event records, document
shared agent admission and verify positive and tampered inputs locally. Bootstrap
readiness is manually reviewed because this task creates the first preflight.
Later actions require the shared preflight plus semantic review. Medium process
risk: a stale pin must fail closed. Correct only unaccepted candidate files on
failure; accepted adoption changes require a successor Correction. No credentials,
network mutation or disposable checkout is required.

## Acceptance matrix
| ID | Criterion | Local verification | Fixture | Expected |
| --- | --- | --- | --- | --- |
| AC-01 | Source pin, inventory, migration and shared admission are explicit | powershell -NoProfile -File scripts/validate_tasks/admission.ps1; inspect pin against git ls-files and upstream HEAD | Original local checkout | PASS; no legacy numeric Epics, workflows or pending requests; original accepted bytes unchanged |
| AC-02 | Missing readiness and altered baseline are rejected on every admission action | powershell -NoProfile -File scripts/validate_tasks/check-adoption.ps1 | Owned temporary synthetic checkout | All five actions reject each invalid input; original state unchanged |

## Completion
Record commands, policy/source hashes, environment, limitations, cleanup and next
action. Emit one correction_closed request; never hand-allocate a version.
