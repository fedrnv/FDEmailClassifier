# FDEC-251 compact model consumer verification

Verified published source `86ec048f98095384d69f88d2253755d573a0ab0d`.
Manual publication followed FDTasks 5.7. The local 5.6 admission engine
verified the exact source and current rule bindings. Tests ran on Apple
Silicon with CPython 3.14.10 and PowerShell 7.7.0. The pinned MLX environment
ran the MLX fixtures and the export environment supplied the CPU and GGUF
test dependencies.

| Criterion | Local result |
| --- | --- |
| AC-01 | The focused compact fixture built and verified a private signed inventory, replayed authentic source projections and kept train and test IDs disjoint. The handoff kit, checkpoint context, training provenance and both stock baseline and evaluation reports used the same compact digest. Only model output generation was substituted. |
| AC-02 | A structurally valid signed inventory containing a structurally valid but incorrect full-width fingerprint failed both admission paths. Replacing current consent invalidated both existing snapshots. The fixture did not invoke a real model. |
| AC-03 | Existing v1 and compact split, training, baseline, evaluation, calibration and export fixtures passed. The return attribution test confirmed identical source notices from v1 and compact metadata, including the verified Sinabis audit, and refused a missing notice. The MLX handoff fixture explicitly models an unsupported architecture to verify that boundary on Apple Silicon. |

| Local command | Outcome |
| --- | --- |
| `python -m unittest discover -s training/finetune/tests -v` | 29 passed |
| `python -m unittest discover -s training/finetune/mlx_tests -v` | 15 passed in the pinned MLX environment |
| `python -m unittest discover -s training/splits -v` | 31 passed |
| `python -m unittest discover -s training/baseline/tests -v` | 11 passed |
| `python -m unittest discover -s training/eval/tests -v` | 10 passed |
| `python -m unittest discover -s training/calibration/tests -v` | 9 passed |
| `python -m unittest discover -s training/export/tests -v` | 6 passed in the pinned export environment |

The first MLX fixture invocation used the environment without MLX packages.
In the correct environment the old fixture revealed that it implicitly
assumed a non-Apple host. The explicit architecture fixture now exercises
the same production denial on the Mac.

All private software fixtures were disposable. This change enables
authenticated compact input and provenance recording. Real cohort approval,
actual benchmark claims and release rights retain their separate gates.
