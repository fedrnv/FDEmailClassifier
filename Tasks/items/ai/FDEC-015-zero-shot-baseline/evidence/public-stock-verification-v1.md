# FDEC-015 current-source stock benchmark

Verified public source `bd1b8108f381d40be95d88fe9eb8810fda6b71bb`.
The production stock Qwen3-0.6B CLI ran on the Apple M4 CPU with
CPython 3.14.10, Torch 2.15.0 and Transformers 5.23.0. The pinned stock
prompt used deterministic non-thinking decoding. Manual publication
followed FDTasks 5.7 and the local admission validator used its qualified
5.6 policy.

The production admission rechecked current rights, original review
provenance and consent. The preflight replay independently reproduced
277 historical record identities and all fingerprint bytes. Every group
and role was preserved, with 57 train, 166 validation and 54 test rows.
The authoritative 54-row annotation file was byte-identical. Rebinding
the single public Gemma receipt changed only the dependent provenance
and authority digests. All 277 original grants and their expiry were
retained. The original authority anchors were checked before and after
execution and remain preserved. Only test rows reached the stock model.

| Criterion | Local result |
| --- | --- |
| AC-01 | The production CLI committed a real report for 54 held-out records in four languages. The authenticated report includes all 54 invalid responses in the metrics. The protected receipt, exact implementation hash, fixed prompt, annotation identity and signed authority bindings reproduced at readback. |
| AC-02 | All 11 local baseline tests passed. They exercise missing inputs, provenance, changed permissions, invalid responses and output rollback in isolated fixtures. The negative tests did not run the stock model. |

| Measurement | Stock result |
| --- | --- |
| Schema-valid responses | 0 of 54 |
| Correct priority | 0 of 53 reviewed |
| Correct action | 0 of 23 reviewed |
| Topic micro-F1 | 0.000 |
| Topic supported macro-F1 | 0.000 |

The measured result reproduces the historical stock outcome on the same
cohort. It makes no claim about quality beyond these reviewed examples.

```sh
python -B training/baseline/baseline.py evaluate --opt-in \
  --inventory "$PRIVATE_INVENTORY" --consent "$PRIVATE_CONSENT" \
  --split-dir "$PRIVATE_SPLIT" --annotations "$REVIEWED_GOLD" \
  --model-dir "$PINNED_STOCK_MODEL" --output-dir "$NEW_PRIVATE_RESULT" \
  --source-run "$TRIAGE_RUN" --source-run "$SINABIS_RUN" --source-run "$GEMMA_RUN"
pwsh -NoProfile -File training/baseline/test-baseline.ps1 -Python "$PINNED_PYTHON"
```

| Evidence | SHA-256 |
| --- | --- |
| Current stock report | `9b05d162f9cda47c7c2f880100aee1bd4ebd9362504e9fedd927962783426955` |
| Commit marker | `1f84209c4ee79fcab76cd390cf62781d819880cba3f03856a71ba554b075b69b` |
| Runtime implementation | `6fc94d0d92af9b4a6fbc62c14ac6c9154dead090dd216ac327438ebfe317779d` |
| Frozen stock prompt | `092f1f97469ff380c6c9207813cdcbd9668f67f618ea5b0577f13cbbc2b46a67` |
| Protected preflight authority readback | `ddfaa22149fb3a80de5260d617e7cd45346af7b6f159b7c2dd4abcea9ad0bf9a` |

The local measurement took 293.37 seconds. Software fixtures cleaned up
their owned temporary inputs. Raw emails, labels, authority records and
model artifacts remain in protected local storage.
