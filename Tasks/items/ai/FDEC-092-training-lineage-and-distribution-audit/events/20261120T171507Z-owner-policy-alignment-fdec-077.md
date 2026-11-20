---
schema: fdtasks-event/v3
event_id: EVT-20261120T171507Z-FDEC-POLICY-077-reidentified-FDEC-092
task_id: FDEC-092
event_type: scope-amended
created_at: 2026-11-20T17:15:07Z
actor: "project-owner-requested policy alignment"
base_revision: "977ce837182d612691d5649c80f0aac5ea74c614"
server_revision: null
---

# Align accepted delivery criteria with free OSS and commercial integration policy

## Payload

Approved product rule: see `docs/legal/COMMERCIAL_USE_POLICY.md` and `docs/PRODUCT_DESCRIPTION.md` (2026-11-20). Publish provenance & weight release eligibility separately: a model may be used commercially only within the reviewed license permissions and weights may be published only after all source/model redistribution checks. If not cleared, keep private and state why.

## Additional acceptance criteria

AC: separate commercial-inference and public-weight checks are recorded; fail-closed model release with reproducible manifest.

## Compatibility and verification

Keep original TASK.md immutable and existing scope/acceptance requirements intact. This addition only clarifies product licensing, distribution and public messaging within the task's existing responsibility. Run focused checks at implementation time; no completed code, license clearance, model shipment, external deployment or tests are claimed by this event.
