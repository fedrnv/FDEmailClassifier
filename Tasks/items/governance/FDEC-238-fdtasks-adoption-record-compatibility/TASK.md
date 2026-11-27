---
schema: fdtasks-spec/v3
id: FDEC-238
title: "Validate accepted FDTasks adoption records"
type: Correction
area: governance
component: task-validator
epic_id: FDEC-EPIC-S001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-27T20:50:27.000Z
created_by: codex
atomicity:
  outcomes: ["Restore repository validation for the accepted FDEC-102 adoption records."]
  packets: ["Teach local repository validation to read the accepted adoption evidence and verify its boundary."]
  independent_acceptance: false
  boundary_reason: "The accepted record, membership, transitions and closure must be validated together to restore the ledger."
---

# FDEC-238 — Validate accepted FDTasks adoption records

## Goal

Restore the local repository validator after the published FDEC-102 developer
policy adoption. On a clean published baseline the existing validator rejects
the accepted inline atomicity mapping before validating the ledger. The
adoption also has an explicit status and closure envelope.

## Authority and scope

Start from published source 0b34f8fe8ccbd606fc41b45982080e733378e398. Developer policy 5.7 governs manual
publication. Its SHA-256 is
`b7c6929e7bbf540ec19cf23beeca24d47030c7654ba5501e019ce5938b137dd8`.
The existing repository validator retains its qualified lifecycle boundary.
Scope is `scripts/validate_tasks/`, directly related validator checks and this
task's append-only records. This change adds compatibility with immutable
published history. It does not activate a 5.7 scheduler or let unpublished
claims qualify. No accepted record, branch rule, workflow or release policy
may be rewritten. Reject altered adoption evidence and unsupported new
record forms with an explicit error.

## Local acceptance

| AC ID | Scenario | Trusted check | Expected result |
| --- | --- | --- | --- |
| AC-01 | Validate the actual public ledger with the accepted FDEC-102 records | Run `pwsh -NoProfile -File scripts/validate_tasks/repository.ps1 -Root .` on the exact candidate | FDEC-102 is projected as Done under S001 with its original version request. |
| AC-02 | Exercise the compatibility boundary with altered or substituted records | Run the focused test under this task's evidence directory in a disposable local fixture | Reject tampered FDEC-102 evidence and unsupported adoption envelopes on another task while preserving ordinary legacy record validation. |

Record the exact source, positive and negative checks, and evidence hashes.
