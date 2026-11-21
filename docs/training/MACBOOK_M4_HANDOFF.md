# FDEC-087: owner-gated MacBook Air M4 handoff

Status: Stage A software implementation. Actual Apple execution, email training
and the completed real round trip have **not** been verified. Windows numerical
protocol tests do not establish those results. M4 / 32 GB MacBook Air is the
preferred temporary training host. The agent/chat cannot migrate automatically.

FDEC-101 adopted effective dependencies FDEC-019/FDEC-101. FDEC-016's original
CUDA criterion remains separately required by D003. All original FDEC-087
criteria, source rights and explicit owner transition remain mandatory.

## Runtime and data prerequisites

The exact 40 Mac wheels, hashes and local-install license review are in the
owning task's `evidence/mac-wheel-observations-v1.json` and
`local-mac-tooling-review-v1.md`. The lock is
`training/config/mlx-requirements-py314-macos15-arm64.txt`.
Require Apple Silicon, macOS 15+, CPython 3.14, 24 GiB RAM minimum, 12 GiB free
disk minimum, AC power and no detected thermal restriction. Plan for at least
20 GiB free storage including scratch space; this is not a measured duration.
PowerShell (`pwsh`) is required by existing FDTasks/data-rights verification.
No Torch/PEFT package is required on Mac.

MLX v1 supports unquantized LoRA only: fixed local Qwen3 revision, F32 base and
adapters, seven attention/MLP targets, AdamW. QLoRA rejects without fallback.
PyTorch remains the default. Full native checkpoints bind adapter, optimizer,
RNG, cursor and config/source/data/environment identities, using bounded
safetensors and a separate MLX HMAC domain. Renaming an adapter is not conversion.

Actual training requires independently reviewed non-OpenAI emails, labels and
training prompt, current source rights, signed consent, replay, PII checks and
verified grouped splits. Evaluation needs separate independently reviewed held-out
gold. The inference-only prompt is never used as training content. Neither
`codex-fixture-v1` nor `fdec-native-templates-v1` may enter actual training or
evaluation. A tooling license grants no corpus or public-weight rights. Missing
admitted inputs mean `insufficient_approved_data`.

## Stage A: primary workstation

Run local checks, inspect the diff, then commit the reviewed source:

```powershell
powershell -NoProfile -File training/finetune/test-mlx-handoff.ps1
powershell -NoProfile -File training/finetune/test-finetune.ps1
.venv/export/Scripts/python.exe training/finetune/train.py cpu-check --opt-in
```

The CPU check is numerical PEFT compatibility, not CUDA/Apple acceptance.
The portable source verifier checks HEAD, index, actual working bytes, hidden
index flags and additional source. Git-normalized blobs allow CRLF/LF portability.
This separate identity does not replace FDTasks' readiness/source-state algorithm.

Choose a new private directory outside every Git checkout. Do not overwrite an
existing store. These commands create a kit, not owner confirmation:

```powershell
$Python = '.venv/export/Scripts/python.exe'
$PrivateStore = Join-Path $env:LOCALAPPDATA 'FDEmailClassifier/private-FDEC-087-v1'
& $Python training/finetune/handoff_cli.py private-store --opt-in --output-dir $PrivateStore
& $Python training/finetune/handoff_cli.py prepare --opt-in --purpose numeric-smoke --config training/config/mlx-trainer-v1.json --output-dir (Join-Path $PrivateStore 'handoff')
& $Python training/finetune/handoff_cli.py inspect --handoff-dir (Join-Path $PrivateStore 'handoff')
```

The kit contains exact committed source history in a Git bundle, manifest,
receipt and private `.authority` key. The key authenticates integrity; it grants
neither owner nor dataset permission. Never upload the kit/key/weights/data to
public Git, release channels, container builds or chat.

Write an append-only pre-Mac task checkpoint: source/policy/readiness hashes,
task state, source cleanliness/preserved unrelated files, input/config/runtime
and kit identities, private artifact alias, pending command and restart predicate.
Numeric-only notice must explicitly state that actual email training is unavailable.
Use the TASK's full "Training is ready" notice only after actual inputs pass.

### Explicit owner transition

Stop before machine-specific execution and request the owner's explicit
confirmation as required by immutable FDEC-087 TASK.md. After an actual affirmative
reply, the authorized executor records it in append-only task evidence and creates
a protected external activation record. No approval/signer/transfer CLI exists.
Counterfactual test records never authorize real devices.

`FDEC_OWNER_CONFIRMATION_FILE` must point outside every Git checkout into the
protected store. It contains exactly:

```json
{
  "schema": "fdec-owner-transition/v1",
  "source_sha": "<exact source SHA from manifest>",
  "handoff_sha256": "<canonical manifest digest from inspect>",
  "scope": "numeric-smoke",
  "confirmation": "explicit-project-owner-device-transition",
  "confirmed_at": "<actual timestamp of explicit owner confirmation>"
}
```

This example is not approval. Do not populate it from silence, general development
or budget permission, or test success. It is an externally protected authority
anchor, not cryptographic proof of conversation; the executor must record genuine
authorization. Scope/source mismatch, future/invalid timestamps and owner-record
change/revocation reject further work. Actual training requires a separate admitted
`actual-training` kit and confirmation bound to that new digest. Never commit
activation records.

## Stage B: after confirmation, on Mac

Transfer the kit through an owner-authorized private local copy, encrypted store
or SSH channel. No endpoint/service is assumed or activated by the scripts.
Verify hashes and permissions at both ends. The POSIX protected root is mode 0700,
current-user owned, with macOS ACLs checked explicitly. Windows checks descendants
and allows only current user, SYSTEM and administrators. Protection only modifies
a newly created empty owned directory, never someone else's populated directory.

Clone `source.bundle` into a **new isolated** worktree, check out its exact SHA,
check Git status and inspect the handoff. Do not overwrite an active Mac worktree.
Ignored data/weights are absent from the Git bundle. Obtain trusted Python 3.14
and `pwsh` under the confirmed transition authority; verify them before proceeding.
Use owner-selected private paths:

```sh
export FDEC_OWNER_CONFIRMATION_FILE="$PRIVATE_STORE/owner-transition.json"
python3.14 training/finetune/handoff_cli.py inspect --handoff-dir "$PRIVATE_STORE/handoff"
pwsh -NoProfile -File Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/evidence/write-readiness-v2.ps1 -Name mac-readiness-unique.json
python3.14 training/scripts/bootstrap_mlx.py --opt-in --handoff-dir "$PRIVATE_STORE/handoff"
.venv/mlx/bin/python training/finetune/train.py mlx-check --opt-in --handoff-dir "$PRIVATE_STORE/handoff" --output-dir "$PRIVATE_STORE/mac-numeric-return"
```

Use a fresh readiness filename. Recompute FDTasks readiness on the real Mac rather
than treating a Windows source-state hash as a Mac measurement. Bootstrap checks
owner/hardware before installation, downloads exact audited tooling wheels and
installs offline with `--no-deps --require-hashes` into owned `.venv/mlx`.
It rejects foreign environments and downloads no stock tensors.

The real numerical smoke uses a tiny random Qwen3 and seeded token IDs, checks
adapter updates/frozen base and four uninterrupted steps against two steps plus
checkpoint/resume plus two steps, including optimizer/evolving RNG equality.
It creates a private native checkpoint, F32 PEFT export, runtime proof and signed
return receipt. No emails/labels are used. API or numerical failure must be
diagnosed, never converted into a PASS by removing a check.

### Actual training only after admission

On the primary host prepare a new kit with `--purpose actual-training`, config,
`--inventory`, `--consent`, `--split-dir`, `--annotations`, `--prompt` and
one `--source-run` per required ingestion run. All files must be private/current.
Existing `FDEC_CONSENT_KEY` authority is needed privately on both hosts; never
put it in commands/logs/evidence or transfer it automatically with the Git kit.
Re-confirm the new kit digest before Apple execution.

After the real Mac numerical smoke passes, use `train.py train --opt-in
--engine mlx --handoff-dir ... --config ... --inventory ... --consent ...
--split-dir ... --annotations ... --prompt ... --source-run ... --model-dir ...
--output-dir ...`. Model directory must be the exact audited local stock snapshot.
Use `--stop-after N`, then a **new output directory** with
`--resume <old-run/step-NNNNNNNNN>` to continue. Checkpoints are immutable.

Run `train.py mlx-evaluate --opt-in` with `--handoff-dir`, `--checkpoint`,
`--config`, `--inventory`, `--consent`, `--split-dir`,
`--training-annotations`, `--training-prompt`, held-out `--annotations`,
`--source-run`, `--model-dir` and a new `--output-dir`. It requires completed
training and admitted independent gold; it measures predictions/metrics and saves
a numeric bridge probe without logging emails/raw responses. Then run
`train.py mlx-collect --opt-in` with the same inputs, another new output directory
and `--evaluation-dir`. Collection is private; GGUF remains unverified.

## Stage C: verified return

Transfer only the authorized bundle privately. Preserve original kit/approval/data
and recoverable checkpoints. On the original host restore exact source, inspect
Git status, reactivate genuine owner authority and reconcile divergence explicitly.
Do not reset uncommitted work or force-push.

```powershell
& $Python training/finetune/handoff_cli.py verify-return --handoff-dir (Join-Path $PrivateStore 'handoff') --received-dir (Join-Path $PrivateStore 'received-return')
```

Numeric verification decodes authenticated native state without MLX/Torch, checks
PEFT tensor transposes, config, files, ACLs, source and owner. It always reports
`training_return_complete: false`, `return_notice: null`. It cannot close
actual training or FDEC-087.

Actual-training verification also requires `--export-dir`, `--llama-cpp-dir`,
`--config`, `--inventory`, `--consent`, `--split-dir`,
`--training-annotations`, `--training-prompt`, held-out `--annotations`,
`--source-run`, `--model-dir`. The original host needs audited FDEC-019
Torch/Transformers/PEFT/converter tooling, compiler and pinned clean llama.cpp.

The verifier re-admits current train/test rights, authenticates complete native
optimizer cursor/evaluation, compares exported PEFT tensors and actual CPU PEFT
logits against the Mac numeric probe, then builds/verifies all four private export
variants and actual llama.cpp base+LoRA versus merged GGUF loading. A structural
transpose alone is insufficient. Candidate includes exact artifact manifests,
measured evaluation, SBOM and durable `handoff-completion.json`.
This new bridge has **not** run on a real Mac-trained adapter. Cross-framework
tolerance and API compatibility remain to be demonstrated; failure means an
explicit incomplete export and no completion notice.

After real verification, append public-safe post-Mac task evidence with exact
source/config/policy, private artifact aliases/hashes, measured results, remaining
work and restart instruction. Only then deliver: "Training and artifact handoff
are complete. You can return to the original development workstation."
The program's verified notice is a predicate, not a replacement for task evidence.
No public-weight rights are granted: release policy stays default deny.

## Interruption

Preserve completed authenticated checkpoints. Re-admit current data/owner authority
before restarting. Hardware/data/authority failure leaves an explicit blocker and
restart predicate; continue independent dependency-ready work under the one-Epic
rule. Do not invent Apple execution, licensed corpus, calibrated probability,
119-language quality, completed training or completed transfer.
