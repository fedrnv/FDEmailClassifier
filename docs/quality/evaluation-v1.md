# Multi-label evaluation suite v1

FDEC-017 supplies metric/report software and acceptance on frozen labeled
classification metadata. Its acceptance does not establish Qwen accuracy,
multilingual coverage, phishing reliability, calibration or actual training.
FDEC-015 stock-model measurements and FDEC-016 supported-GPU acceptance remain
separate incomplete obligations; no D003 gate or Epic closure is inferred.

## Local acceptance and report

```powershell
powershell -NoProfile -File training/eval/test-evaluation.ps1
.venv/ingestion/Scripts/python.exe training/eval/metric_oracle.py `
  --output-dir training/outputs/metric-oracle-run-001
```

The oracle has a fixed input path and SHA-256. It contains four classification
metadata vectors, all 12 topic labels, two declared language buckets, artificial
identities and one invalid-prediction marker. It contains no email subject/body,
personal data or model-generated output. These Codex-assisted technical vectors
must not become actual email training/evaluation data. No actual model receives
them. The report is explicitly `software-metric-oracle-only`,
`actual_model_executed: false`, `model_quality_claim: false`.

`metrics.json` and its checksum receipt are written into a new private directory.
Existing output is never overwritten. Raw responses, prompts, emails, paths and
credentials are not included in reports or diagnostics. A report receipt is the
commit marker; failed publication rolls back only the newly owned directory.
The oracle cannot select another fixture or bypass real inference admission.

Hand-computed expectations for this technical example:

| Quantity | Numerator / denominator | Expected value |
| --- | --- | --- |
| Topic micro F1 | 2×8 TP / (2×8 TP + 1 FP + 4 FN) | 16/21 |
| Topic macro F1, all 12 labels | (7×1 + 2/3 + 4×0) / 12 | 23/36 |
| Priority correctness | 2 / 4 | 1/2 |
| Action correctness | 2 / 4 | 1/2 |
| Spam decided-negative FPR | 1 FP / (1 FP + 1 TN) | 1/2 |
| Spam full-negative unresolved bounds | [1 FP, 1 FP + 1 unresolved clear] / 3 | [1/3, 2/3] |
| Phishing decided-negative FPR | 2 FP / (2 FP + 1 TN) | 2/3 |

The en bucket has topic micro F1 4/5 and action correctness 1. The de bucket has
topic micro F1 8/11 and action correctness 0. These are fixture arithmetic,
not language-quality measurements. Tests additionally exercise 119 syntactically
distinct language buckets without claiming ISO identities, translations or actual
119-language performance. No hard-coded two-language limit exists.

## Definitions

`classification_metrics.measure(gold, predictions)` is the pure API. Gold rows use
the existing classification-v1 validator, record identity, declared language and
six boolean supervision masks. Unknown/unreviewed gold must stay masked false;
a fallback action is not automatically truth. Duplicate IDs, bad schemas,
misalignment, empty inputs or uncertain supervised gold reject. The caller must
provide an exact aligned list: a known attempted invalid prediction is `None`;
silently omitting prediction rows is not allowed. The pure metric function alone
does not authenticate model execution, corpus provenance, rights or consent.

- Per-topic TP/FP/FN, support, precision, recall and F1 use only topic-eligible
  rows. Invalid/unknown/abstained outputs miss the true positive topics, so their
  false negatives remain in micro/macro F1. Topic correctness is exact-set
  correctness with every unresolved output incorrect.
- Micro F1 pools TP/FP/FN over the fixed 12-topic vocabulary. `macro_f1` averages
  all 12 topic F1 values, using zero for an undefined class F1 only when some
  topic-eligible rows exist. `macro_supported_f1` separately averages only classes
  having gold support, with its explicit denominator. Unsupported per-class F1
  is null when both truth and prediction have no positive; all topic scores are
  null if no topic gold is eligible.
- Priority/action correctness includes invalid, unknown and abstained predictions
  as failures in the eligible denominator. Fixed confusion matrices expose the
  unresolved categories and decision coverage; unreviewed heads are excluded.
- Spam/phishing/malware expose TP, FP, TN and decided FN, gold clear/flagged
  supports, unresolved clear/flagged counts, head accuracy and coverage. Standard
  `false_positive_rate` is FP/(FP+TN) on decided known-clear gold. A zero value
  must be read together with decision coverage and unresolved bounds.
- `unresolved_fpr_bounds` gives [FP/N_clear,
  (FP+unresolved_clear)/N_clear]. It shows the range if unresolved outputs became
  clear/flagged decisions; it is not a statistical confidence interval.
  `recall_with_unresolved_as_misses` is TP/N_flagged. No eligible/decided
  denominator produces null, not an invented perfect score or zero FPR.

The same definitions are applied overall and independently by declared language.
Counts are aggregated before ratios; language rates are not naively averaged.
Language tags and label truth require independent review, not automatic inference
by this arithmetic code. Confidence intervals and calibration belong to later
tasks; no security acceptance threshold or confidence claim is introduced here.

## Actual model evaluation

`training/eval/evaluate.py` runs the fixed, pinned local stock Qwen adapter after
the unchanged baseline admission verifies the independent source runs, current
commercial-training/evaluation grants, signed consent, source/thread/family/
duplicate grouping, exact test partition and independent multilingual gold review.
It has no fixture mode, arbitrary model identity or policy-root override. The
baseline inference prompt, non-thinking switch, token budgets and strict output
parser are reused. Bad outputs become explicit attempted failures; infrastructure
or input-budget failures abort instead of silently dropping examples.

```powershell
python training/eval/evaluate.py --opt-in `
  --inventory training/data/approved/inventory.json `
  --consent training/data/approved/consent.json `
  --split-dir training/outputs/approved-split `
  --annotations training/data/approved/independent-gold.json `
  --source-run training/data/approved/source-1 `
  --source-run training/data/approved/source-2 `
  --source-run training/data/approved/source-3 `
  --model-dir models/downloads/qwen-stock-v1 `
  --output-dir training/outputs/evaluation-run-001
```

Use the privately prepared compatible interpreter and existing authority-key
process. Do not put keys in command arguments. Snapshot, input/model identities,
consent/review and implementation digests accompany aggregates. Current authority
is checked before each private-text use and publication, and inputs replay again
before committing a report. This is a point-in-time check, not future-consent
guarantee. Both Codex fixture packs remain denied for actual training/evaluation.

No real model was run for FDEC-017 acceptance. Actual evaluation remains unavailable
until independently prepared admitted data, current authority, local stock tensors
and a compatible runtime exist. Model/runtime/dataset redistribution is not
approved; no download, training, host switch, paid service or publication occurs
through acceptance. Later model adapters can call the pure metric API with their
own verified execution boundary; this does not authorize arbitrary weights here.
