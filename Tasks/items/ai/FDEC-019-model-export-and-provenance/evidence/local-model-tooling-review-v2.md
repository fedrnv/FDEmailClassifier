# Local numerical model-check tooling decision

This extends the local-use-only tooling review to the pinned Torch 2.15.0,
Transformers 5.23.0, PEFT 0.22.0 and resolved dependencies. All 48 wheel filenames,
sizes and hashes matched their exact public PyPI version APIs. Source material and
embedded license identities/prefixes are preserved in model-wheel-observations-v2.

The primary declared/local embedded licenses are Apache-2.0 (including LLVM
exception in PyTorch components), MIT, BSD variants, BSL-1.0, ISC, Zlib, MPL-2.0,
CNRI-Python and PSF-2.0. Null fields for Jinja2/MarkupSafe, markdown-it/mdurl and
other wheels are resolved by their embedded notices, not by assuming no license.
These notices permit local test imports/use. This is not a redistribution audit
of the runtime binaries or their full native/transitive contents.

tokenizers 0.23.3 omitted a license file in its wheel. The initial inspection
stopped. The successor observation resolved the local-use basis from the official
version tag and exact upstream LICENSE commit/hash, recorded as a separate
supplement. No absent-license row was silently approved or removed from review.

Permitted action: offline --require-hashes/--no-deps installation of the exact
lock into the existing isolated export-only environment. Existing 12 format-tool
versions stay pinned. Ingestion/training environments are unchanged. The model
check uses a randomly initialized tiny architecture, numerical weights and fixed
numeric tokens; no email training content, labels or pretrained weights are used.
Downloading hash-verified published tokenizer metadata under the already reviewed
Qwen Apache-2.0 license is permitted for the local format/runtime check only.
No trained-model, dataset, tokenizer or runtime distribution is cleared here.
