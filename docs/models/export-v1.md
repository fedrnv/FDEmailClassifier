# Private model export and weight-release admission

The exporter supports private PEFT float32 LoRA, F16 base GGUF, F16 GGUF LoRA and
F16 merged GGUF with integrity/provenance metadata and a separate default-deny
weight-release gate. Local acceptance uses a complete tiny randomly initialized
Qwen3: real PEFT save/reload/merge, real upstream conversion and real llama.cpp
load/inference. This is the original task's synthetic-fixture acceptance scope.
No email training, pretrained tensor download, actual trained-classifier quality
or public weight clearance is established. FDEC-015/FDEC-016 retain their separate
real-data/training acceptance obligations.

## Local tooling and numerical checks

`models/export-runtime-requirements-win-py314.txt` pins all 12 Windows CPython 3.14
wheel hashes. Each artifact matched the exact public PyPI version API. Embedded
license identities and the local-use decision are in FDEC-019 evidence. A separate
ignored `.venv/export` was installed offline with no dependency/index resolution;
the ingestion/training environments are unchanged. gguf 0.19.0 and safetensors
0.8.0 null PyPI license fields were resolved using their wheel MIT/Apache-2.0
license files for local use. This does not approve wheel/runtime redistribution.
The optional model-check profile adds audited Torch/Transformers/PEFT tooling,
their dependencies and sentencepiece (49 pinned wheels total), plus published
tokenizer metadata. No pretrained tensors or email datasets are downloaded.
On a fresh Windows CPython 3.14 amd64 checkout, run
`python training/export/bootstrap.py --opt-in` to materialize the exact previously
audited wheels and official schema hashes, then install the isolated offline
environment. Existing files/environments are preserved; package mismatches reject
when the runtime is used. Other platforms require their own wheel audit/lock.
Use `--model-check` to install the larger numerical-model-check profile into the
isolated export environment. All installation is offline after hash-verified
acquisition. The tokenizers and sentencepiece wheels omit their license files;
exact official version-tag LICENSE supplements establish local-use permission.
The failed initial audits and successor observations are retained. Runtime or
tokenizer redistribution is not approved by this tooling review.

```powershell
powershell -NoProfile -File training/export/test-export.ps1
.venv/export/Scripts/python.exe training/export/export_cli.py software-check `
  --output-dir training/outputs/export-oracle-run-001
```

The software command uses two fixed numerical matrices, with no emails, personal
data, category labels, model training or pretrained tensors. It saves/loads real
safetensors, writes/reads real GGUF Qwen3 LoRA-format metadata/tensors and checks
the values. This is a container-level check: the two-tensor fixture is not a
complete loadable classifier. Its signed/unsigned manifest kind is exclusively
`technical-container-fixture`; the release gate always rejects this kind.

For the full model check, prepare the exact clean upstream converter checkout
using the task's `fetch-converter-source-v1.py` acquisition helper, then run:

```powershell
python training/export/bootstrap.py --opt-in --model-check
powershell -NoProfile -File training/export/test-model-export.ps1 `
  -OutputDirectory C:/GitHub/FDEmailClassifier/training/outputs/numerical-model-run-001
```

The full fixture has one Qwen3 layer, hidden size 32, rank-2 LoRA, deterministic
random numerical tensors and a fixed numeric-token probe. It does not run an
optimizer or use email/category gold. It copies hash-verified published tokenizer,
chat template and Apache LICENSE metadata, creates all four variants, model cards,
dataset manifest and SBOM, then verifies the actual artifact inventory and real
registry release denial. The numeric HF probe checks adapter reload and merge
tolerance; the GGUF runtime checks exact agreement of two generated tokens for
base+LoRA versus merged F16. This is not full-logit or task-quality equivalence.
The optional `-ReuseObservedBuild` accepts only the fixed locally observed build
path and exact recorded binary/source identities; otherwise it builds afresh.
No arbitrary executable is accepted. Weights stay in ignored private output.

The actual [GGUF Python package](https://github.com/ggml-org/llama.cpp/tree/29b52d398b294509746ec0a3f28948a3107c0213/gguf-py)
is used rather than a private format imitation. Offline cached AJV validates the
generated CycloneDX 1.6 SBOM against the official schema snapshot from
CycloneDX/specification commit `5fee6af48d43c751dc6a5b31138f06af2b10bac5`.
Schema hashes are checked first. The website returned HTTP 403; the versioned
official-repository fallback and failed original acquisition script are retained.
Cached AJV performs structural schema validation with optional unknown format
annotations ignored; the generated documents contain no timestamp/URL/email
fields using those ignored annotations. This is not a format-annotation audit.
SBOM hashes explicitly identify installed distribution METADATA, not full wheel
identities or complete binary-package license clearance. Build libraries are
listed, not bundled. Model/file identities are in the separate candidate manifest.

## Actual private export

The `export` command takes explicit opt-in, checkpoint/base model/converter paths,
current inventory/consent/split, independent reviewed annotations/prompt and all
source ingestion runs. These are private inputs, not repository fixtures:

```powershell
python training/export/export_cli.py export --opt-in `
  --checkpoint training/outputs/approved-training/step-000000100 `
  --model-dir models/downloads/qwen-stock-v1 `
  --llama-cpp-dir training/data/llama-cpp-approved `
  --inventory training/data/approved/inventory.json `
  --consent training/data/approved/consent.json `
  --split-dir training/outputs/approved-split `
  --annotations training/data/approved/training-gold.json `
  --prompt training/data/approved/independent-training-prompt.json `
  --source-run training/data/approved/source-1 `
  --source-run training/data/approved/source-2 `
  --source-run training/data/approved/source-3 `
  --output-dir training/outputs/model-candidate-001
```

This uses a prepared interpreter matching the export tool profile plus Torch
2.15.0, Transformers 5.23.0 and PEFT 0.22.0. These versions passed the complete
random-tensor model check; no real trained checkpoint is available here.
Export is CPU-based and can need multiple
gigabytes of memory and temporary disk. No runtime/model auto-install, Hub download,
host provisioning, Mac transition or upload exists in the exporter.

Existing training admission replays the independently audited non-OpenAI source
bytes/annotations and current rights, consent, split, reviewed canonical labels
and prompt. Every context hash must match the authenticated FDEC trainer checkpoint
and current implementation. The exact pinned stock model files are verified.
Checkpoint HMAC/bytes are checked before restricted `torch.load(weights_only=True)`.
Only matching finite float32 LoRA tensors are exported; optimizer/RNG are omitted.
Both Codex fixture packs stay denied for actual training/evaluation. No new source
or real weight approval is granted by export metadata.

Current support is unquantized LoRA. QLoRA exports reject until quantized-base
equivalence is separately validated: substituting the full-precision base for a
4-bit training base is not silently accepted. MLX checkpoints likewise need a
verified compatible import path after FDEC-087; none is claimed by this task.

Variants are PEFT float32 LoRA, F16 base GGUF, F16 GGUF LoRA and F16 merged GGUF.
The pinned [upstream converters](https://github.com/ggml-org/llama.cpp/tree/29b52d398b294509746ec0a3f28948a3107c0213)
must be an exact clean checkout; converter/LICENSE hashes also match observations.
Only fixed local `--base`, `--outfile`, `--outtype f16` paths/flags are used;
remote IDs/trusted remote code are not permitted. Offline Hub variables are set.
Model/tokenizer/chat-template metadata and base LICENSE are copied from the
verified published snapshot. Model cards explicitly mark quality/language coverage,
calibration and public weight distribution unverified. No local input paths or
email texts enter cards, dataset manifest or diagnostics.

The implementation saves/reloads PEFT adapters and checks fixed numerical-token
logits, safely merges and checks that probe, verifies GGUF tensor containers, then
loads base+LoRA and merged GGUF in llama.cpp. A deterministic two-token numerical
probe must agree. This is load/adapter integration, not full-logit equivalence or
classifier quality. Captured model output is never logged; only a hash is retained.
These checks are implemented but have not run with actual trained weights.

The exporter builds the exact clean pinned llama.cpp source in a new private
owned temporary directory, CPU-only, with curl/tests disabled and only the
completion target selected. It rechecks the source before/after the build, records the binary
and CMake-cache hashes, and rechecks binary identity before each probe and after
completion. No arbitrary executable flag or extra operator build-approval flow
exists. Build output is not distributed and is cleaned up only under the verified
temporary path. Actual compilation passed in the Windows MSVC 2022 build,
followed by complete numerical-model load acceptance.
Protocol unit tests separately use a labeled process double. An older MinGW build
failed on Windows SDK thread-power types; that failed attempt is retained and no
pinned source was patched. The pinned version's interactive `llama-cli` rejects
`--no-conversation`; the production probe uses its supported `llama-completion`
target. Fresh builds require CMake and a compatible compiler (MSVC 2022 on Windows).

Candidates are new private/ignored directories. File hashes and context are HMAC
bound; the checksum receipt is written last. Failed build/authority checks roll
back only the newly owned candidate, preserving earlier accepted files. Source
provenance/current authority replay before/after publication. The dataset manifest
contains source identities/counts and provenance digests, no raw records. SBOM and
model cards accompany the complete artifact. Temporary merged weights are removed
only from verified owned staging paths. All weights stay out of Git.

## Separate public-weight rights gate

`models/release-policy-v1.json` has no approved entries. Training/evaluation rights,
a base Apache license, unsigned source declarations or a successful format load
cannot clear trained-weight distribution. Both free and commercial distribution
require a documented exact-artifact review. The read-only `release-gate` command
never publishes or allocates a release version.

After real conversion/load checks, a registry entry must bind the exact candidate
manifest SHA-256 to an immutable `models/audits/<name>.json` plus public/redacted
legal evidence Markdown hashes. The audit separately identifies base weights,
dataset manifest, annotation and prompt hashes, every allowed variant, reviewer,
date, explicit public-weight permission and completed obligations: base notices,
dataset training/public-weight rights, annotation/prompt rights, generator-provider
terms, tokenizer rights, model card/attribution. Real independent evidence must
substantiate those facts; fields asserting clearance are not proof by themselves.
Current independently approved data/consent/review admission is repeated at gate
time. A changed/revoked source, missing obligation, altered artifact, wrong key,
simulated fixture, missing runtime verification or absent audit rejects.

Even a successful gate returns only `eligible_for_operator_review: true`,
`published: false`. Separate explicit operator authorization is still required for
any later public publication. Counterfactual test policies are isolated outside
the real registry and confer no actual permission. No real entry or legal evidence
claiming cleared weights has been added. A successful numerical-model check
demonstrates export software acceptance only. Actual trained weights require
current independent provenance and the complete separate release audit.
