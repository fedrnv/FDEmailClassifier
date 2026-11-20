# FDEC-005 verification and continuation

Baseline 4e2f1a1ec1e11a377ab21bd4fa21d853615091a4. Upstream policy commit:
00a0d019c1e73d5ecf4c4e75c42c38497c154e50; SHA256:
ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Environment: Windows x86_64, Rust/Cargo 1.98.0, PowerShell 5.1.

AC-01 PASS: manual review of ADR-0001 against README, core v1 schema,
FDEC-022/025/030/032 boundaries and docs/architecture/boundary-review.md.
All four language routes reviewed for input/result ownership, same schema, cleanup,
threading and errors. Optional REST shares engine; selected llama.cpp GGUF adapter
keeps native pointers private, CPU baseline and explicit optional GPU features.
Model package identity/integrity/trust, local-only activation and atomic rollback,
product/API/ABI/schema/model version distinctions explicit. No exact backend/native
binding version admitted before FDEC-022 audit. No model/data downloaded.

AC-02 PASS (architectural review): eleven synthetic invalid/recovery scenarios in
boundary-review.md checked for explicit rejection, prior state preservation and
named implementation owner. Includes missing path, invalid manifest/hash/trust,
unsupported schema/tokenizer, unavailable GPU, invalid C input, concurrent close,
failed reload and invalid/advisory output. These are tabletop contract checks;
not runtime loader/ABI tests. Implementing tasks must prove those scenarios.

Current executable wire evidence: cargo test --locked --offline -p
fdemailclassifier-core schema => four passed, zero failed. Negative malformed
payload and unsafe unknown/abstained states rejected; round-trip/taxonomy passed.
This proves only the current shared schema boundary. No native SDK integration
coverage claimed. Full cross-language execution remains FDEC-033.
Local record check: powershell -NoProfile -File scripts/validate_tasks/repository.ps1
=> PASS (85 records). git diff --check => PASS. Actual documentation diff reviewed;
all task-specified boundaries covered, no production implementation altered.
Technical primary references inspected: llama.cpp public C header, Rustonomicon FFI
and PyO3 thread-safety docs (linked in ADR). They are living design references,
not dependency pins. No external side effect; no independent item review required.
FDEC-007 remains the independent Epic review.

## Candidate raw hashes
- Tasks/decisions/ADR-0001-local-inference-and-sdk-boundaries.md: 8829f0924de9c9859d6156c7738bec30fa7f8ed588732b9f537f7eae335b4ade
- docs/architecture/boundary-review.md: e8e8d53d078e277689db49d7cec8f99d977a2d65c9d6d3b26bf1a26d13d6cba2

## Checkpoint
FDEC-005 verified for closure with one task_closed request. Next fresh turn:
admit FDEC-072 (public GitHub repository presentation), because immutable FDEC-006
plus dependency-added event require it before the integration gate. Bind all
FDEC-001 spec/event revisions as its dependency, all current Epic inputs and scoped
rules. D001 alone Active. Then FDEC-006 gate and FDEC-007 independent review.
No running process or temporary artifact; preserve unrelated .idea files. Standing
user authority covers sequential task development; external release/model publish
still needs explicit operator authorization. Goal active; no current external
blocker for selecting the next task. FDTasks snapshot redistribution restriction
remains and must be respected in any publication work.
