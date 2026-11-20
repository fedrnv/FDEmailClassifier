---
schema: fdtasks-event/v3
event_id: cc080058-da59-48a1-946d-1e22060d1fbc
task_id: FDEC-012
event_type: dependency-added
created_at: 2026-11-20T16:00:53.298Z
actor: codex
base_revision: "09d3a581ce338c9f1d3acfa257f3cfd88cbc8651"
server_revision: null
---

## Payload
Add FDEC-009 as direct dependency: split inventories bind verified ingestion provenance and use its audited source-admission and private-output helpers. This item is independent of blocked FDEC-011; no unapproved augmentation material is admitted. The previous task's durable checkpoint preserves its unresolved source-rights state.
