# FDEC-087 Stage A partial verification

The updated upstream plan is already an ancestor of the local project. Git fetch
observed origin/main at 0ea1e407e32eb2671226ab9f8430e54e4207d6b7, the Mac
training/handoff plan; HEAD a8f98af was 116 commits ahead, zero behind. The GitHub
issue search returned no issues. No merge, reset, push or task-spec rewrite occurred.
Resume the accepted FDEC-087 Stage A after FDEC-101, within D003.

Exact commands, monitor identities, outcomes and earlier corrected failures are
in software-verification-v1.json and software-test-output-v1.txt. No unchanged
failed candidate was retried. The source commit containing these records binds
the tested code; a subsequent readiness/pre-Mac checkpoint binds its exact SHA.

| Criterion | Current measured evidence | Remaining |
| --- | --- | --- |
| AC-01 | Existing trainer 14 tests and actual numerical CPU PEFT resume PASS; pinned MLX configuration/full-state codec implemented | Real Apple MLX numerical LoRA/resume unperformed; explicit hardware/owner wait |
| AC-02 | 13-test handoff suite checks exact bundle/source, external owner binding and absent-owner denial before hardware; detailed runbook | Real source kit/checkpoint follows source freeze; no actual device switch |
| AC-03 | Actual source admission preserved; absent inputs/owner, wrong scope, future date, non-Apple and unsupported MLX QLoRA reject; no Torch/MLX import merely selecting protocol | Actual missing-MLX diagnostic on Apple remains unmeasured |
| AC-04 | Numerical round-trip simulation decodes signed native checkpoint, checks PEFT mathematical transpose; tampering/extra files/foreign context/wrong authority/revocation reject | Real Mac training/evaluation/private transfer/GGUF parity and full post-Mac evidence unperformed |
| AC-05 | Lazy MLX selectable without Torch imports; audited 40-wheel Mac closure excludes Torch/PEFT; original default PyTorch compatibility PASS | Actual Mac execution remains necessary |

The new actual MLX train/evaluate/collect/primary export path is implemented but
has not consumed real email data or run on Apple. Structural PEFT conversion is
not a GGUF compatibility result. The original FDEC-016 CUDA requirement and
FDEC-015 independent multilingual baseline remain incomplete. The release registry
stays default deny. Neither Codex email fixture pack is used by an actual model.
Only seeded numerical tokens reach the CPU PEFT test; test emails/labels are
isolated admission/orchestration doubles, not model training/evaluation inputs.

The new public source is Apache-2.0 project code, not an assertion of permission
to train on Codex text. Mac tool licenses cover exact local software use only.
Current independently approved training review/held-out gold are missing. No
weights, datasets, owner activation, private authority or credentials are in Git.
FDEC-087 is not Done and has no closure/version request.
