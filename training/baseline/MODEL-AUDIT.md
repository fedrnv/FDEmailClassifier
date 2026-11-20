# Stock baseline model and runtime observations

Scope: local stock-model inference only. This document does not approve public
distribution of downloaded tensors, fine-tuned weights, datasets or runtime
bundles. It does not certify the model publisher's underlying pretraining corpus.

On 2026-11-20 the public Hugging Face API and pinned publisher documents were
observed without downloading tensors. Machine-readable document hashes and
metadata are in FDEC-015 `evidence/qwen-observations-v1.json`; the observation
script is retained there. `qwen-stock-v1.json` binds that observation and the exact
eight local files needed by the adapter. LFS artifacts use SHA-256; other files
use publisher Git-blob SHA-1 identities and lengths, not plain file SHA-1.

- Publisher/model: [Qwen/Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B),
  revision `c1899de289a04d12100db370d81485cdf75e47ca`.
- [Pinned license](https://huggingface.co/Qwen/Qwen3-0.6B/raw/c1899de289a04d12100db370d81485cdf75e47ca/LICENSE):
  Apache License 2.0; observed SHA-256
  `832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e`.
  Its grant provides the local-use basis. Any later redistribution needs its own
  documented release audit, license/notice compliance and operator authorization.
- [Pinned model card](https://huggingface.co/Qwen/Qwen3-0.6B/raw/c1899de289a04d12100db370d81485cdf75e47ca/README.md)
  describes `enable_thinking=False` and Qwen3-compatible Transformers. No quality
  or 119-language performance claim has been measured here.
- The single safetensors file is 1,503,300,328 bytes, SHA-256
  `f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`.
  No tensor download or actual snapshot verification occurred in this task turn.

Public package metadata observed candidate versions
[Transformers 5.23.0](https://pypi.org/pypi/transformers/5.23.0/json) and
[PyTorch 2.15.0](https://pypi.org/pypi/torch/2.15.0/json), both declaring Python
3.11 or newer. The adapter requires exactly these top-level versions; this is
not a claim that they are installed, interoperable or wheel-audited. Transformers
declares Apache 2.0. PyTorch metadata declares a combination of Apache-2.0,
Apache-2.0 WITH LLVM-exception, BSD-2-Clause, BSD-3-Clause, BSL-1.0, ISC, MIT and
Zlib. Metadata does not replace the installed wheels' notices or an audit of
their transitive/native components. Before an actual run, provision and verify a
compatible local environment, retain its exact dependency versions and artifact
hashes privately, and run the real adapter check. The report binds a digest of
installed distribution names/versions; that digest alone is not an install lock.
Runtime and actual-model integration remain unverified until this happens.

Local software tests need neither a GPU nor a VPS. A downloaded stock snapshot
could be evaluated on CPU; throughput has not been measured. Do not purchase a
host or switch to the owner's Mac merely to pass these software checks. Assess
hardware using an admitted corpus, sequence lengths and an actual pilot when the
plan reaches the operator-confirmed training handoff. No paid service is used.
