# Training compute assessment

Assessment date: 2026-11-20. The owner permits use of a Linux VPS when useful. This does not authorize a paid rental or transfer the separate EUR 50 dataset-license allowance to compute.

## Current environment and immediate work

The Windows environment exposes 8 logical processors and 16 GiB RAM. Its display controllers report Microsoft Remote Display Adapter and Microsoft Basic Display Adapter; no `nvidia-smi` executable was found. A usable CUDA device has not been established. The workspace drive has approximately 85 GiB free at assessment time.

Continue source-license research, Sinabis 10K preparation, mapping development, thread/duplicate checks and software-fixture tests locally. These steps do not require GPU training. Do not download the much larger 10M corpus merely to research its license or language schema. No VPS is needed for the current FDEC-011 software outcome.

## Later training decision

FDEC-015 specifies a Qwen3-0.6B baseline, and FDEC-016 specifies a Qwen3-0.6B LoRA/QLoRA trainer with a GPU checkpoint/resume test. A Linux machine with a supported GPU is useful for those tasks if no suitable local GPU is available. An ordinary CPU-only VPS does not supply that capability.

For planning only, consider one GPU with 12–16 GiB VRAM, 16–32 GiB system RAM and enough disk for pinned input data, the base model, temporary files and retained checkpoints. These are provisional capacity estimates, not measured minimums or acceptance results. Context length, batch size, precision, optimizer and checkpoint retention determine actual requirements. Start with a small batch and bounded context, measure peak GPU allocation and elapsed time, and size a real run from that result. Quantization can reduce weight memory; it does not remove activation or optimizer costs.

The [Qwen3-0.6B model card](https://huggingface.co/Qwen/Qwen3-0.6B) identifies the planned base model. [PEFT quantization documentation](https://huggingface.co/docs/peft/en/developer_guides/quantization) describes combining low-bit loading with adapter training. Exact base weights, training dependencies and redistribution rights still require their own pinned audit.

Do not provision paid infrastructure now. When a training run is ready, present a concrete provider, GPU, hourly price, storage charges, maximum duration and total spending cap for separate owner confirmation. If the owner supplies an existing VPS, inspect its available hardware and supported stack before scheduling work; keep credentials outside Git. Use only admitted independent training inputs. Codex-authored texts and labels remain software fixtures, including on remote machines.

No remote connection, purchase, corpus upload or model-training run was performed for this assessment.
