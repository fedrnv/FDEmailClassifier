---
schema: fdtasks-event/v3
event_id: 7c133fce-d340-4c6c-9184-b2a6057e826b
task_id: FDEC-087
event_type: status-changed
created_at: 2026-11-21T01:57:52.213Z
actor: codex
base_revision: "6e6a9eef5cf1fb145db7246e1c83ac310fe2905e"
server_revision: null
---

InProgress -> Blocked. Stage A software and a protected numeric-only Mac kit are
concrete and locally verified. See evidence/software-verification-v1.json,
evidence/software-test-output-v1.txt, evidence/readiness-v2.json and
evidence/pre-mac-checkpoint-v1.json. Thirteen handoff checks, fourteen existing
trainer checks and an actual numerical CPU PEFT resume passed; none is Apple
acceptance or actual email training. Repository validation passed for 115 records.

The original owner-confirmed Apple step is the next device-dependent action.
No actual owner confirmation, Mac access/execution, real training/evaluation or
completed artifact round trip exists. The protected kit is bound to source
6e6a9eef5cf1fb145db7246e1c83ac310fe2905e and canonical handoff SHA-256
fd10c30d531a09aed3037df1aee5556c22457947dd0330ffc63a9ba4af6b2e76.
No authority key, owner activation, weights or email data is in Git. The production
mlx-check against this actual frozen kit rejected explicit_owner_transition_missing
before hardware/output creation. Actual-training prepare without independent
inputs rejected insufficient_approved_data and created no output.

Restart only after genuine owner confirmation of the numeric-smoke transition,
authorized private transfer and compatible Apple host preflight, exact source and
latest immutable task state with fresh FDTasks readiness/resume event. Follow
docs/training/MACBOOK_M4_HANDOFF.md. The activation example is not permission;
do not generate owner approval from silence or general development authority.
Actual email training additionally requires a separate admitted-data kit, current
signed consent, independent training labels/prompt/held-out gold and bound owner
confirmation. Do not announce full training completion on a numerical return.

FDEC-087 remains incomplete, with no closure/version request. Preserve the separate
FDEC-015 independent multilingual baseline and FDEC-016 original CUDA obligations;
do not skip them or prematurely run the D003 gate/review. This event is a bounded
task handoff, not completion or suspension of the overall development goal.
