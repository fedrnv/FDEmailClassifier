# D002 local changed-area integration gate

Run from a clean committed candidate:

```powershell
powershell -NoProfile -File docs/verification/run-d002-current.ps1 -ExpectedSource <full-40-character-commit>
```

This supplements the immutable adoption-bound `DEVELOPMENT.md`; FDEC-013 records the documentation-location refinement through append-only acceptance events. Run acceptance locally. No hosted workflow, corpus download, provider API, training, artifact upload or publication is part of this command.

The current command first verifies the FDEC-099 outcome/source continuity and accepted FDEC-100 process repair, then runs the unchanged eight-stage `scripts/verification/D002.ps1` component. It produces one combined nine-stage result on the same frozen candidate. The original component command remains available for its narrower software integration scope. The current outcome check replays its historical verifier in a bounded temporary worktree and removes it; source/data rights are not broadened. See `d002-outcome-continuity.md` for the preserved outcome and deferred actual-data obligations.

## Prerequisites and source identity

Use the pinned Rust toolchain and cached dependencies, Python 3.14.5 and the already audited ingestion environment at `.venv/ingestion/Scripts/python.exe` with PyArrow 26.0.1. Mapping schema checks use cached AJV CLI 5.0.0 through `npm exec --offline`. Dependency absence fails explicitly; the gate does not install packages or retrieve data.

The requested commit must be HEAD. Tracked working bytes and the index must both match it; unmerged/unsupported index entries and assume-unchanged/skip-worktree flags reject. Untracked source rejects, except this gate task's append-only evidence/events and the repository's narrowly recognized unrelated IDE metadata. No arbitrary exclusion list or source-root CLI override is provided. Source state is rechecked before and after every stage. A reviewer reruns the exact candidate in a clean checkout with the audited cached runtime, rather than substituting a later closure/review commit or an uncommitted working tree.

## Stages and direct interactions

| Stage | Verification |
| --- | --- |
| Effective outcome/source continuity | Exact original outcome and owner-authority interpretation, accepted process repair and immutable original request; 102 protected files, 23 current metadata/index negatives and 14 historical negatives |
| Frozen-source negatives | Wrong candidate, working/index differences, hidden Git flags, untracked implementation and state changes reject |
| Dataset rights and ingestion | Existing audited allowlist negatives; exact-byte opt-in private ingestion, MIME normalization, actual pinned Parquet decoding, provenance and rollback |
| Annotation/schema boundary | Mapping ambiguity/missing/abstention semantics, masks, mapping schema and existing classification v1 schema |
| Augmentation/input separation | Original/native fixture generation, translation, lineage, repeatability and the unchanged independent ingestion boundary |
| Sinabis preparation contract | Exact reviewed profile, attribution and separate downstream uses; source/origin/label/split failures, no per-message automatic supervision |
| Consent/splits | Current signed authority, whole-source/thread/duplicate/family components, immutable reference manifests and contamination/revocation rejection |
| Cross-component pipeline | Actual ingestion plus boundary replay across Parquet, JSONL and EML; annotation content-ID join; signed three-cohort split build/verify; adverse label/manifest/consent mutations and Codex/Sinabis boundary interactions |
| Rust contract | Targeted offline tests of the unchanged classification schema consumed by the mapping projection |

The integration fixture drives the real existing license guard; its positive decisions and provider/consent records are **counterfactual software fixtures**, not actual source approvals. The fixture provider enum models a reviewed-source branch and does not attest human authorship of a corpus. All content is generated technical tokens or existing explicitly fixture-only augmentation. The production allowlist is unchanged, temporary policy roots are inaccessible through production CLIs, and no model consumes fixture texts or labels. An annotation-review fixture tests interface semantics, not independent ground-truth quality.

Fixture runs verify source hashes before decoding and replay normalized text/annotations from a verified snapshot. Mapping uses a separate canonical annotation hash and the same content ID as the normalized source. The preparer binds snapshot/receipt identities into a signed inventory. The gate checks that the split references contain neither bodies nor subjects, preserve complete cohorts/threads and reject substituted assignments even when the superficial manifest checksum is updated. Current revocation invalidates an old manifest without overwriting it. This is a software integration of the trusted preparer/authority contract, not authentication of a real person's legal consent.

## Result and limits

Only after all stages and the final source check pass, stdout includes `GATE_RESULT_BEGIN`, a `fdec-gate-result/v1` JSON object, and `GATE_RESULT_END`. It binds FDEC-013, D002, candidate SHA/tree and policy SHA, with each stage's command/result. A failed stage returns failure and emits no passing result object. Capture the command, complete log and typed result in fresh immutable task evidence; never overwrite earlier runs. Temporary fixture cleanup is bounded to owned resolved paths, and previously existing data/results are preserved on invalid input.

The current runner relabels the inner component markers as `COMPONENT_GATE_RESULT_BEGIN/END`; its eight-stage decision is component evidence. Only the outer nine-stage decision is current gate acceptance. The result preserves both actual sub-results and hashes of the current runner, composition module, original component and outcome verifier. Composition rejects mismatched candidate/tree/policy/state, missing or substituted stages, unsafe claims and invalid runner identities. Run `powershell -NoProfile -File docs/verification/test-d002-current-result.ps1` for its metadata-only positive and 26 negative checks; those counterfactual fixtures do not attest real acceptance or source rights.

The gate is deliberately independent of the ignored Sinabis source copy. Its public metadata/rights profile is checked, while corpus-level measurements remain in FDEC-011's pinned verification evidence. Missing optional data does not block testing the components. All Codex packs remain fixture-only; this command does not approve actual training or evaluation on their contents.

An exact Sinabis source-rights profile is not an admitted training dataset. Independent annotation, quality checks, current consent/split integration and the training task remain required; the existing split gate has not been broadened to CC BY. The single Oil source family must not be manufactured into three independent cohorts. No actual corpus train/test admission, model accuracy, 29/119-language quality, training run or model release is claimed by a passing software gate. D002's independent review must assess the exact passing candidate and these limits separately.
