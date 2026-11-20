# FDEmailClassifier

Open-source, local-first multilingual email classification engine.

- **Core:** Rust library; native Rust SDK and C ABI, C++ wrapper, Python bindings.
- **Model:** Qwen3-0.6B; optional GGUF CPU/GPU inference backend.
- **Output:** 12 multi-label topics, priority, security flags and suggested action.
- **Languages:** accepts all languages supported by the base model; per-language quality is measured and reported, never assumed.
- **Service:** optional self-hosted REST API and Docker distribution.
- **Training:** reproducible Python LoRA/QLoRA pipeline with dataset-license provenance.
- **Publishing:** public source, documented artifacts, FDUpdate distribution after compatibility verification.
- **Website:** https://emailclassifier.fedrv.de (planned).

This repository follows **FDTasks v5.6**; see `Tasks/` for immutable Epics and tasks. Work is planned, not implemented.

## License intent

The project's **original source code** is intended for Apache-2.0. Third-party code, datasets and model weights have their own licenses. No dataset or trained weights may be published before explicit rights review.

## Security

Never commit email contents, personal data, production credentials, model access tokens or unapproved training datasets.
