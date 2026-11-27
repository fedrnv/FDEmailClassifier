# FDEC-249 guarded Gemma source replay

The exact published source was `da5a64059e3870a02de06f718824863ea7c122a7`.
Manual publication followed FDTasks 5.7 and the qualified local 5.6
admission engine verified the source. The checks ran on Apple Silicon
with CPython 3.14.10, PyArrow 26.0.1 and PowerShell 7.7.0.

| Criterion | Local result |
| --- | --- |
| AC-01 | The production CLI `python training/augmentation/gemma_source.py --opt-in --source <pinned-private-artifact> --output-dir <new-private-run>` produced 19,839 projected rows. The production `training_boundary.admit_training_run` reopened the exact source bytes and receipt, reproduced the projection, and required signed split and consent. In the focused fixture the real grouped split and trainer input code kept the entire source in a single partition. |
| AC-02 | The direct fixture rejected modified raw bytes, receipt, each of the two FDEC-248 audit files and revoked consent. The fixture excludes candidate rows with a contact pattern or a noncanonical output shape before training inputs are assembled. |
| AC-03 | The existing Sinabis and ordinary ingestion trainer fixtures, signed split suite and stock baseline software suite passed. |

| Local test | Outcome |
| --- | --- |
| `python -m unittest discover -s training/finetune/tests -p test_gemma_admission.py -v` | 7 passed |
| `python -m unittest discover -s training/finetune/tests -p test_finetune.py -v` | 20 passed |
| `python -m unittest discover -s training/splits -p test_splits.py -v` | 21 passed |
| `pwsh -NoProfile -File training/baseline/test-baseline.ps1 -Python <pinned-python>` | 11 passed, software checks only |

The replay binds the public FDEC-248 report and aggregate. Projection
SHA-256 is `636d509f050ddbff08094a0b1a84562167dbea83b12a628af6a8d670b5a8196a`.
Exact new run receipt SHA-256 is
`ee8395f7f7ea9ee2ced60920b8b3167e7c7104d6124ac497ba7c8736d6a4542c`.
The new receipt reflects the public audit binding. Prior receipts are
historical evidence for their own implementations.

The replay copy and temporary software fixtures stayed in owner-only
storage. No labels were generated and no model ran. Actual cohort
selection, current signed consent and independent gold remain separate
requirements for a real benchmark.
