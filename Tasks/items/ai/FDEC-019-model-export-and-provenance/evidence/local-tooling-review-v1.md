# Local exporter tooling decision

Scope: local development/test imports only; no wheel, dataset or weight release.
Each downloaded wheel matched the exact filename/version SHA-256 served by its
public PyPI version API. Embedded LICENSE/NOTICE identities and metadata are
retained in wheel-observations-v1.json; original wheels stay ignored/private.

Inspected license material establishes the following local-use basis: gguf MIT;
safetensors Apache-2.0 (resolving the null PyPI metadata field for this wheel);
colorama BSD-style notice; NumPy BSD notice and bundled permissive component
notices; PyArrow Apache-2.0 with bundled notices; PyYAML MIT; requests Apache-2.0;
idna BSD-3-Clause; urllib3/charset-normalizer MIT; certifi MPL-2.0; tqdm mixed
MPL-2.0/MIT. No wheel is bundled into a model release by this decision. The full
NumPy/PyArrow native-component notice sets are preserved in the original wheels;
this is not a completed redistribution audit of those binary packages.

The permitted action is installation of these exact hash-pinned artifacts from
the local wheel directory, with no index/dependency resolution, into a new ignored
`.venv/export` environment. The ingestion/training environments are not modified.
No model tensors, email contents, training texts, labels or paid licenses are
downloaded. The policy grants no dataset/model rights or publication authority.
Actual Torch/PEFT conversion and trained-model runtime loading remain unverified.
