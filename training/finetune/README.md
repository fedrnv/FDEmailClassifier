# Deterministic private PyTorch/PEFT trainer (FDEC-016)

This implements the local trainer contract. It has not passed the required
supported-GPU acceptance run. The current workstation exposes only Microsoft
Basic Display Adapter; a compatible CUDA runtime/device is not confirmed. Actual
CUDA/QLoRA integration and GPU numerical reproducibility remain unverified.
The installed, audited export-only runtime additionally supports the complete
numerical CPU LoRA check below; it is not an actual-training CPU fallback.
Software checks, protocol doubles and signed counterfactual dataset policies are
not evidence of actual email training or GPU acceptance. FDEC-016 stays incomplete
until the accepted GPU checkpoint/resume criterion actually passes.

```powershell
powershell -NoProfile -File training/finetune/test-finetune.ps1
.venv/ingestion/Scripts/python.exe training/finetune/train.py preflight
```

These commands do not install a transformer runtime or train a model. The tests
exercise the real existing rights, ingestion replay and grouped-split verifiers
on isolated software fixtures. No actual language model consumes their generated
email content or labels. Numerical checkpoint/orchestration doubles do not call
PyTorch; the actual checkpoint codec and engine have a separate numerical CPU
check and the original mandatory supported-GPU acceptance check.

## Additional numerical CPU checkpoint check

```powershell
.venv/export/Scripts/python.exe training/finetune/train.py cpu-check --opt-in
```

Use the exact locally audited runtime prepared by
`python training/export/bootstrap.py --opt-in --model-check`. No additional
package installation or pretrained tensor download occurs in the check.
It initializes a tiny random Qwen3, creates a real PEFT LoRA adapter and performs
four gradient updates on seeded random numeric tokens. Real engine update,
AdamW, adapter/optimizer/RNG state, authenticated checkpoint serialization and
restricted PyTorch load are exercised. Uninterrupted state must match a
two-step interruption plus restored two-step continuation exactly. The adapter
must actually change and every frozen base tensor must stay unchanged.
Existing checkpoint overwrite must fail without changing its bytes, and native
state corruption must reject before invoking the decoder. Only scalar booleans,
counts and static diagnostics are printed; temporary numerical weights/state
are removed through guarded owned temporary directories. No email, classification
gold, stock weights or actual commercial training is involved.

The result explicitly reports `supported_gpu_acceptance: false`. This command
permits only numerical LoRA; it cannot enable QLoRA on CPU. The actual `train`
command has no CPU/technical override and still requires its original compatible
single bfloat16 CUDA device plus all current private data/rights checks. The
production engine derives tensor placement from its loaded parameters and only
captures/restores CUDA RNG for CUDA models. Actual model initialization remains
CUDA-only. CPU fixture results never close the original supported-GPU criterion.

## Actual training admission

`train` requires opt-in, a private approved inventory, current signed consent,
verified grouped split and every required independent source ingestion run. The
same origin/license checks remain mandatory, including both commercial-training
and evaluation grants used by the existing split policy. Neither Codex fixture
pack is admitted. No CLI policy-root override, fixture promotion or automatic
source approval exists. Source bytes, normalized text and original annotations
are replayed before joining canonical reviewed training labels. Only the exact
train partition can be used; validation/test rows cannot be targets.

The private annotation file has schema `fdec-training-annotations/v1` and `rows`.
Each row follows the existing classification-v1 contract with `record_id`,
`language`, `classification` and six boolean mask fields (`topics`, `priority`,
`spam`, `phishing`, `malware`, `action`). This first whole-JSON SFT objective
requires every head to be independently reviewed, known and masked true. Partial
annotations fail explicitly rather than being filled, dropped or turned into
false negative targets. A fallback `review` action is not automatically gold.
Partial-head objectives require a separately verified extension; this limitation
does not change the earlier canonical mapper or authorize source-label promotion.

The independent training prompt is a private JSON file with schema
`fdec-independent-training-prompt/v1`, `system` and `origin` equal to
`independently-reviewed-non-openai`. No natural-language training prompt, email
template or gold label is shipped by this trainer. The baseline's Codex-written
inference prompt is not used as training content. Canonical serialization and the
publisher's tokenizer format are transformations of the independently reviewed
inputs, not new semantic annotations. Prompt/user token losses are masked -100;
only the fully reviewed assistant JSON completion and EOS are supervised.
The tokenizer receives `enable_thinking=False`; sequence limits reject rather
than truncate or silently discard examples. Input and target token sequences
are concatenated explicitly at the assistant boundary, avoiding a required BPE
prefix match between separately rendered full conversations.

The protected operator anchor is `training/data/training-review/current.json`,
schema `fdec-signed-training-review/v1`, containing `payload` and `hmac_sha256`.
Payload schema `fdec-training-label-review/v1` binds canonical inventory, signed
consent and split-receipt SHA-256, exact annotation and prompt file SHA-256,
`reviewer_kind` = `independently-reviewed-non-openai`, independent evidence
SHA-256, `issued_at`, `valid_until` (UTC seconds). HMAC-SHA256 covers UTF-8
`fdec-training-label-review/v1` + NUL + canonical payload JSON, using the existing
protected 32-byte consent key. Provision it through the existing private authority
process, never via a command argument or Git. No automatic signing command is
provided. An operator signature is a trust-boundary attestation, not proof of
real-world authorship, rights or label truth; retain the actual independent
review evidence privately. A file merely asserting an origin is insufficient.

## Execution and resume

The runtime profile pins observed candidate top-level package versions; it is
not a wheel lock, interoperability claim or distribution approval. Actual runs
need an audited compatible environment and the pinned local stock snapshot from
`training/baseline/qwen-stock-v1.json`. No automatic pip/model download, remote
code or hosted execution occurs. See `RUNTIME-AUDIT.md`.

```powershell
python training/finetune/train.py train --opt-in `
  --config training/config/peft-trainer-v1.json `
  --inventory training/data/approved/inventory.json `
  --consent training/data/approved/consent.json `
  --split-dir training/outputs/approved-split `
  --annotations training/data/approved/training-gold.json `
  --prompt training/data/approved/independent-training-prompt.json `
  --source-run training/data/approved/source-1 `
  --source-run training/data/approved/source-2 `
  --source-run training/data/approved/source-3 `
  --model-dir models/downloads/qwen-stock-v1 `
  --output-dir training/outputs/train-run-001 --stop-after 20
```

Run with the prepared interpreter. `--stop-after` checkpoints an intentional
interruption; it does not change the configured final step count. Resume with
the same input arguments/config, a fresh output directory and
`--resume training/outputs/train-run-001/step-000000020`. Config, model, runtime
fingerprint, implementation, input, review or authority changes reject resume.
There is no in-place overwrite or silent fresh-start fallback.

The CUDA engine uses one visible bf16-capable device, eager attention, float32
LoRA adapters, zero LoRA dropout, AdamW without fused/foreach kernels, deterministic
algorithm enforcement, fixed seeds, no TF32, batch size one and configured gradient
accumulation/clipping. `CUDA_VISIBLE_DEVICES` can select one existing device before
starting the process; no device is rented or provisioned by this software.
QLoRA additionally requests NF4/double quantization and prepares the frozen base
for k-bit training. Unsupported deterministic kernels fail; QLoRA reproducibility
must be measured separately on its target device. No accuracy claim is inferred.

The pure seeded epoch order is reconstructed from global optimizer step and
accumulation count. Checkpoints contain only trainable adapter tensors, exact
parameter order, optimizer state, CPU/CUDA RNG and bound metadata; no email,
token sequences, prompt text or raw responses are persisted. Checkpoint tensors
can still encode training information: they stay private and ignored by Git.
The HMAC-authenticated receipt is written last. State bytes and context are
authenticated and frozen before restricted `torch.load(weights_only=True)`;
no unrestricted pickle load or extra globals are allowed. Size is bounded to
512 MB. Existing checkpoints are never overwritten. Failure removes only the
new owned incomplete checkpoint; earlier committed checkpoints remain recoverable.
The run result is staged, flushed and atomically renamed only after the requested
steps and final authority check. Failed final publication leaves no completed
result and preserves the committed checkpoint for recovery.

Current rights/consent/review are checked before use, optimizer mutation and
checkpoint publication; source/split/label bytes are replayed again at checkpoints.
This is a point-in-time authority check, not a future-consent guarantee. Logs and
CLI errors contain static status/step counts, never input paths, emails, targets,
keys or third-party diagnostics. There is no public model export or release step.

## Required GPU acceptance

On an already authorized compatible host with the prepared runtime:

```powershell
python training/finetune/train.py gpu-check --opt-in
```

This constructs a disposable, tiny randomly initialized Qwen3 with PEFT LoRA,
uses seeded random numerical token IDs, and compares uninterrupted four-step
state against a two-step checkpoint plus resume for both LoRA and QLoRA by default.
`--backend lora` or `--backend qlora` can isolate one path; a single-path result
does not prove both. QLoRA creates a disposable private random base snapshot for
local 4-bit loading; no publisher tensors are downloaded. It checks adapter parameters,
optimizer and RNG byte equality using the actual PyTorch codec. No stock tensors,
natural-language training texts, email fixtures or category annotations are used.
Successful numerical technical-fixture acceptance is not real dataset training,
model quality evidence or permission to distribute the disposable fixture model.
Both target-host paths still require actual deterministic runs.

No paid VPS is needed for software development. A supported GPU is needed for
the remaining acceptance run. The owner's preferred Mac/MLX handoff remains
FDEC-087 with its own dependencies and explicit operator-confirmed transition;
this task does not perform or pre-authorize that switch. Do not weaken either
task's acceptance or request a device switch before it is dependency-ready.
