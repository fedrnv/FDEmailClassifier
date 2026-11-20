---
schema: fdtasks-event/v3
event_id: EVT-20261120T171502Z-FDEC-POLICY-072
task_id: FDEC-072
event_type: scope-amended
created_at: 2026-11-20T17:15:02Z
actor: "project-owner-requested policy alignment"
base_revision: "977ce837182d612691d5649c80f0aac5ea74c614"
server_revision: null
---

# Align accepted delivery criteria with free OSS and commercial integration policy

## Payload

Approved product rule: see `docs/legal/COMMERCIAL_USE_POLICY.md` and `docs/PRODUCT_DESCRIPTION.md` (2026-11-20). Use docs/PRODUCT_DESCRIPTION.md as authoritative public copy: free open-source, designed for commercial usage including in paid FDFiles; describe current planned status accurately; add usage/rights links. Align GitHub About metadata when authorized GitHub settings support writing.

## Additional acceptance criteria

AC: README, GitHub About and topics do not claim the model or 119-language accuracy has shipped; commercial use visibly permitted.

## Compatibility and verification

Keep original TASK.md immutable and existing scope/acceptance requirements intact. This addition only clarifies product licensing, distribution and public messaging within the task's existing responsibility. Run focused checks at implementation time; no completed code, license clearance, model shipment, external deployment or tests are claimed by this event.
