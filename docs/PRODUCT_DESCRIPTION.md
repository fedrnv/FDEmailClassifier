# FDEmailClassifier — public product description

**Status:** Planned/open-source project in development. The following text is approved positioning copy, not evidence that a finished release is available.

## One-line description (GitHub About / website SEO)

Free, open-source multilingual AI email classifier for Rust, Python, C and C++ — local inference, privacy-first, and designed for commercial integration.

## Short description

FDEmailClassifier is a free, open-source, self-hosted email classification engine built in Rust. It is designed for Rust, Python, C and C++ applications and optional REST/Docker deployment. The planned Qwen3-0.6B backend classifies messages into 12 overlapping topics plus priority, security indicators and recommended actions. It is designed for personal, open-source **and commercial use**, including in the paid FDFiles service.

## Website / README long description

**Classify email locally. Keep control of your data.**

FDEmailClassifier is being developed as a reusable open-source library and optional self-hosted API for multilingual email classification. It aims to provide 12 topic categories (multi-label), priority estimation, spam/phishing indicators, and suggested actions with a structured result. Its Rust core is intended to be accessible through native Rust, C, C++ and Python APIs. No third-party cloud inference is required by the planned self-hosted architecture.

**Free and open source, including for commercial products.** The project intends to license its own source code under Apache-2.0, allowing both free and paid software to integrate it. The standalone FDEmailClassifier component is planned to be supplied at no cost; FDFiles can use it as part of a paid product without imposing a requirement to open source FDFiles.

**Model and quality transparency.** The intended base model is Qwen3-0.6B. The model's broad language capability does not imply proven classifier accuracy for every language. Model weights will be downloadable only after verified dataset/model rights; until then they may remain private. Source code, training tooling, documented adapters and reproducible public benchmark methods are separate from weight release eligibility.

## Suggested website FAQ

**Can I use FDEmailClassifier in a paid application?**
Yes. Commercial integration, including use within paid FDFiles subscriptions, is part of the approved product direction. The project's original code will be licensed Apache-2.0 before release; third-party components and model weights retain their applicable terms.

**Will FDEmailClassifier cost money?**
The project intends to make its self-hosted open-source components available free of charge. Running your own infrastructure may incur normal computing costs.

**Can I download a trained model?**
The plan is to publish trained model weights for free only once training-data and model licenses permit it. A public model release is not currently promised.

**Will email content be sent to an external AI provider?**
The planned deployment performs inference locally/on your own server. No external AI inference API is required. Operators still control their own hosting, logging and privacy settings.

**Are 119 languages already verified?**
No. Language availability and measured classification quality will be published per language as benchmarks become available.

**Are the benchmarks public?**
The plan is to publish benchmark software, evaluation methodology and permissible examples/results; real personal mail is not published without appropriate rights.

## Metadata suggestions

- Repository description: `Free, open-source multilingual email classifier for Rust, Python, C and C++. Local AI, commercial use allowed.`
- Website: `https://emailclassifier.fedrv.de` (planned until deployed)
- Topics: `rust`, `email-classification`, `qwen3`, `open-source`, `apache-2-0`, `multilingual`, `python`, `cpp`, `commercial-use`.
- Branding: official red `E` rounded-square SVG under `assets/branding/`, with light/dark variants.

## Important qualification

This copy must not be published with the words “available”, “released”, “Apache-2.0 licensed”, “verified for 119 languages”, or “download model” unless the exact statement is supported by actual implemented files, licenses, artifacts or measured results.
