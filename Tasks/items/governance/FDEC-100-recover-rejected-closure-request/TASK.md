---
schema: fdtasks-spec/v3
id: FDEC-100
title: "Recover a rejected closure request without rewriting its immutable record"
type: Correction
area: governance
component: task-request-recovery
epic_id: FDEC-EPIC-S001
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T19:43:00Z
created_by: codex
atomicity:
  outcomes: ["Restore strict request validation for the rejected FDEC-099 closure through explicit hash-bound append-only recovery while preserving the original request and identity."]
  packets: ["Specify, implement and verify the single rejected-request recovery boundary and its exact initial case."]
  independent_acceptance: false
  boundary_reason: "One demonstrably invalid closure metadata record and the directly necessary generic recovery/negative checks; no source, licensing or version allocation change."
---

# FDEC-100 rejected closure-request recovery

## Problem and original evidence

Commit `65a44ee` added the first FDEC-099 request with `task_closed` although
its immutable specification is a Correction. The post-commit repository check
monitor `f3a23ebc-6157-49a6-86a6-15278c1396fe` rejects it with
`Closure request type does not match item`. The prior close admission did not
validate the not-yet-written request. This request has never passed complete
repository validation or been allocated/published. FDEC-099 must remain open
until recovery validates. Preserve the failed record, event and all proof bytes.

## Scope and readiness

Allowed: `scripts/validate_tasks`, new append-only `Tasks/request-recoveries`
records and a versioned local recovery specification/history under
`Tasks/policy`, `docs/verification`, directly necessary focused tests and own
metadata. S001 membership and affected task dependency/reopening events are
lifecycle bookkeeping. The original upstream/adoption policy and accepted
requests/specifications/events/evidence must not be edited or deleted.

Pin source, policy, governing rules, the exact rejected request/specification,
the failure evidence and preserved original FDEC-099 closure proof. Record the
bootstrap reason explicitly: ordinary repository admission currently rejects
the malformed request. Limit any bootstrap to this process Correction and
verify normal strict admission after recovery. Never hide the initial failure.

## One recovery contract

Add an explicit audited append-only recovery path for a demonstrably rejected,
unallocated request's type mismatch. Bind the exact original bytes/identity,
task specification and first closure proof, recorded rejection, reason and
governing S001 Correction. The only effective correction is the type derived
from the immutable work-item kind (`Correction` => `correction_closed` here).
Do not replace request_id, work_item_id, Epic, verification, summary or create
a second first-closure/version request. A valid accepted request cannot be
rewritten through recovery. Do not grant arbitrary overlay fields or bypass
duplicate, artifact, closure, history or identity checks. Preserve strict
rejection when a recovery is absent, malformed, stale, repeated or unsupported.

Document precisely how the effective validated request is derived and why this
does not authorize mutation of accepted requests or allocate a version. Share
the recovery boundary across affected request consumers so they cannot disagree
about identity or effective type. Existing license/data/model gates are outside
scope and must remain unchanged. If the recovery requires a normative exception,
record a versioned explicit local proposal/adoption and its exact authority;
do not silently weaken the pinned upstream contract.

## Acceptance matrix

| AC ID | Observable criterion | Level/scenario | Command or steps | Environment | Expected result |
| --- | --- | --- | --- | --- | --- |
| AC-01 | Exact rejected FDEC-099 request validates under an explicit audited append-only recovery with original request bytes and unique identity preserved | Focused integration | Reproduce initial rejection, validate recovered effective type against immutable Correction, check all original proof/identity bindings and normal repository admission | Local metadata-only repository fixtures and current repository | Recovery validates without request overwrite, duplicate closure request or version allocation |
| AC-02 | Invalid or overly broad recovery cannot alter a valid request or bypass original checks | Negative/direct compatibility | Exercise missing/mismatched request/spec/proof/rejection, unsupported or duplicate recoveries, altered identities/artifacts, normal valid requests and unchanged historical closure checks | Owned metadata fixtures | Explicit rejection; valid unrecovered requests and original immutable records unchanged |

## Completion and continuation

Record source/policy, exact tests including failure, accepted local recovery
authority, preserved request hash and cleanup. No publication, allocator,
external service, training, source-rights or product changes. Complete this
Correction with a correctly typed own first request checked before committing.
Then resume/reclose FDEC-099 using its preserved first request and new proof,
repeat FDEC-013 and obtain a fresh FDEC-014 review. Never count the malformed
closure or mechanical recovery as acceptance of D002.
