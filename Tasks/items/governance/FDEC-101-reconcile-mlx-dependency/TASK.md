---
schema: fdtasks-spec/v3
id: FDEC-101
title: "Reconcile MLX preparation dependency without waiving CUDA acceptance"
type: Correction
area: governance
component: dependency-amendment-admission
epic_id: FDEC-EPIC-S001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-019]
created_at: 2026-11-21T00:12:00Z
created_by: codex
atomicity:
  outcomes: ["Apply a strictly validated append-only FDEC-087 dependency amendment so MLX preparation can follow verified export independently of unfinished CUDA acceptance, with all original task and Epic criteria preserved."]
  packets: ["Specify and verify the dependency interpretation boundary and its exact MLX planning correction."]
  independent_acceptance: false
  boundary_reason: "One contradictory dependency and the directly necessary shared validator and negative admission checks; no training backend or acceptance reduction."
---

# FDEC-101 MLX dependency reconciliation

## Defect and authority

FDEC-087 AC-05 states that GPU VPS/PyTorch are not prerequisites to approved Mac
training. Its initial dependency on FDEC-016 nevertheless waits for that task's
supported-CUDA LoRA/QLoRA checkpoint acceptance. FDEC-016 currently has a verified
CPU replay but no CUDA device. FDEC-019 export acceptance is Done. This is an
observable orchestration defect preventing independent Stage A MLX development,
not permission to mark CUDA training complete or bypass a device confirmation.

The owner explicitly authorized continued independent software development and
append-only task-contract correction when required. No new owner consent,
training right or physical host access is asserted. Preserve every original
TASK.md, criterion, prior dependency event, and existing closure/request.

## Scope and outcome

Allowed paths: scripts/validate_tasks; Tasks/dependency-amendments;
Tasks/policy/dependency-amendment-1.0.md; FDEC-087 events; S001 events;
docs/training/MACBOOK_M4_HANDOFF.md; this task's own events/evidence/request.
Implement one versioned local interpretation of explicit, hash-bound dependency
amendments. Bind source/specification, exact prior/new sets, separate S001
Correction and explicit S001 adoption. Unknown, stale, ambiguous or unauthorized
records reject. The governing Correction must itself remain a new dependency,
so no affected task can dispatch while its process correction is unverified.
All ordinary graph, source/readiness, closure and license checks remain in force.

Apply only the reviewed initial case: replace FDEC-087's prior [FDEC-016] with
[FDEC-019, FDEC-101]. The original FDEC-016 and FDEC-087 acceptance is unchanged.
FDEC-020 must still depend on FDEC-015, FDEC-016 and FDEC-087, and D003 cannot
close until their original outcomes, gate and independent review are accepted.
Update the handoff explanation. Do not develop MLX or switch hosts in this task.

This compatible local envelope extension applies pinned FDTasks 5.6 append-only
dependency/readiness requirements, rather than inventing upstream 5.7 or editing
the pinned normative/adoption documents. Publish its immutable local 1.0 contract
and S001 adoption/history entry under this separate Correction. Keep S001 open.

## Failure/recovery and non-goals

Fail before dispatch on invalid amendments. No record rewrite, implicit removal,
self-approval, terminal task amendment, duplicate records, unsafe path or cycle.
Existing versioned identity-collision replacements keep their original checks.
No acceptance change, new dataset approval, model publication, actual training,
device transition, paid host, credentials, data or other repository modification.
After verification resume D003 at FDEC-087 Stage A under fresh readiness; before
machine-specific execution retain explicit owner confirmation and data admission.

## Acceptance matrix

| AC ID | Observable criterion | Level/scenario | Trusted command or steps | Environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | Explicit adopted exact amendment makes FDEC-087 depend on verified FDEC-019 and governing FDEC-101 while preserving original criteria and D003 gate members | Focused integration | Run test-dependency-amendments.ps1, repository validator and shared admission dependency boundary | Local metadata-only Git fixtures and current repository | Exact intended graph, governing Correction blocks premature dispatch; no criterion/GPU/rights waiver |
| AC-02 | Invalid dependency amendments cannot remove prerequisites implicitly or bypass ordinary admission/history | Negative/direct compatibility | Exercise stale prior/spec/source, missing adoption/Correction, duplicates/unknown fields, terminal targets, unsafe paths and cycles; run existing readiness/acceptance and relationship-migration checks | Owned metadata fixtures | Explicit rejection; ordinary dependencies, immutable bytes and existing closure/request validation unchanged |

## Completion

Record exact source/policy, preemption checkpoint, contract/adoption identities,
commands/results, failures and cleanup. Close only this bounded Correction with
one correctly typed correction_closed request. No development Epic closure or
version allocation. Revalidate FDEC-087 readiness on the next separate turn.
