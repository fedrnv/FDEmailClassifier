---
schema: fdtasks-event/v3
event_id: EVT-20261120T171501Z-FDEC-POLICY-001
task_id: FDEC-001
event_type: scope-amended
created_at: 2026-11-20T17:15:01Z
actor: "project-owner-requested policy alignment"
base_revision: "977ce837182d612691d5649c80f0aac5ea74c614"
server_revision: null
---

# Align accepted delivery criteria with free OSS and commercial integration policy

## Payload

Approved product rule: see `docs/legal/COMMERCIAL_USE_POLICY.md` and `docs/PRODUCT_DESCRIPTION.md` (2026-11-20). Ensure Apache License 2.0 is actually included in repository with required notices; commercial integration into proprietary paid FDFiles is permitted under the chosen license. No non-commercial/no-resale restriction; project distributing original software without charge is a business policy, not a change to Apache-2.0. Reference docs/legal/COMMERCIAL_USE_POLICY.md.

## Additional acceptance criteria

AC: LICENSE/NOTICE and source policy agree; legal review distinguishes code, base model, training data and finetuned weights.

## Compatibility and verification

Keep original TASK.md immutable and existing scope/acceptance requirements intact. This addition only clarifies product licensing, distribution and public messaging within the task's existing responsibility. Run focused checks at implementation time; no completed code, license clearance, model shipment, external deployment or tests are claimed by this event.
