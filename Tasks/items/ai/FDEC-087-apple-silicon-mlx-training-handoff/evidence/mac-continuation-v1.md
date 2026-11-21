# Owner-confirmed Mac continuation

The owner has confirmed the pending numeric-smoke transition and authorized
public source publication. Continue FDEC-087 within D003. Do not repeat that
permission request for the exact existing kit and scope. Actual email training
is not ready: independent training review and held-out gold are still missing.

## Source and private inputs

- Public source identity: 6e6a9eef5cf1fb145db7246e1c83ac310fe2905e.
- Public continuation metadata: the commit containing this evidence and the
  20261121T061242781Z owner-transition-confirmed event, or its descendant containing
  only this task's append-only metadata. Inspect the fetched commit before work.
- Existing kit canonical digest:
  fd10c30d531a09aed3037df1aee5556c22457947dd0330ffc63a9ba4af6b2e76.
- Source bundle SHA-256:
  5243d6ddf6b649ee4606f0e0c84f03b25c81d83a427a2ba3cbb19ec732631ab4.
- On Windows the private store is
  `%LOCALAPPDATA%\FDEmailClassifier\private-FDEC-087-v1`.
  Preserve the whole store, including hidden files, `handoff/.authority`, exact
  source bundle, manifests/receipts and the new genuine `owner-transition.json`.
  Its machine-specific absolute path and authority key are not public evidence.
- Copy this store privately to the Mac; public Git contains none of its private
  authority or activation. The public repository alone cannot activate this kit.
  No transfer has been performed by this Windows session.

Clone the published repository into a new directory, or inspect an existing
checkout and fetch without discarding its work. The published continuation commit
retains the exact code identity above and includes current task metadata. The
portable verifier permits these task-only metadata descendants; do not check out
the older source commit and accidentally discard the current task events. Do not
merge unrelated source changes into the pinned run. The private bundle is an
additional exact source recovery copy, not a replacement for current task state.

## Next executor actions on Mac

1. Read AGENTS.md, DEVELOPMENT.md, Tasks/AGENTS.md, this task, the latest events
   and docs/training/MACBOOK_M4_HANDOFF.md. Verify actual Apple M4/32 GB environment,
   macOS 15+, Python 3.14, pwsh, AC power, thermal conditions and approximately
   20 GiB free disk. Do not claim a Windows test establishes Apple availability.
2. Inspect the owner-copied private store and its hashes. Establish current-user
   mode-0700 storage with no extra macOS ACLs; preserve hidden private files.
   Repair copy permissions only on the proven-owned copy if necessary; never
   rewrite permissions or overwrite a foreign directory. Set PRIVATE_STORE to
   its actual Mac location and FDEC_OWNER_CONFIRMATION_FILE to its genuine
   owner-transition.json. Do not synthesize a new kit/activation or reveal keys.
3. Inspect the kit, recompute fresh FDTasks readiness, then append the appropriate
   Blocked -> InProgress resume event only when environment and private inputs
   are verified. Use a new immutable readiness filename.
4. Run the exact audited tooling bootstrap and actual numerical smoke/resume.
   Record real outcomes and failures. Do not feed Codex emails/labels to a model.

```sh
export FDEC_OWNER_CONFIRMATION_FILE="$PRIVATE_STORE/owner-transition.json"
python3.14 training/finetune/handoff_cli.py inspect --handoff-dir "$PRIVATE_STORE/handoff"
pwsh -NoProfile -File Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/evidence/write-readiness-v2.ps1 -Name mac-readiness-unique.json
python3.14 training/scripts/bootstrap_mlx.py --opt-in --handoff-dir "$PRIVATE_STORE/handoff"
.venv/mlx/bin/python training/finetune/train.py mlx-check --opt-in --handoff-dir "$PRIVATE_STORE/handoff" --output-dir "$PRIVATE_STORE/mac-numeric-return"
```

Bootstrap requires the copied original kit/approval and actual supported host;
the commands will fail closed if private material or host prerequisites are absent.
Do not interpret a missing transfer as a reason to weaken owner verification.
Preserve original Windows storage for verified return. Follow the full runbook
for protected return verification; a numeric return never announces completed
email training, GGUF acceptance or public-weight permission. FDEC-015 baseline
and FDEC-016 original CUDA obligations remain separate and incomplete.
