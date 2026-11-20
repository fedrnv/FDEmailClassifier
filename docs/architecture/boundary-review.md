# ADR-0001 acceptance walkthrough

Reviewed baseline: 4e2f1a1; decision: Tasks/decisions/ADR-0001-local-inference-and-sdk-boundaries.md.
Scope is architectural approval. Native SDKs/backend/REST are still unimplemented.

## Four SDK paths

Use the same synthetic metadata result in `schemas/examples/classified.json`:
schema version 1, topics work+finance, high priority, spam clear, phishing/malware
unknown and suggested action review. No email or personal information is needed.

| Path | Walkthrough | Required result and cleanup | Review |
| --- | --- | --- | --- |
| Rust | Borrow bounded input, call the shared engine, validate owned result | Exact Classification v1; dropping result does not require engine lifetime; Result on failure | Consistent with existing Serde ownership and FDEC-029 |
| C | Check ABI, create opaque engine, pass pointer/length, receive owned result, close engine, read/free result | Same v1 JSON; result retains independent ownership; same library frees it once | No Rust/native backend layout crosses C; FDEC-030 defines symbols and tests |
| C++ | Wrap C handle and result with move-only RAII; transfer ownership then destroy wrapper | Same JSON and one free per successful allocation; exception cannot cross C | One inference implementation, consistent with FDEC-031 |
| Python | Construct PyO3 engine, validate input, run bounded Rust call without borrowed Python references, return owned Python result, close | Same v1 fields; Python references outlive native call safely; close synchronizes context lifecycle | No Python dependency in core; FDEC-032 defines actual extension |

Optional REST adds authentication and request/resource bounds to the same engine;
it must not introduce a second taxonomy or a remote dependency for local SDKs.
The public response schema and advisory-only behavior are identical.

## Negative and recovery scenarios

These scenarios are tabletop checks of the accepted boundary, not claims that a
model loader or native API already exists. Each was checked for an explicit error,
preserved prior state and a named implementation owner.

| Synthetic invalid input | Architectural response | Prior state / recovery | Owner |
| --- | --- | --- | --- |
| Missing initial local model path | Model-unavailable error, no inference result or network download | Engine unavailable; retry only with explicit valid local artifact | FDEC-022/025 |
| Manifest missing digest, unsupported version or path `../outside.gguf` | Reject during staging before load | Active generation unchanged | FDEC-025 |
| File digest differs from manifest or trust proof missing | Integrity/trust error; do not activate or publish | Preserve prior generation; operator provides trusted package | FDEC-025/051 |
| Package requires schema 2 but caller supports 1 | Compatibility error; no silent field deletion or downgrade | Preserve prior generation/result; install compatible pair explicitly | FDEC-024/025/033 |
| Wrong tokenizer/prompt/calibration identity | Package compatibility rejection before activation | Existing requests finish on prior generation | FDEC-019/025 |
| GPU selected but feature/device unavailable | Explicit capability error; CPU only if caller permits fallback | No implicit download or changed execution policy | FDEC-022 |
| Null C pointer with nonzero length, invalid UTF-8 or unsupported ABI | Safe status error, no successful output allocation | Caller corrects input; no native context mutation | FDEC-030 |
| Reload fails while requests are active | No swap; existing generation retained until users release it | Retry corrected candidate, never mutate live weights | FDEC-025/026 |
| Concurrent close and classify / exhausted pool | Serialize/reject close or return bounded busy/cancelled status | No use-after-free or unbounded queue | FDEC-026/030/032 |
| Unknown topic, duplicate label or action delete | Existing v1 Serde contract rejects payload | No result published, no action executed | FDEC-003/024 |
| Unknown or abstained result requests archive | Existing v1 Serde contract rejects cross-field state | Result must use review and empty topics | FDEC-003/024 |

Review outcome: all four SDK routes converge on one engine, define result/input
ownership and error cleanup, preserve the accepted v1 contract and have bounded
failure ownership. No missing authority or backend revision is concealed: actual
native support, artifact signatures and license audits must be proven in the
named implementation tasks before their use or distribution.

## Current executable evidence

Run `cargo test --locked --offline -p fdemailclassifier-core schema`. Four current
tests cover JSON round-trip, twelve topic names, malformed/missing fields, duplicate
keys/labels, and safe unknown/abstained serialization. This proves current wire
validation only. It does not prove the future native lifecycle scenarios above.
FDEC-033 must run the same golden contract through all four implemented SDKs.
