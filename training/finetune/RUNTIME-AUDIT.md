# Trainer runtime observation and limits

Scope: preparation of local software, not public redistribution or a completed
runtime/license audit. No training package or model tensors were installed or
downloaded in this task turn. The stock model's pinned Apache-2.0 local-use basis
and unresolved release boundaries are in `training/baseline/MODEL-AUDIT.md`.
Actual source rights, independent labels/prompt and current authority remain
separate mandatory checks; a runtime package license cannot grant dataset rights.

The task's `evidence/runtime-observations-v1.json` records exact public metadata
hashes on 2026-11-20 and the observation script. Candidate versions are torch
2.15.0, transformers 5.23.0, peft 0.22.0, safetensors 0.8.0, bitsandbytes 0.50.2
and numpy 2.5.5. The config profile binds that observation. These packages are not
claimed installed, tested together, wheel-audited or supported by current hardware.
The native checkpoint and CUDA implementations have not run on this workstation.

Publisher metadata declares Transformers/PEFT Apache, bitsandbytes MIT, PyTorch
a combination of Apache-2.0 (including LLVM exception), BSD, BSL-1.0, ISC, MIT and
Zlib, and NumPy a combination of BSD-3-Clause, 0BSD, MIT, Zlib and CC0-1.0.
Safetensors' observed PyPI license field is null: do not treat that metadata alone
as clearance. Its [upstream license file](https://github.com/safetensors/safetensors/blob/main/LICENSE)
is available, but a floating main-branch file is not a versioned wheel audit.
Resolve the exact installed wheel notices and transitive/native dependencies
before installation/distribution decisions. No blanket release approval is issued.
Future actual runs must privately retain their exact environment lock and artifact
hashes; the runtime name/version digest in checkpoints does not replace that lock.

Implementation references checked against primary documentation:

- [PEFT LoRA](https://huggingface.co/docs/peft/package_reference/lora) for adapter
  configuration and k-bit preparation.
- [Transformers bitsandbytes](https://huggingface.co/docs/transformers/quantization/bitsandbytes)
  for the explicit NF4/double-quantization path.
- [PyTorch restricted load](https://docs.pytorch.org/docs/stable/generated/torch.load.html)
  for `weights_only=True` after checkpoint authentication.
- [Optimizer state semantics](https://docs.pytorch.org/docs/stable/generated/torch.optim.Optimizer.state_dict.html)
  require exact parameter-order binding rather than assuming IDs identify names.

This preparation does not prove exact reproducibility across releases, drivers,
operating systems or different devices. Context binds package-version fingerprint,
Python/platform, CUDA/cuDNN, device capability and NVIDIA driver, and refuses a
changed environment. The dedicated GPU check must still establish exact resumed
state on its supported target. Software doubles cannot establish that property.
