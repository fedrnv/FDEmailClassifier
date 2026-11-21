# FDEC-016 resumed partial verification

Source commit: `aed8be3068711f039d10d487db51ebab7a52a158`.
Source state: `e83fb7d70c6f1ea0aec3322b7c5d674af2bbbb287abd6e451d0ba23e194bae56`.
FDTasks 5.6 policy: `ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403`.
Execute admission passed before implementation and again at the frozen commit,
in `resumed-readiness-v1.json` and `frozen-resumed-readiness-v1.json`.
The original task, GPU criterion, dependencies and source-rights policy are
unchanged. This is additional partial evidence, not closure or scope amendment.

| Original criterion | Actual evidence | Status |
| --- | --- | --- |
| AC-01: actual tiny synthetic training/checkpoint resume on supported GPU | Complete real numerical CPU LoRA update, native checkpoint and exact replay now pass; GPU LoRA attempt rejects, and QLoRA is not installed/tested | NOT FULFILLED |
| AC-02: invalid/missing input preserves prior state and prevents unsafe publication | 14 software tests plus actual native CPU checkpoint overwrite preservation and tamper rejection before decoder | SOFTWARE/CPU PASS; GPU failure paths remain unverified |

Final software command: `powershell -NoProfile -File training/finetune/test-finetune.ps1`.
Monitor `3cc001cc-eb78-463e-8d08-0ecbcd5841f9`, exit 0: 14 tests in 53.447
seconds, full output `test-output-v2.txt`. The suite explicitly reports GPU
acceptance NOT_RUN and no actual email training. The new negative test establishes
that numerical CPU mode cannot enable the actual trainer without its original
single bfloat16 CUDA device. `train --technical-cpu` is not a supported argument;
the CPU check requires its own opt-in and refuses the QLoRA backend.

Final native CPU command:
`.venv/export/Scripts/python.exe training/finetune/train.py cpu-check --opt-in`.
Monitor `f5987151-14be-49d9-b8cc-1a61f27ec0eb`, exit 0; full output preserved
as `cpu-check-v1.json`. Tiny random Qwen3, numerical random token IDs, LoRA rank 2,
four genuine gradient updates; no stock tensors, natural-language email content
or category gold. Production engine update, AdamW, gradient clipping, native
`torch.save` and authenticated restricted `torch.load(weights_only=True)` run.
Uninterrupted four-step adapter/optimizer/RNG state equals the two-step checkpoint
plus restored two-step continuation exactly. At least one adapter tensor changes
and every frozen base tensor stays unchanged. Attempting to write the existing
checkpoint fails and preserves its state/metadata/receipt bytes. Corrupting native
state afterward rejects before the numerical decoder is called.

Production initialization remains CUDA-only: existing data/license/consent/split,
independent annotation/prompt, stock-snapshot and protected checkpoint admission
remain mandatory. The technical fixture creates a tiny model directly rather
than admitting fixture emails through actual `train`. Tensor placement now follows
the engine's actual parameter device. CUDA synchronization/RNG are used only for
CUDA model state; CPU state cannot restore a nonempty CUDA RNG list. No CLI input
can select CPU for actual email training. Fixture checkpoint context is explicitly
technical and cannot impersonate an admitted actual training context.

Final original GPU command attempted:
`.venv/export/Scripts/python.exe training/finetune/train.py gpu-check --opt-in --backend lora`.
Monitor `e8f4398c-11bd-4fa1-95c6-e0fd6baa612a`, exit 2, static diagnostic
`trainer_execution_rejected`; full output `gpu-attempt-v2.txt`. This is a failed
availability/admission attempt, not a successful GPU check. It does not prove
QLoRA compatibility, resumed GPU equality or GPU failure/recovery correctness.

The exact installed-runtime observation command is
`.venv/export/Scripts/python.exe Tasks/items/ai/FDEC-016-lora-qlora-trainer/evidence/observe-local-runtime-v2.py`.
Monitor `00798ba4-828b-4ce9-ace0-7b222b9d7c6a`, exit 0; full observation
`local-runtime-v2.json`. CPython 3.14.5, Torch 2.15.0, Transformers 5.23.0,
PEFT 0.22.0, safetensors 0.8.0 and NumPy 2.5.5 match the pinned LoRA profile.
`cuda_available` is false, device count 0, and Torch CUDA build is null.
The production runtime gate explicitly rejects with
`single_bfloat16_cuda_device_required`. Unlike the original attempt, missing
LoRA Python packages are no longer the immediate obstacle. FDEC-019's immutable
wheel observations/reviews establish local tooling use, not runtime or model
distribution rights. bitsandbytes/CUDA wheels require their own supported-host
audit before the GPU paths can run.

Exploratory evidence: the first native CPU replay passed, then the added existing
checkpoint preservation scenario exposed the expected `IngestionError` from the
shared private-output guard, which the new check initially did not catch. The
diagnostic run `1eac8137-02c4-4868-8c64-58e16b2d4feb` exited 1. The check was
corrected to recognize that explicit guard rejection while still checking every
existing byte. No production ownership/licensing guard changed. The complete
CPU check then passed before freeze and again in the final run above. No failed
attempt is relabeled as a passed test.

## Remaining external requirement and continuation

FDEC-016 remains incomplete on its original supported-GPU LoRA/QLoRA acceptance.
A CPU-only VPS cannot establish that criterion. Existing Linux VPS authorization
does not identify a supported GPU, connection or audited CUDA runtime; a concise
hardware/access-information question is pending. No GPU was rented or provider
account accessed. Do not invent a host, CUDA capability or a passing run.

The preferred Mac/MLX workflow still belongs to FDEC-087, depends on FDEC-016 and
requires its own explicit owner-confirmed transition. It is not silently used to
replace the PyTorch/PEFT acceptance or bypass task dependencies. Actual email
training separately requires admitted independent data/labels/prompt and current
authority; no Codex email/label output is used. Both prohibited Codex packs retain
their actual training/evaluation denials. No actual classifier quality,
probabilities, public weight permission, host switch, spend, release allocation
or task closure/version request is asserted. D003 remains Active; FDEC-020 cannot
dispatch with unfinished dependencies.

All numeric tensor/checkpoint staging was removed by the guarded owned temporary
directory. Only code and metadata evidence enter Git; no tensor, email body,
credential or private dataset. Pre-existing `.idea/` is untouched. The global goal
remains Active: this turn materially advances genuine engine/codec verification,
while preserving the remaining GPU obligation rather than declaring completion.
