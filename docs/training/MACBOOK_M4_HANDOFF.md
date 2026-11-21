# Operator-gated training handoff: MacBook Air M4

Status: approved workflow, **not an executed training run**. Owner's Apple M4 / 32 GB MacBook Air is the preferred temporary Qwen3-0.6B LoRA/MLX host.

FDEC-101 records the append-only correction of the original FDEC-087 dependency:
MLX preparation follows verified export FDEC-019 and the verified process
Correction itself. CUDA/PyTorch acceptance FDEC-016 remains independently required
by the D003 gate; a CPU or MLX smoke test cannot close it. This reconciliation
does not authorize a Mac switch, actual email training or model publication.

## Development → MacBook

1. Develop and validate training code on the normal development workstation as far as possible without the Mac.
2. When the **next dependency-ready task really requires GPU/Apple MLX training**, Codex must tell the owner that a device switch is required, not impose a guessed calendar date.
3. In the notification provide: task ID and source commit; what is finished; rights-approved dataset manifest (or explicit `insufficient_approved_data` blocker); model/config revisions; prerequisites; expected storage use; exact resume command; clean Git checkpoint.
4. Operator explicitly confirms switching to the Mac. Never imply Codex can physically/automatically transfer execution to a different computer.
5. On the Mac: obtain exact source revision, install/check pinned MLX-LM dependencies, run a tiny synthetic test, and only then run licensed training. Use normal power supply, monitor thermal throttling, and preserve recoverable private checkpoints. Record exact environment and results.

## MacBook → development stand

6. Export compatible private model artifacts/checkpoints and metrics, record SHA-256, base model/tokenizer IDs, data rights provenance, training settings, benchmark results and version compatibility.
7. Transfer only via approved private encrypted storage/SSH or direct local copy. Never commit checkpoint/LoRA/weights/raw training data to public GitHub or FDUpdate.
8. Verify artifacts at destination and record a durable post-training FDTasks handoff. If failed, report incomplete transfer and remain in recoverable state.
9. Codex tells the operator **training is complete and it is time to return to the development stand**. The operator switches devices.
10. Resume from the exact original task/checkpoint/commit; reconcile source changes without force pushing or overwriting uncommitted work.

## Failure and no-blocking rule

If the Mac or approved training data is not available at handoff time, stop this training-dependent task with an explicit reason, checkpoint and restart condition. Continue other dependency-ready development work on the original stand. No claims of training, accuracy, license clearance or artifact release without evidence. The Mac is a *temporary training worker*, not the canonical code/source host.
