# FDEC-019 acceptance verification

Source commit: `6e4b1c949329e3dab993bba2ae6d06ab896c921f`.
Source state: `543ff4539b825e41876cd9a21f6c212dd27552cc836a8747965adcbde56af72b`.
FDTasks 5.6 policy: `ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403`.
Frozen execute admission: `frozen-readiness-v4.json`, accepted and PASS before
final tests. The immutable TASK.md is unchanged. The append-only
`acceptance-scope-clarification-v1.md` corrects the executor's earlier unnecessary
requirement for actual email-trained weights; the original AC explicitly permits
synthetic/non-sensitive fixtures. No contract outcome or criterion is weakened.

| Original criterion | Actual verification | Result |
| --- | --- | --- |
| AC-01: GGUF load/round trip and release-manifest license gate | Complete random-tensor Qwen3 plus nonzero rank-2 LoRA, real PEFT reload/merge, upstream base/adapter/merged conversion, actual pinned-source llama.cpp load and two-token base+LoRA/merged agreement; all four variants, tokenizer/chat metadata, dataset manifest/cards and CycloneDX SBOM; actual artifact integrity and real fixture release denial; isolated counterfactual exact-rights gate | PASS |
| AC-02: invalid/missing input preserves state and never publishes unsafe output | Missing lineage, invalid CLI arguments, malformed GGUF, NaN/wrong architecture, artifact mutation, unsigned actual candidate, HMAC/checksum rebinding, extra file, current-authority revocation, incomplete/wrong rights audit, runtime hash/probe mismatch and rollback preserving prior output | PASS |

Final focused command: `powershell -NoProfile -File training/export/test-export.ps1`.
Monitor `2522c1bc-3cf5-40c3-b75e-78a06eb0815d`, exit 0, six Python tests in
2.175 seconds, numerical container check and official SBOM schema validation.
Full unabridged output: `test-output-v1.txt`.

Final complete-model command:
`powershell -NoProfile -File training/export/test-model-export.ps1 -OutputDirectory C:/GitHub/FDEmailClassifier/training/outputs/fdec019-6e4b1c9-v1 -ReuseObservedBuild`.
Monitor `fb9499b0-621e-49e2-a255-4b94b6e93c83`, exit 0. Full unabridged output:
`fixture-run-v1.txt`. Verification checks the actual emitted inventory, full-model
probe report and default registry release rejection, then validates this model's
SBOM against the hash-pinned official CycloneDX 1.6 schema. Cached AJV ignores
optional unknown format annotations; generated documents have no affected
timestamp/URL/email fields. This is structural validation, not a format audit.

Environment: local Windows x64, CPython 3.14.5, 49 hash-pinned export-only wheels,
Torch 2.15.0, Transformers 5.23.0, PEFT 0.22.0, GGUF 0.19.0, safetensors 0.8.0,
sentencepiece 0.2.3, CMake and existing Visual Studio Build Tools 2022. No hosted
acceptance tests, GPU rental, Mac transition, paid license or VPS were needed.
The opt-in model-tooling bootstrap also completed successfully, monitor
`52091f9c-875c-4989-b4e0-292a21a7f087`. It verifies exact public artifact hashes
and installs offline/no-deps/require-hashes. No dependency or model is bundled.

The runtime was really compiled from clean upstream llama.cpp commit
`29b52d398b294509746ec0a3f28948a3107c0213` using the production build function.
Build monitor `dfb1b38e-afff-4d06-89a4-8737418a30f2` exited 0; immutable
`runtime-build-v3.json` records executable SHA-256
`5e4a2acbbad532f5f29f2564eb25901a6ebce9039bc096fd4eb6e3c8a8d44ac2`
and CMake-cache identity. Final acceptance reuses only that fixed observed private
path and hash, rechecks the clean source pin, and checks executable identity
before/after actual model loads. Fresh builds use the same production function.
The compiler/runtime is not a test double; the separate unit test explicitly is.

Model fixture: deterministic seed 104729, one Qwen3 layer, hidden 32, intermediate
64, four attention heads/two KV heads, rank-2 LoRA over seven target modules.
Random LoRA-B is nonzero; no optimizer or gradient/training step runs. PEFT
save/reload logits agree; merge maximum absolute probe error is
`8.940696716308594e-08` within the explicit tolerance. The real GGUF adapter has
14 tensors and base/merged models have 13 each. Both actual runtime loads exit 0
and generate identical two-token numeric-probe output hash
`4d6c81d25b182f867ed4b2a31f9eb3c3ac3f8892ac1d9ebb260093417aff8126`.
This is load/integration evidence, not full-logit equivalence or classifier
quality, calibration, language coverage or phishing-reliability evidence.

Metadata-only copies from the complete candidate are preserved byte-for-byte as
`fixture-report-v1.json`, `fixture-receipt-v1.json`, `fixture-manifest-v1.json`
and `fixture-sbom-v1.json`. The receipt authenticates no real rights: its manifest
is a technical fixture with public weight permission false. The actual verifier
checks every private artifact hash, required variants/tokenizer/card/provenance
inventory and real release denial. Weights/tokenizer bytes remain ignored; no
weight, email body, secret or private training data enters Git. The public
tokenizer LICENSE/version/file observations establish local tooling use only.

## Failure/recovery and rights boundaries

The initial MinGW build failed on missing Windows SDK thread-power types. Existing
MSVC successfully built the same pinned source without patches. A first complete
model attempt stopped because sentencepiece was missing. Its wheel omitted its
license file: the initial audit failed; a successor audit checked the exact
official version-tag Apache-2.0 LICENSE and retained it for local use before
offline installation. The next attempt exposed `--no-conversation` unsupported
by this upstream interactive `llama-cli`; the supported `llama-completion` target
was built instead. Final full-model checks pass with that production selection.
Earlier attempts and helper successors are retained, not overwritten. Failed
candidates rolled back their own newly created directories; no existing release
or model was overwritten. Temporary tensor staging was cleaned by owned paths.

The real `models/release-policy-v1.json` remains empty/default-deny. Both free and
commercial public weight distribution require a separately documented exact
artifact audit covering base notices, training/public-weight rights, independent
annotation/prompt rights, generator terms, tokenizer rights and attribution.
Positive rights-gate tests use isolated counterfactual audits, not actual grants.
Actual exports replay existing source-origin/license/current consent/grouped
split/annotation admission and authenticated trainer checkpoint lineage. Revoked
authority and altered inputs fail closed. Both Codex packs remain prohibited for
actual email-model training/evaluation. No Codex email text or category gold is
fed to any model; only numerical technical tensors/tokens are used here.

The supported actual checkpoint backend is unquantized LoRA. QLoRA rejects until
quantized-base equivalence is validated; MLX import remains a separate compatible
backend obligation after the owner-confirmed FDEC-087 handoff. Real trained
checkpoint export is not claimed. No actual email training, actual classifier
evaluation, OpenAI training permission, new dataset approval, real weight rights,
release allocation, public publication or external spend is asserted.

FDEC-015 and FDEC-016 remain incomplete. D003 remains Active and still requires
dependency readiness, its own local gate and independent review. The next turn
must reassess unfinished D003 training/handoff work before dispatching a gate
whose dependencies are not Done. Pre-existing `.idea/` is untouched. The complete
numeric candidate/build are retained in ignored private outputs for reproduction.
