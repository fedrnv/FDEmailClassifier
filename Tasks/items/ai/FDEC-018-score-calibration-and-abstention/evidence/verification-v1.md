# FDEC-018 acceptance verification

Candidate: `9181762bcc73b1a884a70a3144641f65a4bce9e9`.
Source-state SHA-256:
`c2abad4cd2e7ebc9db6112796954668285f4fdb343057fecdba4e1dfef370188`.
FDTasks policy SHA-256:
`ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403`.
Initial and frozen execute admissions passed. The immutable task is unchanged.

| Original criterion | Actual verification | Result |
| --- | --- | --- |
| AC-01: threshold boundaries and calibration stability on held-out fixtures | Validation-only fit, exact-fraction brute-force threshold oracle across 30 deterministic score variations, test score/label/language perturbations, row-order invariance, shared Python/Rust cutoff vectors and structured numerical report | PASS |
| AC-02: invalid/missing input preserves state and fails explicitly | Missing/unknown/overlapping scores, low support, NaN/boolean score rejection, bad roles, group/record leakage, model drift, authenticated observation mutation, current-consent revocation and existing output preservation | PASS |

Final command: `powershell -NoProfile -File training/calibration/test-calibration.ps1`.
Monitor `bc7f501e-64ce-407e-a2a3-57a933c78d3e`, exit zero: eight Python tests in
24.193 seconds and seven Rust tests, including all four existing schema tests.
Environment: CPython 3.14.5, pinned PyArrow 26.0.1 and Rust 1.98.0, offline cached
Rust dependencies. Full output is `test-output-v1.txt`. The exploratory suite also
passed eight Python/seven Rust tests before freeze. An initial formatting check
reported the newly added Rust file unformatted; rustfmt was applied and the final
workspace formatting check passed before freeze. No hosted tests were used.

The frozen numerical report command ran at this candidate, monitor
`d3904cb9-b7d7-42bc-b0c0-8acd7283ea19`, exit zero; see `fixture-run-v1.txt`.
The report/receipt were copied byte-for-byte from the ignored private output into
`fixture-report-v1.json` and `fixture-receipt-v1.json`, with matching SHA-256 in
`result-v1.json`. Input fixture SHA-256 is
`523535d05151555b6342209b490a09d540e57b6dda056588ba193623de52f180`.

The report is explicitly `software-numerical-fixture-only` and records no actual
model execution, no actual model calibration and no estimated probabilities.
These technical numerical targets are not actual training/evaluation labels for
email content; no model consumes them and no model weights are created. Acceptance
proves the original held-out-fixture software criterion, not calibration validity
for Qwen or a deployment/safety threshold.

For the work-topic fixture the validation F1 optimum is threshold 0, while the
empirical decision cuts are -1 and 2. The independently scaled phishing cuts are
8 and 14. Exact cutoffs decide inclusively; interior scores and out-of-observed-
range values abstain. German insufficient support and unobserved labels remain
unsupported. Test targets/scores/languages do not change the fitted artifact.
The held-out work-topic report has 4 eligible, 2 decided/correct, 2 abstained,
coverage 1/2 and correct fraction 1/2; no abstention is hidden as a correct answer.
The production default needs 20 samples per class/tail; only the explicit numeric
fixture uses two. Pure tails are empirical support, not statistical confidence.

The actual-score consumer replays the unchanged D002 source bytes and annotations,
license/origin checks, current signed consent and grouped split, then verifies a
protected current independent score/label-review HMAC binding exact observations,
model/score convention and evidence identity. The integration test actually runs
these checks under isolated counterfactual policies. Changed observation bytes and
new revocation reject. Simulated reviews/source grants are not real-world rights
or measurement proof. Both Codex packs remain forbidden for actual use, and the
existing OpenAI-origin denial is also applied to measured-score producer identity.
No automatic review signer or CLI trust/policy override exists.

Rust adds checked per-label margin arithmetic and explicit abstention reasons,
plus a valid unassessed classification constructor. MarginBand does not authenticate
arbitrary artifact files: policy loading must verify signature/current authority,
model, score-kind and language first. Existing classification-v1 serialization is
unchanged and rejects added probability fields. Mutually exclusive priority/action
resolution remains a caller obligation; conflicting decisions must abstain rather
than invent confidence. The current stock hard-label JSON output has no measured
margins, so actual model calibration remains unsupported.

## Boundaries and continuation

Existing dataset licenses, origin policies, ingestion, split/consent, baseline,
trainer, evaluation suite and JSON schema files are unchanged. No probabilities,
actual model quality, phishing reliability, legal clearance for new data/weights,
model/runtime installation, training, downloads, paid host, Mac handoff, release
allocation or publication are claimed. FDEC-015/FDEC-016 stay incomplete; D003
still requires its later gate and independent review. No task outcome was amended.

Temporary counterfactual fixtures were cleaned up through guarded paths. The
ignored numerical output is retained for reproducibility alongside metadata-only
evidence copies. No raw email, private data, secrets or weights enter Git.
Pre-existing untracked `.idea/` is untouched. Next sequential task: FDEC-019.
