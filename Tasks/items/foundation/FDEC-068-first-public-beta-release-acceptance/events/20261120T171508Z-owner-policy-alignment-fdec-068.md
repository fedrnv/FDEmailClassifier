---
schema: fdtasks-event/v3
event_id: EVT-20261120T171508Z-FDEC-POLICY-068
task_id: FDEC-068
event_type: scope-amended
created_at: 2026-11-20T17:15:08Z
actor: "project-owner-requested policy alignment"
base_revision: "977ce837182d612691d5649c80f0aac5ea74c614"
server_revision: null
---

# Align accepted delivery criteria with free OSS and commercial integration policy

## Payload

Approved product rule: see `docs/legal/COMMERCIAL_USE_POLICY.md` and `docs/PRODUCT_DESCRIPTION.md` (2026-11-20). Final public beta acceptance must confirm license file, disclosures, ability to use licensed code inside paid FDFiles, zero required standalone subscription, no misleading free-weight claims, and protected rights/PII release gates.

## Additional acceptance criteria

AC: public README/site/release descriptions agree on free OSS & commercial integration; trained weights shipped only with verified redistribution permission.

## Compatibility and verification

Keep original TASK.md immutable and existing scope/acceptance requirements intact. This addition only clarifies product licensing, distribution and public messaging within the task's existing responsibility. Run focused checks at implementation time; no completed code, license clearance, model shipment, external deployment or tests are claimed by this event.
