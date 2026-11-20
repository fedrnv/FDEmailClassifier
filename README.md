# FDEmailClassifier

**Free and open-source multilingual email classification — designed for commercial use, including paid FDFiles integration.**

> **Development status:** The public product is under development. Features described below are planned unless explicitly marked released.

FDEmailClassifier is a privacy-first, local-inference email classification engine. The goal is to provide a reusable standalone component, not a service tied to FDFiles or a paid API.

## Intended features

- **Rust core:** native Rust SDK; C ABI, C++ wrapper and Python bindings.
- **Model:** Qwen3-0.6B as planned inference backend, with configurable local GGUF CPU/GPU runtime.
- **Results:** 12 multi-label email topics, priority, security indicators and suggested actions.
- **Languages:** broad multilingual support is targeted; real-world classifier quality must be measured per language rather than assumed.
- **Deployment:** optional self-hosted REST API and Docker packaging.
- **Training and benchmarking:** reproducible LoRA/QLoRA pipeline, dataset-rights provenance, independent public benchmark tooling and reports.
- **Distribution:** public source and planned free release artifacts through GitHub Releases and FDUpdate.
- **Website:** https://emailclassifier.fedrv.de (planned).

## Free software and commercial integration

**The standalone FDEmailClassifier project is intended to be available at no cost.** Its original source code is planned for **Apache License 2.0** (the license and required notices must be published before the first licensed release). Under that license, third parties may use, modify and integrate the code into **commercial and proprietary software**. In particular, **FDFiles may use the classifier inside its paid service without opening the FDFiles source code**.

This is **not** a “non-commercial only” or “no-resale” license: Apache-2.0 also allows redistribution and commercial services by others, subject to its terms.

Trained weights/LoRA adapters are **not automatically licensed by the source-code license**. Free public model release is a goal, conditional on documented rights for the base model and each training source. No dataset or trained weights are published by this plan alone. Until cleared, weights remain private or are omitted from public artifacts, and the rest of the project can progress independently.

See [commercial-use and release policy](docs/legal/COMMERCIAL_USE_POLICY.md) and [approved product descriptions](docs/PRODUCT_DESCRIPTION.md).

## Work tracking

This repository follows **FDTasks v5.6**; see [Tasks/](Tasks/) for immutable Epics and tasks and [project plan](docs/PROJECT_PLAN.md). Planning records do not represent finished functionality.

## Branding

The selected default is the **red rounded-square E** logo, with [light and dark SVG variants](assets/branding/). The planned information site follows the visual language of files.fedrv.de without copying private assets.

## Privacy and security

No raw emails, personal data, credentials, model access tokens, or uncleared training datasets may be committed. The planned self-hosted engine does not require an external cloud inference API. Benchmark results and language claims are published only when verifiable.
