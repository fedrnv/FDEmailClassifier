---
schema: fdtasks-spec/v3
id: FDEC-081
title: "Admit verified development Epic closure requests"
type: Correction
area: governance
component: process
epic_id: FDEC-EPIC-S001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T13:20:00Z
created_by: codex
atomicity:
  outcomes: ["Validate one immutable first-closure request for a development Epic against its completed membership, current passing gate and independent acceptance."]
  packets: ["Implement and verify bounded offline Epic closure proof admission without allocating versions."]
  independent_acceptance: false
  boundary_reason: "One lifecycle deadlock repair; allocation and publication remain separate D008 work."
---

# FDEC-081 verified Epic closure requests

## Defect and rule layer
At e71e0ae every D001 member is Done, repeated gate passes b56bc3d and R002
independently accepts it. repository.ps1 nevertheless rejects every epic_closed
request as requiring a publisher not implemented at foundation. D008/FDEC-055
follows earlier Epic closure, so the restriction deadlocks sequential delivery.
Implement the existing pinned FDTasks 5.6 first-closure/request rule; this is no
normative successor and current/proposed normative version remains 5.6.

## Scope and continuation
Allowed implementation: scripts/validate_tasks and docs/verification. Own task,
events, evidence, first request and S001 membership are append-only bookkeeping.
No allocator, version.json/history edits, source push, release, external settings,
accepted record edits or new product behavior. FDEC-055 retains allocation scope.
Reopen FDEC-006 and FDEC-007 by events because the reviewed validator changes;
retain original requests and R002. Add this process correction as a gate dependency.
After this task, repeat gate and independent review before attempting D001 closure.
D001 alone remains active. No external authority is missing.

## Contract
Only development Epics may emit epic_closed, once per identity. Require an actual
Done transition and an Epic-local hash-bound closure proof. Bind exact historical
membership and dependency state at that transition, every member Done, mandatory
gate/review topology, successful gate and Accepted latest independent round for
the same candidate/tree/policy/gate identity. Candidate-to-closure implementation
must match: only own Epic/item ledger descendants may follow the tested source.
Reopen/reclose preserves the first verified request. Missing, stale, tampered,
wrong-scope, duplicate or special-Epic proofs reject without mutation. Unsupported
release/major requests remain rejected. Evidence validates mechanical provenance;
semantic review and the authorized append-only writer boundary remain necessary.

## Local acceptance matrix
| AC ID | Observable criterion | Local verification | Fixture/environment | Expected |
| --- | --- | --- | --- | --- |
| AC-01 | A completed development Epic with a current passing gate and independent acceptance admits exactly one first-closure request, preserved on reopen/reclose | powershell -NoProfile -File scripts/validate_tasks/test-epic-closure.ps1 | Disposable local Git repositories with synthetic gate/review evidence | Shared repository validator admits valid history; original requests remain unchanged; no allocation or publication |
| AC-02 | Incomplete, stale, tampered, mismatched, duplicate, special-Epic and evidence-free closure requests reject | Same focused script through the production repository validator plus existing reopened-item regression | Negative disposable fixtures | Explicit rejection and unchanged original repository |

## Evidence and recovery
Record policy/source/rule hashes, exact command/results, failure diagnostics and
fixture cleanup. Freeze tested implementation before closure readiness. On failure
keep D001 open and preserve accepted R002; repair only this bounded process outcome.
