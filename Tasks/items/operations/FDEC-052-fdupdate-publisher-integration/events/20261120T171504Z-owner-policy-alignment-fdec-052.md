---
schema: fdtasks-event/v3
event_id: EVT-20261120T171504Z-FDEC-POLICY-052
task_id: FDEC-052
event_type: scope-amended
created_at: 2026-11-20T17:15:04Z
actor: "project-owner-requested policy alignment"
base_revision: "977ce837182d612691d5649c80f0aac5ea74c614"
server_revision: null
---

# Align accepted delivery criteria with free OSS and commercial integration policy

## Payload

Approved product rule: see `docs/legal/COMMERCIAL_USE_POLICY.md` and `docs/PRODUCT_DESCRIPTION.md` (2026-11-20). Public FDUpdate channel must allow free release of licensed binaries/libraries, while trained weights are uploaded only after a separate reviewed license/provenance gate. Commercial embedding in FDFiles is a supported consumer scenario; no mandatory license-key payment or activation.

## Additional acceptance criteria

AC: dry-run with cleared code succeeds, uncleared model artifact is rejected, public channel metadata and docs express free/commercial-allowed use.

## Compatibility and verification

Keep original TASK.md immutable and existing scope/acceptance requirements intact. This addition only clarifies product licensing, distribution and public messaging within the task's existing responsibility. Run focused checks at implementation time; no completed code, license clearance, model shipment, external deployment or tests are claimed by this event.
