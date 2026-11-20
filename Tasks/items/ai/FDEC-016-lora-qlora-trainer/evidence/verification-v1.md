# FDEC-016 partial implementation verification

Tested source: `483326f26f95bd8dff93cb89ff916a54addec01f`.
FDTasks policy SHA-256:
`ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403`.
The accepted task and its supported-GPU acceptance criterion remain unchanged.
This is partial evidence, not a closure proof, scope amendment or version request.

| Criterion | Actual evidence | Status |
| --- | --- | --- |
| AC-01: deterministic PyTorch/PEFT trainer, checkpoint/resume on supported GPU | LoRA/QLoRA configuration, input admission, private authenticated state, deterministic cursor/RNG handling, restricted decoder and actual numerical GPU-check command implemented. No supported-GPU run passed; actual PyTorch/PEFT/QLoRA integration is unverified. | NOT FULFILLED |
| AC-02: invalid/missing input preserves state and fails explicitly | 13 software tests cover config bounds, missing input before engine initialization, source replay, train/test exclusion, partial/unknown labels, reviewed prompt, review signatures, current-consent revocation, checkpoint integrity/context/HMAC, decoder ordering, write rollback, resume orchestration and failed final-publication recovery. | SOFTWARE CHECKS PASS; actual GPU failure paths unverified |

Final command: `powershell -NoProfile -File training/finetune/test-finetune.ps1`.
Monitor `0ec62302-855d-4a5f-90b0-2905ab6effe0`, exit zero, 13 tests in 52.862
seconds. Full output is `test-output-v1.txt`. The software suite deliberately ends
`SUPPORTED_GPU_ACCEPTANCE=NOT_RUN`. It cannot close AC-01.

An earlier frozen source `d2a8faceb7bd3b63a460346264fab2f036020a9e` passed 13
tests in 52.652 seconds, monitor `a716f84c-d083-4feb-b534-a8c6499cb712`.
Final-publication staging/flush/atomic rename and its failure injection were then
added, followed by the complete 13-test rerun above. An exploratory 11-test run and
focused orchestration check also passed before that freeze; they are not used as
proof of the final source. No failed software check is being hidden or relabeled.

The actual GPU command was attempted at `d2a8faceb7bd3b63a460346264fab2f036020a9e`,
monitor `d16f73a0-0f23-49b9-81e4-871b71f27b35`, exit 2, static diagnostic
`trainer_execution_rejected`; see `gpu-attempt-v1.txt`. It did not reach tensor
construction/training because the required packages are not installed. The
current display-controller query exposes only Microsoft Basic Display Adapter;
`nvidia-smi` is unavailable. No compatible CUDA device/runtime is confirmed.
The result is unavailable GPU acceptance, not a passed test or measured GPU defect.

## Coverage and honest limits

Dataset tests actually execute the existing rights guard, source-byte/annotation
replay and grouped-split/consent verifier using isolated counterfactual policies.
They use generated software tokens and simulated independent reviews, not real
dataset rights, human authorship or canonical annotation evidence. No actual
language model consumes their email fixtures or labels. Both Codex packs retain
their commercial-training/evaluation prohibitions. Existing rights/origin/split
implementation and policies are unchanged by FDEC-016; only new trainer files and
two new config profiles were added to those functional areas.

The checkpoint arithmetic oracle and runner/tokenizer doubles exercise state,
masking, integrity and publication mechanics without PyTorch. They do not establish
native checkpoint serialization, exact GPU resume or actual model training.
The dedicated GPU command creates only a disposable, tiny randomly initialized
Qwen3 architecture and seeded random numerical tokens; it uses no natural-language
emails, category labels, stock tensors or fixture packs. Its default requires
both LoRA and QLoRA state equality, including optimizer and RNG. No actual pass
exists for either path. This accepted technical-fixture test is separate from
commercial/email training and cannot grant rights to a later dataset or model.

Actual email training additionally lacks admitted private train artifacts with
fully reviewed non-OpenAI labels, an independently reviewed non-OpenAI prompt and
current consent/review authority. Whole-JSON v1 rejects partial masks instead of
fabricating unknown heads. No training prompt, email content or training gold is
provided by Codex for actual model use. The baseline inference prompt is not used
as SFT content. Source labels are never automatically promoted to canonical truth.

Runtime observations pin public metadata candidates, not installed wheels or
interoperability. Safetensors' null PyPI license field is explicitly unresolved at
the wheel level; floating upstream documentation is not a completed artifact
audit. No public runtime/model/dataset redistribution is approved. No transformer
packages or stock tensors were installed/downloaded, actual training performed,
paid service used, Mac transition made or model published in this turn.

## Continuation

FDEC-016 remains incomplete, blocked on the actual supported-GPU checkpoint/resume
acceptance run. Provision a compatible, audited runtime on an already authorized
supported host and run the real command; preserve the original criterion. The
Mac/MLX task FDEC-087 still depends on FDEC-016 and requires its own explicit
operator-confirmed transition. No dependency or handoff approval is bypassed here.
The global development goal can continue: FDEC-017 has no dependency on FDEC-016
and is the next separate turn. D003 remains the sole Active development Epic;
FDEC-015, FDEC-016 and later gate/review obligations are not waived.

Temporary numerical and counterfactual-policy fixtures were cleaned up through
guarded temporary paths. No private text, secrets or weights were committed.
Pre-existing untracked `.idea/` remains untouched. Final ledger validation after
the blocked-status event is recorded separately.
