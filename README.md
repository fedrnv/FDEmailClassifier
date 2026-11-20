# FDEmailClassifier

**Free, open-source email classification with local inference, designed for commercial integrations including paid FDFiles.**

FDEmailClassifier is an independent open-source project for multilingual,
multi-label email classification. Its goal is inference on your own machine with
Rust, C, C++ and Python SDKs sharing one output contract.

**Status: early development.** The Rust workspace and classification schema work
today. Inference, usable classification SDKs, trained model packages and REST are
planned. There is no released classifier, downloadable model or production
installation command yet.

## Current and planned capabilities

| Area | Available now | Planned |
| --- | --- | --- |
| Rust core | Buildable crate and strict JSON/Serde v1 contract | Local classification engine and native SDK |
| Output | Twelve multi-label topics, separate priority/security/action, unknown/abstained states | Measured inference, calibration and thresholds |
| Other SDKs | Native library and isolated Python build scaffolds | Stable C ABI, C++ wrapper and PyO3 extension |
| Models | Architecture and license admission boundaries | Qwen3-0.6B-based training; optional llama.cpp/GGUF CPU and GPU backend |
| Service | Server help/version scaffold | Optional self-hosted REST API and Docker |
| Distribution | Local source build documentation | Audited releases and FDUpdate integration |

Topic labels and security assessments are advisory metadata. The project does not
automatically archive, delete or reply to emails. Model language coverage is an
experimental target, **not verified per-language accuracy**. No 119-language quality
or phishing-reliability guarantee is offered; measurements must precede claims.

## Architecture

Rust SDK and PyO3 bindings will call one Rust engine. C uses a versioned C ABI;
C++ wraps it with RAII. Optional REST shares the engine. A private backend boundary
isolates local GGUF inference and verified model packages. Local SDK use will not
require Python, a remote API or a running service.

Read the [architecture decision](Tasks/decisions/ADR-0001-local-inference-and-sdk-boundaries.md)
and [SDK boundary walkthrough](docs/architecture/boundary-review.md).

## Try the source scaffolds

Prerequisites: Git, rustup and a native Rust linker/toolchain for your platform.
`rust-toolchain.toml` pins Rust 1.98.0. From a local checkout:

```text
cargo check --workspace --locked
cargo test --locked -p fdemailclassifier-core schema
cargo run --locked -p fdemailclassifier-example
cargo run --locked -p fdemailclassifier-server -- --help
```

The example checks the build entrypoint; it does not classify email. The server
starts no listener. Source checks were run on Windows x86_64 MSVC; other platform
support is not yet verified. Offline use requires cached dependencies/toolchain.

See the [workspace guide](crates/README.md), [Rust example](examples/README.md),
[Python scaffold](bindings/python/README.md), [v1 contract](docs/api/classification-v1.md)
and [synthetic JSON example](schemas/examples/classified.json). C/C++ headers and
an importable Python package will follow their implementation tasks.

## Contribute and report issues

Start with [CONTRIBUTING](CONTRIBUTING.md), [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md)
and [DEVELOPMENT](DEVELOPMENT.md). Work follows immutable
[FDTasks records](Tasks/README.md) and the [delivery plan](docs/PROJECT_PLAN.md).
Acceptance and integration checks run locally; hosted workflows must be manually
dispatched. Follow [SECURITY.md](SECURITY.md) for vulnerabilities. Never commit
credentials, raw emails, personal information or private training data.

## Free software, commercial integration and training

The standalone project is intended to be available at no charge. Original code
uses Apache-2.0, which permits commercial and proprietary integration, including
paid FDFiles, subject to its terms. FDEmailClassifier stays independent of FDFiles
internals and does not require a paid external inference API. The project's free
distribution policy adds no noncommercial or no-resale restriction.

Weights and LoRA adapters need separate base-model and dataset rights audits,
including commercial inference and public redistribution. Until approved, they
remain private or are omitted from releases. Missing optional data rights do not
stop independent software and benchmark development. See the
[commercial-use policy](docs/legal/COMMERCIAL_USE_POLICY.md) and
[product descriptions](docs/PRODUCT_DESCRIPTION.md).

Training is planned for Qwen3-0.6B with LoRA/QLoRA. The owner's MacBook Air M4
with 32 GB memory is the preferred temporary MLX host when a dependency-ready
training step requires it. The [Mac handoff](docs/training/MACBOOK_M4_HANDOFF.md)
requires operator confirmation and verified private artifact transfer before
returning to the original development workstation. No training run is claimed.
Independent benchmark tooling and measured public reports are planned; source
licenses, cohort independence and per-language evidence remain mandatory.

## Branding

The selected logo is a red rounded-square E; see [branding assets](assets/branding/).
The planned website follows the visual language of files.fedrv.de with neutral
backgrounds and red accents.

## License and artifact rights

Original source and documentation are [Apache-2.0](LICENSE); see [NOTICE](NOTICE).
Third-party material retains its own terms. The [inventory](docs/legal/THIRD_PARTY.md)
and [dependency audit](docs/api/dependency-audit.md) record current boundaries.
Models/datasets require separate audits before distribution. The existing FDTasks
reference has unresolved redistribution rights: a public source package must
resolve those rights or use a reviewed exclusion plan.

Website: https://emailclassifier.fedrv.de — **planned; not deployed by this project yet**.
