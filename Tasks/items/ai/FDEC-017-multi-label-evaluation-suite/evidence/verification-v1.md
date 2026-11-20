# FDEC-017 acceptance verification

Frozen candidate: `9fb05d59ef5e347c75be4d47d7b419c7697edc7f`.
Actual source-state SHA-256:
`572803dd9c9edaf352071b66bb9c30bcce9b5b7aea3d6de52d47036b6bd0c8d8`.
FDTasks policy SHA-256:
`ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403`.
Initial execute admission and frozen execute admission passed; the immutable task
and its two acceptance criteria are unchanged.

The accepted outcome is the multilingual metric/report suite. AC-01 explicitly
requires evaluation against frozen labeled fixtures and a structured report.
These fixtures are classification metadata with no email content, real personal
data or actual model output. The completed acceptance establishes arithmetic,
report generation and software boundaries. It does not establish model quality,
actual corpus admission, training, calibration, rights to distribute weights or
the unfinished FDEC-015/FDEC-016 outcomes.

| Criterion | Executed verification | Outcome |
| --- | --- | --- |
| AC-01: per-topic/macro/micro F1, priority/action correctness, spam/phishing false positives by language | Frozen four-row metadata fixture covering all 12 topics and en/de buckets; independent hand-derived fraction oracles; actual CLI-generated checksum-bound structured report | PASS for the original fixture-based evaluation-suite criterion |
| AC-02: invalid/missing input preserves state and fails explicitly | Misalignment, duplicate IDs, schema/unknown supervised gold, masked/zero supports, unknown/abstained/invalid predictions, repeated output rejection, sanitized CLI input, missing admission before model initialization, real current-consent revocation between predictions | PASS |

Trusted command: `powershell -NoProfile -File training/eval/test-evaluation.ps1`.
The final accepted run follows `frozen-readiness-v2.json`; full output and exact
monitor identity are retained in `test-output-v1.txt`. An earlier run on the same
frozen code passed 10 tests in 22.118 seconds, monitor
`128f7b0f-f37c-4257-a1a6-0b3be2817598`. Exploratory eight- and ten-test runs also
passed before candidate freeze; they are not substituted for the final evidence.

The separate report command ran at this candidate:
`C:\GitHub\FDEmailClassifier\.venv\ingestion\Scripts\python.exe training/eval/metric_oracle.py --output-dir training/outputs/fdec017-9fb05d5-v1`.
Monitor `6f38b639-42c0-408f-a541-358fe017a9d0`, exit zero. Verbatim output is
`fixture-run-v1.txt`. The raw report and checksum receipt were copied byte-for-byte
to `fixture-report-v1.json` and `fixture-receipt-v1.json`; the receipt binds report
SHA-256 `df3944cb52afff38dc4443ac6e9c7693f4d3ad915c0be915bd654e0521455f91`.
The report explicitly has `actual_model_executed: false`,
`model_quality_claim: false` and scope `software-metric-oracle-only`.

Hand-derived fixture expectations and actual results agree:

| Measurement | Expected and observed |
| --- | --- |
| Topic micro F1 | 16/21 (8 TP, 1 FP, 4 FN) |
| Topic macro F1 over 12 labels | 23/36 |
| Priority correctness | 2/4 |
| Action correctness | 2/4 |
| Spam decided-negative FPR | 1/2, denominator 2 |
| Spam unresolved full-negative bounds | [1/3, 2/3], denominator 3 |
| Phishing decided-negative FPR | 2/3 |
| en topic micro F1, action correctness | 4/5, 1 |
| de topic micro F1, action correctness | 8/11, 0 |

Counts, confusion matrices, per-topic F1 and denominators are retained overall
and by language. All-unresolved predictions produce null decided-negative FPR
and bounds [0,1], rather than an invented zero FPR. Unknown gold remains masked;
no eligible malware gold gives null scores. Correctness/topic recall retain
invalid and abstained attempted predictions as failures. The all-label macro
and gold-supported macro are separately named. Exact-set topic correctness,
per-language aggregation, permutation invariance and 119 syntactic language
buckets are checked. The latter is not a claim of 119 real language identities,
translations, samples or model performance.

The revocation test actually replays the existing three-source D002 ingestion,
rights, grouped split and signed current-consent checks under isolated
counterfactual software policies. A protocol double returns one classification
and activates a newer revoked consent snapshot. The next prediction is blocked;
no report is created, and a later attempt fails before model initialization. No
actual language model consumes the fixture emails/labels. These simulated rights,
independent reviews and language tags are not real-world approval evidence.

## Compatibility, limits and cleanup

Existing classification-v1, baseline metrics, dataset/fixture licensing, origin,
consent, grouped-split and training implementations are unchanged. New actual
inference reporting reuses their checks with no CLI policy-root, fake-model,
source-approval or fixture-promotion bypass. Current authority is checked before
each private-text use and publication; source/annotation bytes replay again before
publication. Both Codex fixture packs remain denied for actual training/evaluation.
The pure arithmetic API alone is not a model-execution or data-rights attestation.

Actual Qwen measurements remain unavailable pending admitted independent gold,
current authority and compatible local model/runtime artifacts. FDEC-015 and
FDEC-016 remain Blocked; no task or Epic contract is narrowed by FDEC-017 closure.
No actual model, training, tensor download, new runtime installation, remote host,
Mac handoff, paid service, version allocation or public artifact release occurred.
No confidence, calibration or phishing-safety guarantee is inferred from fixtures.

Temporary fixtures were removed through guarded temporary paths. The single
ignored oracle output directory is retained for reproducibility alongside its
metadata-only evidence copies. No raw emails, secrets, real private data or weights
enter Git. Pre-existing `.idea/` is untouched and untracked. D003 remains the only
Active development Epic and still requires its later integration gate and fresh
independent review. The next sequential task is FDEC-018.
