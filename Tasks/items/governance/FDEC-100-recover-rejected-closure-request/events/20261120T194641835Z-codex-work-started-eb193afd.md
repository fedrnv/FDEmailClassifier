---
schema: fdtasks-event/v3
event_id: eb193afd-3fd7-4974-9e39-c886c4b225f8
task_id: FDEC-100
event_type: work-started
created_at: 2026-11-20T19:46:41.835Z
actor: codex
base_revision: "af394b8684a7705c74030491d089333175f9a216"
server_revision: null
---

## Payload
Planned -> InProgress. Bounded S001 bootstrap is documented in evidence/bootstrap-readiness-v1.json because normal strict validation rejects the malformed immutable FDEC-099 request; the error is independently reproduced before implementation. Execute only the explicit append-only rejected-request recovery boundary and its direct tests. No normal admission or verified closure is claimed until the repaired validator and unchanged admission pass. Preserve original request bytes/identity, all source-rights guards and existing policy baseline.
