---
schema: fdtasks-event/v3
event_id: EVT-20261120T173201Z-FDEC-020-DEP-087
task_id: FDEC-020
event_type: dependency-added
created_at: 2026-11-20T17:32:01Z
actor: "project-owner-approved planning"
base_revision: "57da47a419e3031974121518410250483d0dd625"
server_revision: null
---

# Include Mac training workflow in D003 integration gate

## Payload
Add `FDEC-087` as a prerequisite for `FDEC-020`. The local targeted gate must verify MLX backend selection, operator confirmation, private artifact integrity/transfer and return to the primary dev workstation. Existing FDEC-015..FDEC-019 dependencies remain unchanged. Gate/review can use synthetic/permissioned fixtures for simulation, but cannot claim a completed real training run without actual evidence.

## Verification
No tests or completed training claimed.
