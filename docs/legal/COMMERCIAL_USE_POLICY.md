# FDEmailClassifier: open-source and commercial-use policy

**Status:** Approved project/product direction (2026-11-20). This document records intended product and release rules; it is not a legal opinion, third-party license, or evidence that training rights were cleared.

## Product and use model

- FDEmailClassifier is a **free-of-charge, open-source** multilingual email classification library/service. No license fee, activation, paid subscription or mandatory hosted AI API is required for the self-hosted project.
- Original FDEmailClassifier **source code is to be released under Apache License 2.0** (FDEC-001 must add and verify the actual LICENSE and required notices). A README or this policy document alone does not grant the license before it is actually applied.
- **Commercial use is explicitly intended and allowed by the chosen Apache-2.0 source-code license**, including embedding/calling the classifier from the paid FDFiles service and other third-party commercial products. FDFiles does not have to become open source merely because it uses an Apache-2.0 component.
- The project owner intends not to charge for FDEmailClassifier itself. Apache-2.0 nevertheless permits third parties to sell support, binaries or redistributed software subject to its terms; this project must **not** add an incompatible non-commercial or no-resale restriction.
- No dependency on FDFiles internals. Rust core, Rust SDK, C ABI/C++ and Python bindings, REST service, Docker setup and training/benchmark tooling remain standalone project components.

## Dataset rights and training

- Admit datasets and generated texts to production/commercial training **only** after documenting source, exact revision, provenance, author/provider rights, license terms, required notices and permitted purposes.
- Specifically check **commercial training**, **use for commercial inference (including in FDFiles)** and, if model publishing is planned, **public redistribution of resulting weights**. Do not infer rights from an unverified Hugging Face license label or from source-code Apache-2.0.
- A model trained on only some allowed sources must identify exactly those sources. Unclear/denied optional sources are excluded with a recorded reason. Never falsify a manifest or weaken fail-closed admission.
- Generated text/labels from Codex/OpenAI are **technical fixtures only by default**, not training inputs, unless the applicable OpenAI/provider terms and the intended use have been separately documented and approved.
- Raw private mail, credentials, sensitive personal data and legally uncleared datasets must not enter public git or public training artifacts.
- The initially researched sources include `imnim/multiclass-email-classification`, `weijianzhg/email-triage-action-seed`, `talby/spamassassin`, and optionally Sinabis synthetic email sets. **Listing a source is not approval**; each exact dataset needs its own evidence-based decision. An optional source never becomes mandatory for unrelated software implementation.

## Model weights, packaging and publishing

- The **target** is a free downloadable, reproducible trained Qwen3-0.6B classifier, provided the base-model and full training pipeline permissions permit its public distribution. Until this gate passes, trained weights/LoRA adapters remain private or are omitted from artifacts.
- Free public source/binaries, SDKs, REST server, Docker recipes, docs, and independent test tooling can continue to be developed/released even if model distribution is not yet possible. Do not advertise a downloadable model until it actually ships.
- GitHub Releases and FDUpdate **public channel** may distribute only release-cleared artifacts. In particular, model-weight eligibility must be verified separately from code eligibility. Public Docker images must not embed uncleared model weights.
- Attribution/NOTICE, manifest and checksum obligations follow all third-party components/datasets that are actually used.

## Public benchmark and quality statements

- Publish reproducible benchmark code, methodology, permitted test fixtures, source/model version identifiers and aggregated measured results. Publish private/consented real email bodies **only when their owners and applicable law explicitly permit that specific disclosure**; default is not to distribute them.
- Benchmark cohorts must remain independent of training, split by source/thread and screened for near-duplicates; report synthetic vs real-email results distinctly.
- Never claim verified quality for all Qwen-supported languages or for phishing detection without independent per-language/per-risk evidence. A public report must disclose missing cohorts and limitations.

## Responsibilities / release gates

- **FDEC-001**: apply actual Apache-2.0 licensing, NOTICE, dependencies and contributor terms.
- **FDEC-072**: GitHub About/README public messaging.
- **FDEC-058**: website `emailclassifier.fedrv.de` messaging and commercial-use FAQ.
- **FDEC-074 / FDEC-077**: audit per-source training and resulting-model redistribution rights.
- **FDEC-052 / FDEC-053**: independent approval gates for FDUpdate and GitHub/public registry assets.
- **FDEC-068**: final release acceptance evidence and accurate statements.
- This policy does not change their FDTasks statuses or authorize any external payment/publication on its own.
