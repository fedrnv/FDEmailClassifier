---
schema: fdtasks-event/v3
event_id: EVT-20261120T171505Z-FDEC-POLICY-053
task_id: FDEC-053
event_type: scope-amended
created_at: 2026-11-20T17:15:05Z
actor: "project-owner-requested policy alignment"
base_revision: "977ce837182d612691d5649c80f0aac5ea74c614"
server_revision: null
---

# Align accepted delivery criteria with free OSS and commercial integration policy

## Payload

Approved product rule: see `docs/legal/COMMERCIAL_USE_POLICY.md` and `docs/PRODUCT_DESCRIPTION.md` (2026-11-20). GitHub Releases/packages/containers distribute Apache-2.0-cleared OSS assets free of charge. Do not package unapproved datasets or model weights inside Docker or binaries. Preserve third-party notices and clear free/commercial usage wording.

## Additional acceptance criteria

AC: artifact manifest/NOTICE and release description distinguish code license from separately gated weights and permit use by commercial FDFiles.

## Compatibility and verification

Keep original TASK.md immutable and existing scope/acceptance requirements intact. This addition only clarifies product licensing, distribution and public messaging within the task's existing responsibility. Run focused checks at implementation time; no completed code, license clearance, model shipment, external deployment or tests are claimed by this event.
