# Raw-margin threshold calibration and abstention v1

This task supplies validation-only threshold fitting and an abstention policy.
It does not turn classification-v1 JSON labels into scores or probabilities.
The stock baseline currently emits no measured per-label margins, so calibrated
model decisions remain unsupported until independent instrumentation and reviewed
data exist. `probabilities_estimated` is always false. Classification-v1 remains
unchanged; its unknown/abstained states and lack of probability fields are retained.

## Numerical acceptance

```powershell
powershell -NoProfile -File training/calibration/test-calibration.ps1
.venv/ingestion/Scripts/python.exe training/calibration/calibration_cli.py software-check `
  --output-dir training/outputs/calibration-oracle-run-001
```

The frozen SHA-256-bound fixture contains numerical scores, binary arithmetic
targets and artificial identities only. It contains no email, personal data,
actual model output or source corpus. No actual model consumes these technical
vectors or their targets. The report says `software-numerical-fixture-only`,
`actual_model_executed: false`, `actual_model_calibrated: false`. It must not be
promoted to actual training/calibration or deployed model evidence.

## Algorithm and limitations

Each of 23 binary one-vs-rest labels (12 topics, four priorities, three security
heads, four actions) is fitted independently by language. Input score kind is
explicitly `binary-logit-margin/v1`: a quantitatively measured classifier head
margin, not a model's self-reported confidence, hard-label answer or token string.
The model identity and score convention must remain fixed. No probability
interpretation, confidence level, guarantee or automatic score extraction is added.
These scalar policies do not resolve mutually exclusive priority/action heads:
a later classifier adapter must abstain on contradictory decisions, enforce the
existing classification-v1 invariants and verify all required policy bindings.

Fit uses validation rows only. Test rows cannot affect thresholds, language
policies or support counts. Duplicate record/label observations and any record or
whole-group role/language inconsistency reject, as do train rows, NaN, infinity,
boolean scores, wrong labels and malformed inputs. Unknown gold and missing
scores are excluded explicitly, with unmeasured support counts. The existing real
split policy additionally groups source/thread/family/exact/near/translation copies.

The diagnostic threshold maximizes validation F1 at observed score breakpoints;
exact integer comparisons resolve F1 ties, choosing the larger threshold. The
implementation scans score histograms rather than comparing every row at every
threshold. The decision band is more conservative than that diagnostic cut:

- A negative tail contains validation negatives strictly below every validation
  positive; the highest such score is the inclusive clear cutoff.
- A positive tail contains validation positives strictly above every validation
  negative; the lowest such score is the inclusive flagged cutoff.
- Each tail and each class needs its configured support. Actual CLI defaults are
  20 per class/tail; the numerical acceptance fixture explicitly uses two.
- Scores between the two cuts, outside the observed validation range, missing
  scores, unsupported languages/labels, insufficient support or overlapping
  distributions abstain. One-sided support can decide only its measured tail.

Pure tails are an empirical property of this validation sample, not statistical
confidence or proof of future false-positive rates. Small/biased samples can
overfit; no deployment threshold is approved by software acceptance. Conflicting
ties do not produce confident tails. Held-out reporting separately records
coverage, correct fraction over all eligible cases, FP/FN on decided cases and
abstention counts. Unknown gold is never a negative. Test labels are used only for
that final report, never fitting. No test-driven threshold selection is performed.

For the technical work-topic validation sequence (-2,N), (-1,N), (0,P), (1,N),
(2,P), (3,P), the F1-optimal diagnostic threshold is 0, but the decision cuts are
-1 and 2. Thus scores -1 and 2 decide, 0 and 1 abstain, and 3.1 abstains outside
the observed range. The phishing fixture uses the independent affine scale
2×score+10 and therefore cuts 8 and 14. German sample support is insufficient;
unobserved labels are unsupported. These are software arithmetic examples only.

## Actual measured-score admission

```powershell
python training/calibration/calibration_cli.py fit --opt-in `
  --inventory training/data/approved/inventory.json `
  --consent training/data/approved/consent.json `
  --split-dir training/outputs/approved-split `
  --observations training/data/approved/measured-margins.json `
  --source-run training/data/approved/source-1 `
  --source-run training/data/approved/source-2 `
  --source-run training/data/approved/source-3 `
  --output-dir training/outputs/calibration-run-001
```

The observation object has schema `fdec-calibration-observations/v1`, score_kind,
model (`id`, exact `revision`, artifact `sha256`) and rows containing `record_id`,
`group_id`, role (`validation` or `test`), language, canonical `label`, numeric
`score` or null, and independently reviewed binary `gold` or null. It must cover
exactly the split's validation/test record IDs and agree with actual group/role
assignments. Score direction is greater = stronger evidence for the named label.
The trusted preparer must independently establish gold truth, language, measured
score provenance/direction, model-use rights and separation of independent cohorts.

Existing rights/origin checks, original source-byte/annotation replay, signed
current consent and grouped-split verification are unchanged and mandatory.
Neither Codex fixture pack is admitted. No approval or policy-root override exists
in the CLI. A protected `training/data/calibration-review/current.json` has schema
`fdec-signed-calibration-review/v1`, payload and HMAC-SHA256. Payload schema
`fdec-calibration-score-review/v1` binds canonical inventory, signed consent,
split receipt and exact observations-file SHA-256, score_kind, origin
`independently-reviewed-non-openai`, independent evidence SHA-256 and issued_at/
valid_until (UTC seconds). HMAC input is UTF-8 `fdec-calibration-score-review/v1`
+ NUL + canonical payload JSON using the existing protected 32-byte consent key.
The underlying evidence must verify actual score measurements, reviewed labels
and locally allowed model use. A signature is an operator trust boundary, not
automatic proof of authorship, measurement accuracy or real-world rights.

No signing/approval command is shipped. Provision the authority key privately;
never put it in command arguments or Git. Fresh admission is replayed before
publication and after writing the report, before its checksum receipt. Actual
reports bind artifact/provenance with HMAC domain `fdec-calibration-artifact/v1`.
New output directories only; publication failure preserves prior accepted state.
No raw messages, scores, labels, paths or keys enter diagnostics. Actual outputs
stay private/ignored. No model weights are loaded, trained, downloaded or released.

Rust `schema::calibration::MarginBand` provides the corresponding production
arithmetic, checked construction and abstention reasons. It does not deserialize
or authenticate arbitrary artifact files: callers must first verify the artifact
signature/provenance, model/score convention/language and current authority through
the verified loading path. Missing policy returns Unsupported. `unassessed_result`
constructs a valid advisory abstention with unknown security assessments, unknown
priority, empty topics and review action. No mailbox action is executed.

Actual Qwen/model calibration, deployment validity and confidence measurements
remain unproven. FDEC-015/016 and later D003 gate/review obligations are unchanged.
No source-license weakening, paid service, machine transition or publication is
authorized by this component or by its technical acceptance.
