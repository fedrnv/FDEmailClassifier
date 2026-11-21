---
schema: fdtasks-event/v3
event_id: b3956b25-c510-4c24-bd9a-a3bbed7539b7
task_id: FDEC-087
event_type: status-changed
created_at: 2026-11-21T06:12:42.781Z
actor: codex-recording-explicit-project-owner-instruction
base_revision: "0f780f856c937b5b38a7a87a34f8be9d781c8faf"
server_revision: null
---

Blocked -> Blocked. Owner transition authority is now supplied; actual Mac host
availability and private kit transfer remain to be verified on that host.

The owner explicitly instructed the executor to push all changes needed for Mac
continuation and stated that they are switching to the Mac. This answers the
pending numeric MLX smoke transition request. The timestamp records authorization
in this execution turn, not a guessed exact timestamp of the owner's message.

Bind confirmation to source 6e6a9eef5cf1fb145db7246e1c83ac310fe2905e,
numeric-smoke scope and canonical handoff SHA-256
fd10c30d531a09aed3037df1aee5556c22457947dd0330ffc63a9ba4af6b2e76.
The genuine protected external owner-transition.json was created and successfully
verified against the existing kit. It is not fixture approval or data consent.

Public source/task publication to origin/main is explicitly authorized. Private
authority, activation, datasets, credentials and weights remain outside Git. The
owner must carry the private store through their private channel; no endpoint or
successful transfer is assumed. See evidence/mac-continuation-v1.md.

Resume only after Mac environment/private-input verification and fresh FDTasks
readiness. No Mac execution, install, training, transfer, export or round-trip
success is claimed. Actual email training additionally requires independently
admitted non-OpenAI data/labels/prompt/gold, current consent and a separately bound
kit. No closure/version request is created.

Publication validation initially rejected an unaccepted draft using the unsupported
owner-transition-confirmed event type. Its bytes were preserved in the ignored
local journal; this supported status-changed record replaces that rejected draft
before any commit/publication. No accepted history or validator rule was modified.
