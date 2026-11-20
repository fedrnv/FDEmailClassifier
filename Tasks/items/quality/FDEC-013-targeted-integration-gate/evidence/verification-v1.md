# FDEC-013 targeted integration verification

Result: PASS. Exact candidate `0bcd4c4f377af86ee8b83d1d0bf770f0eb448ad8`, tree `558697de3b18fd1bea8358a144bae90a90231c76`. Policy SHA-256 `ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403`. All five functionality dependencies were Done at admission; D002 is the sole active development Epic. The accepted task specification and adoption-bound DEVELOPMENT.md were not edited. The append-only documentation amendment points to `docs/verification/d002-gate.md` without reducing the gate outcome or negative criterion.

## Exact execution

```powershell
powershell -NoProfile -File scripts/verification/D002.ps1 -ExpectedSource 0bcd4c4f377af86ee8b83d1d0bf770f0eb448ad8
```

Monitor `19cf1aab-f50c-4e54-b10e-ac3ad304f100` completed with exit 0. `result-v1.json` is extracted from the actual `GATE_RESULT_BEGIN`/`GATE_RESULT_END` output and carries the typed `fdec-gate-result/v1` contract. Its candidate SHA/tree were compared with Git and its source-state identity `c003a26275a7451d3ace7d6a47a00668ac262042b357acb3daa7a8eb2eb3d287` matched accepted frozen readiness. No passing result was manually substituted for a failed stage.

The monitor truncated an intermediate observation; its complete nontruncated terminal log was read and checked for this command's first stage and final exact-candidate pass marker. `test-output-v1.txt` retains every stage's content with trailing whitespace/final blank lines normalized. The original raw monitor log SHA-256 is recorded in the typed result. The earlier launcher failure and successful six-case preflight remain separate immutable evidence.

Environment: Windows x64, PowerShell 5.1, Git 2.45.1, CPython 3.14.5, existing audited PyArrow 26.0.1 ingestion environment, cached AJV CLI 5.0.0 and pinned Rust 1.98.0 dependencies. All checks ran locally; npm and Cargo checks used offline mode. No package installation or source/model download was performed.

## AC-01: changed interfaces and direct interactions

All eight stages passed on the same committed source, checked before and after each stage:

1. Source-freeze positives and eight negative cases: wrong commit, tracked bytes, index-only change with restored working bytes, both hidden Git flags, untracked implementation/unknown IDE content and a mismatched frozen-state digest.
2. Rights and ingestion: 20 ingestion tests, existing allowlist rejection scenarios and dependency consistency. Real pinned Parquet decoding, JSONL/EML, MIME attachment exclusion, normalization, checksums, duplicate provenance and failed-write recovery passed.
3. Annotation/schema: 21 mapping tests plus generated valid mapping/classification fixtures and invalid-schema rejection. Missing, ambiguous and abstained dimensions preserve supervision masks rather than becoming trusted defaults.
4. Fixture generation and independent ingestion: 20 original augmentation, 15 native grammar and 13 integrity/origin-boundary tests. Both Codex packs stay fixture-only; current source bytes, normalized text/labels and rights proofs must match.
5. Sinabis contract: 23 tests for exact reviewed profile, separate downstream rights/attribution, source snapshot limits, unresolved origins, absent trusted labels, lexical duplicate detection, role consistency, Unicode-safe output and static diagnostics. The real ignored corpus copy is not a prerequisite or input to this gate.
6. Consent/splits: 21 tests for protected current signed authority, monotonic activation, revocation/expiry, whole-source/thread/duplicate/family grouping, actual source-rights checks, immutable manifests and corruption/contamination failures.
7. Cross-component pipeline: six integration scenarios. The positive path performs actual ingestion and independently replays it through the training-input boundary for three generated technical-token sources in Parquet, JSONL and EML. A separate annotation fixture joins by verified content ID. Four records enter a signed inventory and produce three nonempty role cohorts; source and thread membership stay indivisible. The test uses the real guard against isolated counterfactual policies, without mocking production inclusion.
8. Rust classification contract: all four targeted schema tests pass, including state round trips, invalid payload rejection and all twelve topics matching the JSON contract used by mapping.

Python test groups total **139**: 20, 21, 20, 15, 13, 23, 21 and 6. The four Rust tests, license scenarios, source negatives and JSON-schema fixtures are additional checks. This is bounded D002 integration and its immediate classification interface, not an unrelated workspace-wide regression.

## AC-02: invalid input preserves state and prevents unsafe output

The new pipeline negatives reject modified normalized labels despite an updated checksum, changed split assignment despite a rebound manifest hash, and an old manifest after current consent revocation. Failed admission/verification does not overwrite previously completed manifests or repair attacker-supplied input into an accepted state. Missing independent groups after revocation creates no replacement split run. Conflicting annotation candidates disable topic supervision. Reference manifests contain no bodies or subjects.

Generation/translation produces explicit fixture-only receipts for both Codex packs; the independent training boundary and split-ingestion bridge reject them. Sinabis source-rights metadata does not become a canonical ingestion receipt, label grant or accepted split. The earlier component suites add source/evidence/path/schema/rollback and malformed-argument coverage. Source freezing independently rejects dirty working bytes and dirty index state, including changes hidden from ordinary diff by Git flags.

Temporary Git repositories, source files, simulated grants and outputs were generated only in bounded private fixture directories and cleaned through guarded owned-target cleanup. All fixture policies, provider enums and annotations are counterfactual software test inputs: they attest neither real human authorship nor real dataset ownership/consent. No model consumed any text or label. Production registries and previously accepted implementation files were unchanged by this task.

## Limits and next task

The passing gate verifies software integration. It does not establish actual corpus train/test admission, trusted real annotations, model training, accuracy, multilingual coverage or weight redistribution rights. Sinabis preparation measurements and source-origin evidence remain in FDEC-011; independent annotations, quality, current consent/split integration and training admission remain unresolved for actual training. The existing CC BY/split boundary is not relaxed, and the Oil source family is not fabricated into independent cohorts. Optional source limitations do not become false approvals or block independent software work.

No corpus or weights were committed; no credentials, external messages, purchase, model training, Mac switch, push, publication or release/version allocation occurred. Unrelated IDE state remains untouched. Close only FDEC-013 with one task version request. FDEC-014 must independently review this exact passing candidate and the stated limits before D002 closure; no independent acceptance or Epic completion is claimed here.
