---
schema: fdtasks-spec/v3
id: FDEC-087
title: "Apple Silicon MLX training with operator-gated development handoff"
type: Task
area: ai
component: apple-silicon-training-handoff
epic_id: FDEC-EPIC-D003
size: medium
initial_priority: P1
initial_status: Planned
initial_dependencies: [FDEC-016]
created_at: 2026-11-20T17:32:00Z
created_by: "project-owner-approved planning"
atomicity:
  outcomes: ["Provide a reproducible, operator-confirmed training round trip from the primary development environment to MacBook Air M4 and back, without losing source state or private training artifacts."]
  packets: ["Implement and verify one atomic source-to-Mac-and-return training workflow with MLX adapter, handoff checkpoints, and recovery controls."]
  independent_acceptance: false
  boundary_reason: "A source-to-Mac-to-source round trip has one end-to-end training/handoff contract; incomplete transition cannot be accepted without recoverable return and artifact verification."
---

# FDEC-087 — Apple Silicon MLX training and development handoff

## Goal

Use the project owner's **MacBook Air 15-inch (Apple M4, 32 GB unified RAM)** as the preferred execution host for actual Qwen3-0.6B LoRA training with Apple **MLX/MLX-LM**, rather than renting a GPU VPS or tying up the primary development stand. The Mac is a temporary **training host**, not a replacement for the normal development workstation.

Codex **must inform the owner when switching to the Mac becomes necessary**, stop before any machine-specific execution, and request the owner's explicit confirmation of the transition. After training finishes, artifact verification and checkpoint export must complete and Codex **must inform the owner that it is time to return** to the original development stand. Do not claim the agent or chat session can move automatically between devices: all continuation is via durable repository handoff and the owner's explicit device switch.

## Inputs and dependencies

- D002: only rights-approved training sources and frozen splits; source-rights audit is not bypassed by use of a different machine.
- FDEC-016: existing model training contract (PyTorch/PEFT as available); the Apple MLX backend is an additional compatible path, not a destructive replacement.
- Model/config contract and export compatibility in FDEC-019.
- Exact source commit and upstream FDTasks v5.6 policy SHA must be pinned at readiness, not guessed in advance.
- Owner's Mac hardware is known, but no assumption is made about installed Python/MLX, disk capacity, credentials, remote access or ability to run unattended.
- Handoff runbook: `docs/training/MACBOOK_M4_HANDOFF.md`.

## Scope and allowed paths

`training/finetune/`, `training/config/`, `training/scripts/`, `docs/training/` and immediately relevant local tests and verification evidence. Prefer extending the existing training pipeline with a backend selector (`mlx` or `pytorch`) and a portable manifest, rather than building a separate application. No changes to FDFiles or other repositories.

## Required round-trip workflow

**Stage A — Before the Mac is needed (primary development workstation)**

1. Keep ordinary development on the original workstation. Build and locally test the preprocessing/training adapter using synthetic software-only fixtures. For actual training, require a rights-approved dataset manifest, sufficient training data, fixed base-model/tokenizer revision, reproducible settings and training/validation split.
2. Only when actual device-dependent training is the next actionable step, emit a clear operator-facing message: **"Training is ready. Switch development to the MacBook Air M4."** Include the exact repository commit, task ID, required inputs, source-license status, estimated disk/RAM requirements and commands to resume. Do **not** promise an exact clock time in advance.
3. Write a durable **pre-Mac handoff checkpoint** under the owning task's immutable event/evidence contract containing source revision, environment and policy hashes, pending command, current task state, working-tree cleanliness, input manifest hashes, artifact destination and restart predicate. Stop before machine switching. Never commit tokens/private email/model weights in the handoff.

**Stage B — After the owner confirms the Mac is available**

4. Fetch/check out the exact pinned revision on Mac; check Apple Silicon architecture, compatible Python and MLX/MLX-LM, disk space, available unified memory, privacy/data permissions and power/thermal conditions; do not silently change or override an active workstation checkout.
5. Run a tiny synthetic-fixture MLX LoRA smoke test and save checkpoint/resume evidence. Then, if and only if approved sources exist and user has authorized the run, execute the actual training and evaluation on Mac (including checkpoints, metrics, failure/resume).
6. Keep outputs in local protected storage or authorized private encrypted artifact store. Do **not** push weights/adapters/raw training data to public GitHub, FDUpdate public channel, public Docker builds or chat. Store hash, model revision, dataset manifest, training seed/params, timings, metrics and export compatibility metadata.
7. If a trained checkpoint is not technically or legally ready for Rust inference/GGUF export, explicitly report the conversion or rights blocker; keep the checkpoint private, and do not fabricate a completed export.

**Stage C — Return to the original development workstation**

8. At completed training, securely transfer/retrieve **only the authorized artifacts needed for continuing development**, by documented private transfer/SSH/encrypted storage (not public git). Verify SHA-256 identities and access permissions on both ends. If transfer/export cannot complete, mark transfer incomplete and do not tell the owner the handoff is complete.
9. Write a durable **post-Mac completion checkpoint** (exact code/config revisions, private artifact references/hashes, test/benchmark results, unfinished work and next instruction). Only then send a clear operator-facing message: **"Training and artifact handoff are complete. You can return to the original development workstation."**
10. On the original workstation, reload the exact checkpoint, check git status and artifact checksums, resume outstanding normal development without recreating work. If source versions diverged, reconcile without force pushing or silently discarding changes.

**Failure mode:** If Mac is unavailable or training is interrupted, preserve state/checkpoints, report the blocker and resume non-dependent tasks on the original development workstation. Do not hold unrelated development hostage to Apple hardware access.

## Non-goals

No automatic remote desktop control, no autonomous physical device switching, no forced server purchase, no purchase of datasets, no model weights publication, no pretense of a GPU training success based on software-only tests, no weakening rights/PII checks, no changes to closed historical tasks.

## Security, compatibility and recovery

The repo is public; raw email, training corpus, adapters and checkpoints default to non-public. Credentials and machine identifiers never enter task evidence. MLX and PyTorch pathways must retain schema/model version compatibility and provide explicit unsupported-backend error/fallback. Recoverable checkpoints must not overwrite each other or be erased before post-handoff checksum verification.

## Readiness and AC-to-local-test matrix

Risk: medium for environment portability; high for loss/leakage of model/data. Exact tool versions and commands are pinned at task readiness and captured from the implemented setup. Hosted GitHub Actions remain manual build/package only; real training, acceptance and full gate run locally.

| AC ID | Observable criterion | Test level / scenario | Trusted steps / command | Environment | Expected |
| --- | --- | --- | --- | --- | --- |
| AC-01 | MLX training backend has reproducible configuration with checkpoint resume and does not break existing backend selection | Local functional | Run implemented MLX-LM tiny-fixture smoke/resume commands, capture exact commands and metadata | MacBook M4 or valid Apple Silicon environment | LoRA smoke/resume PASS or explicit hardware-unavailable blocker; no invented result |
| AC-02 | Codex gives pre-switch notice and writes exact handoff before training | Handoff simulation | Run documented Stage A dry-run; inspect checkpoint and operator message | Primary workstation | No switch without owner confirmation; source/license/runtime inputs listed |
| AC-03 | Rights or missing Mac conditions cannot launch real training | Negative boundary | Run absent dataset license, missing MLX and unapproved-owner fixtures | Local synthetic fixtures | Fail closed and retain recoverable workstation state |
| AC-04 | Post-training notice occurs only after protected artifacts, hashes, metrics and resume checkpoint are verified | End-to-end handoff | Run synthetic round-trip simulation, verify checksums and restart instructions; perform actual Mac run when authorized and available | Mac and original workstation | Exact clean return; no public leakage, no false completed notice |
| AC-05 | GPU VPS and PyTorch are not prerequisites to executing approved Mac training | Contract/portability | Inspect backend configuration, run local backend-selection tests | Local checkout | MLX selectable, PyTorch retained, clear missing-backend errors |

## Completion evidence

Record exact source SHA/policy SHA, Mac host hardware class (without serial), MLX/Python versions, local command results, input manifest, artifact hashes and both handoff confirmations. Do not close the task on an unperformed real training run if the adopted acceptance requires that evidence; record a bounded external wait and continue unrelated work instead.
