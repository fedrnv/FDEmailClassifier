---
schema: fdtasks-event/v3
event_id: EVT-20261120T171506Z-FDEC-POLICY-074-reidentified-FDEC-089
task_id: FDEC-089
event_type: scope-amended
created_at: 2026-11-20T17:15:06Z
actor: "project-owner-requested policy alignment"
base_revision: "977ce837182d612691d5649c80f0aac5ea74c614"
server_revision: null
---

# Align accepted delivery criteria with free OSS and commercial integration policy

## Payload

Approved product rule: see `docs/legal/COMMERCIAL_USE_POLICY.md` and `docs/PRODUCT_DESCRIPTION.md` (2026-11-20). Per-source admission must check training for commercial use, SaaS inference inside paid FDFiles, and redistribution of trained weights as separate rights. Optional sources lacking evidence are excluded; Codex-generated content is technical fixture only absent explicit provider-rights approval.

## Additional acceptance criteria

AC: manifests block source lacking any required purpose, while permitted independent software work remains ready; no rights are inferred from metadata alone.

## Compatibility and verification

Keep original TASK.md immutable and existing scope/acceptance requirements intact. This addition only clarifies product licensing, distribution and public messaging within the task's existing responsibility. Run focused checks at implementation time; no completed code, license clearance, model shipment, external deployment or tests are claimed by this event.
