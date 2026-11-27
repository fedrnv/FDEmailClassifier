# FDEC-247 reviewed Sinabis source replay

The exact public candidate was `54193e8aeba21793b5d1cf88a96f01c4221e1386`.
All five implementation and test files match the previously measured
replay implementation. Manual publication followed FDTasks 5.7. Local
admission used the qualified 5.6 engine and its existing policy pin.
Verification ran locally on Apple Silicon with CPython 3.14.10, PyArrow
26.0.1 and PowerShell 7.7.0.

| Criterion | Local result |
| --- | --- |
| AC-01 | The production CLI `python training/augmentation/sinabis_source.py --opt-in --source <pinned-private-artifact> --output-dir <new-private-run>` wrote the admitted receipt. The shared guard `training_boundary.admit_training_run` reopened that exact run, reproduced 9,387 approved rows and required split and consent. The trainer integration fixture verified the signed inventory, consent and component and Oil family grouping. |
| AC-02 | The focused Sinabis preparation and trainer suites rejected changed source, receipt and lineage, unapproved origin and revoked consent. The preparation fixture verified that failure preserved existing inputs. |
| AC-03 | The existing independent split and trainer suites passed, including ordinary ingestion, signed splits, consent expiry and reproducible grouping. |

| Local command | Outcome |
| --- | --- |
| `python -m unittest discover -s training/augmentation -p test_sinabis.py -v` | 23 passed |
| `python -m unittest discover -s training/splits -p test_splits.py -v` | 21 passed |
| `python -m unittest discover -s training/finetune/tests -p test_finetune.py -v` | 20 passed |

Projection SHA-256
`ca364b7cb425383d11460d8727e7f91d7fb9385dcfe3fdf836fa881d546d6f17`.
Exact run receipt SHA-256
`3f2a0e48784f82ef4e939a54bac23fd18f6be39e1f9c26ebdf60fb80340e9d66`.

All software fixtures used temporary storage. The replay copy stayed in an
owned private test directory. No labels were produced and no model was run.
The pinned source profile, existing audits and public release policy were
preserved.
