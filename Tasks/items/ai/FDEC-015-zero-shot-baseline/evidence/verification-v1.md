# FDEC-015 partial implementation verification

Tested source: `5c3d286041a2f6baf49723c79b621637fedbcf07`.
FDTasks policy SHA-256:
`ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403`.
The original accepted task and its benchmark outcome remain unchanged. No scope
amendment, closure proof or task-closed request is asserted by this evidence.

| Criterion | Actual observation | Status |
| --- | --- | --- |
| AC-01: benchmark stock Qwen on a multilingual held-out set and save metrics | Fixed prompt, guarded runner, snapshot verification and masked metrics implemented; 11 software tests pass. No admitted corpus, independent gold or current consent/review anchor; no model tensors downloaded, actual model loaded or benchmark executed. | NOT FULFILLED |
| AC-02: invalid/missing inputs preserve state and fail explicitly | Parser, masks, source-byte replay, test-only joins, origin-policy changes, signed review bindings/expiry, current-consent revocation, fake snapshot, token budget, invalid/truncated model output and output rollback/preservation exercised. | SOFTWARE CHECKS PASS; real-runtime integration unverified |

The final focused run is recorded verbatim in `test-output-v1.txt`, monitor
`fb0e7e44-8ff0-4c98-afa1-17c8cc7f6168`, exit zero, 11 tests in 72.096 seconds.
Tests use the existing isolated D002 pipeline fixture for three counterfactual
MIT sources and signed consent. The source/license guard and split verifier are
actually executed. The signed review and language declarations in those fixtures
are simulated technical metadata, not independent real-world annotation evidence.
No actual language model consumes their generated email contents or labels.
The adapter test is a protocol double; actual PyTorch/Transformers integration,
runtime compatibility, CPU throughput and Qwen quality have not been measured.

The earlier frozen run at `cbd72d1cd921718510c3cc7e95306ab7ac969d38` failed one
new test-double setup because of a Python class scope name error. Its complete
output is retained as `test-failure-v1.txt`; the test was corrected and all 11
checks rerun. An earlier exploratory nine-test run also passed but is not used
as acceptance of this later source.

Repository validation with absolute root passed for 114 records at source
`cbd72d1cd921718510c3cc7e95306ab7ac969d38`, monitor
`97424d1d-34e4-4bc6-bfbe-8cd2f91433cd`, exit zero. The first invocation with
relative `-Root .` failed `Incomplete planning history` because the existing
migration validator compares absolute history paths with supplied root paths.
The corrected invocation used `-Root C:\GitHub\FDEmailClassifier`; no validator,
accepted migration or protected dataset policy was changed. Final ledger
validation is recorded separately after the task status event is added.

## Outstanding independent inputs

The checkout has no admitted multilingual held-out inventory with independently
reviewed non-OpenAI canonical labels and currently activated signed consent and
label-review authority. Sinabis preparation is not such a corpus: it has no
independent canonical gold and the retained source family does not provide three
independent groups under the accepted split policy. Automatically mapped source
labels and Codex-created labels are not promoted to evaluation truth. Both Codex
fixture packs remain barred from actual training and evaluation. This is a
specific missing-input observation, not a claim that no lawful source can exist.

An independent preparer/operator must supply those reviewed private artifacts
through the existing audited source and authority processes. A compatible local
runtime and verified pinned stock snapshot then need provisioning and an actual
run. The model profile and audit are preparation evidence only; they do not
approve public distribution of any downloaded or fine-tuned weights. No expense,
VPS provisioning, remote execution, Mac switch, training or publication occurred.
Software tests require no GPU VPS. A hardware decision for actual training remains
subject to the accepted operator-confirmed Mac/MLX handoff task.

## Continuation and cleanup

FDEC-015 remains incomplete and its actual benchmark is blocked on the independent
data/annotation/authority inputs above. D003 remains the sole Active development
Epic. FDEC-016 has no dependency on FDEC-015 and may proceed next turn within its
own immutable scope; its supported-GPU acceptance must not be fabricated either.
This does not remove FDEC-015 from the later D003 gate or authorize Epic closure.
All temporary software fixtures were cleaned up by guarded temporary-directory
cleanup. No private corpus, secrets, model weights or raw model responses enter
Git. Pre-existing `.idea/` remains untouched and untracked.
