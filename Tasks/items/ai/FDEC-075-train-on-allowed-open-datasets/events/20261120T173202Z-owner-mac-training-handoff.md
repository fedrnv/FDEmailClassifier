---
schema: fdtasks-event/v3
event_id: EVT-20261120T173202Z-FDEC-075-MAC-EXECUTION
task_id: FDEC-075
event_type: scope-amended
created_at: 2026-11-20T17:32:02Z
actor: "project-owner-approved planning"
base_revision: "57da47a419e3031974121518410250483d0dd625"
server_revision: null
---

# Preferred execution host for approved-dataset training

## Payload
When FDEC-075 reaches an **actual training** run, prefer the MacBook Air Apple M4/32 GB MLX path of FDEC-087 rather than a non-GPU Linux VPS. Before handoff, Codex must notify the project owner to switch from normal development stand to Mac and record checkpoint. After completion, verified private export, transfer and post-Mac checkpoint, Codex must notify owner to return. This is a platform choice, not a new blanket dependency on Mac availability for source audit/config/code work.

Model/data rights admission remains independent and mandatory; no publication of weights until separately cleared. Python/PyTorch path remains a fallback where supported. See `docs/training/MACBOOK_M4_HANDOFF.md`.

## Additional acceptance evidence
Evidence for any actual training run identifies the machine class, MLX/runtime versions, source/data manifests, checkpoint/transfer SHA-256 and both operator notifications. If hardware unavailable, create blocker on training-dependent step and continue unrelated ready work.

## Verification
Planning only; no hardware validation or training execution claimed.
