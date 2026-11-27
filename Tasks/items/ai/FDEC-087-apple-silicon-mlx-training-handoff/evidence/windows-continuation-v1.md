# FDEC-087 Windows development continuation

Use the original Windows development workstation from this point. Mac
training, local quality evaluation and return preparation are complete.
FDEC-087 remains open until the exact trained return is verified on the
original workstation.

## Public checkout and task state

For a new checkout, clone the [public repository](https://github.com/fedrnv/FDEmailClassifier.git).
In an existing checkout, inspect its status and fetch before reconciling
local work. Preserve uncommitted changes and local-only commits. Use a
fast-forward update only when the current branch can be advanced safely.

```powershell
git status --short --branch
git fetch origin main
git log -1 --oneline origin/main
```

Open the updated checkout in the Windows development session. Read
[developer policy 5.7](../../../../FDTasks_5_7_ADOPTION.md) and the
[project development contract](../../../../../DEVELOPMENT.md).
The last verified checkpoint before this handoff was
`972c1b674d42d646bab76d1b0dcbb38012010763`.

| Work | Published evidence or next gate |
| --- | --- |
| FDEC-015 stock benchmark | [Done on the public source](../../FDEC-015-zero-shot-baseline/evidence/public-stock-verification-v1.md) |
| FDEC-016 CUDA | [CPU and software evidence](../../FDEC-016-lora-qlora-trainer/evidence/verification-v2.md). Supported-GPU acceptance remains open. |
| FDEC-087 training and return | [Mac quality results](mac-training-and-held-out-quality-2026-11-27.md) and [verified transfer staging](mac-original-host-staging-2026-11-27.md). Original-host acceptance remains open. |
| D003 integration and review | [FDEC-020 integration gate](../../../quality/FDEC-020-targeted-integration-gate/TASK.md) and [FDEC-021 independent review](../../../quality/FDEC-021-independent-acceptance-review/TASK.md), after their prerequisites. |
| Stable 1.0 and round two | [FDEC-239 stable release](../../../operations/FDEC-239-stable-1-0-release-before-retraining/TASK.md) gates [D013](../../../../epics/FDEC-EPIC-D013/EPIC.md). Use the Mac again for round-two training after that release is verified. |

## FDEC-016 CUDA verification

Inspect the Windows CUDA driver and use the audited Python environment
for the candidate. Set `$Python` to that interpreter. The
[pinned profile](../../../../../training/config/peft-runtime-v1.json) and
existing runtime observer are in the checkout. A driver response is hardware evidence. The
installed Torch build must expose one bfloat16-capable CUDA device.

```powershell
nvidia-smi
& $Python Tasks/items/ai/FDEC-016-lora-qlora-trainer/evidence/observe-local-runtime-v2.py
```

Once the supported CUDA runtime and the current task admission are
verified, run the synthetic GPU checkpoint-and-resume procedure documented
in [FDEC-016 evidence](../../FDEC-016-lora-qlora-trainer/evidence/verification-v2.md).
Record exact source, runtime, command and output. CPU evidence remains
valid for its own tested scope.

## FDEC-087 private receiver

Use the protected `original-workstation-return.zip` delivered privately by
the owner. Set `$PrivateArchive` to the received local path. Check it against SHA-256
`35a7f636c1ddc9a139c93a9c5bd29faffbafaff6ff9220b20edc3d5a1b4a5330`
before extraction into an owner-controlled receiver.

```powershell
(Get-FileHash -Algorithm SHA256 -LiteralPath $PrivateArchive).Hash
```

The archive carries the exact producer source bundle for
`fd4d8fbf539862da2172ccf46509d3e9e19837c5`, the trained return and its
bound metadata. Preserve it independently of the current public
development checkout. Provision the authority keys, exact approved
source runs and stock snapshot separately using protected storage. The
owner's private input index records the exact inputs. Model weights,
raw sources, review data and keys are private. The public repository
contains the implementation, reports and artifact identities.

The producer's compact inventory reader rejects native Windows.
Qualify an original-workstation receiver that can verify the exact
private inventory and authentic source-bound artifacts. Keep the
original signatures and identities. Follow the
[Stage C verification procedure](../../../../../docs/training/MACBOOK_M4_HANDOFF.md)
once those prerequisites are met. Record the receiving evidence before
closing FDEC-087. Public model release remains subject to the
[artifact-specific release policy](../../../../../models/release-policy-v1.json).
