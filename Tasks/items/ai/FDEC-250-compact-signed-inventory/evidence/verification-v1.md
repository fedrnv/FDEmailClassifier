# FDEC-250 compact signed split verification

Verified published source `fe5227bb44342a1f6edf54ee60820655c5728adc`.
Manual publication followed FDTasks 5.7. The qualified local 5.6 admission
engine verified the source and current rule bindings. Tests ran on Apple
M4 arm64, CPython 3.14.10, PyArrow 26.0.1 and PowerShell 7.7.0, with a
private physical temporary path and en_US.UTF-8.

| Criterion | Local result |
| --- | --- |
| AC-01 | The compact parity fixtures matched the legacy algorithm, including exact 0.80 threshold equality and cross-source component edges. The real private source replay packed 33,131 rows and 20,119,151 fingerprints. Exact grouping checked 2,542,880 candidate pairs and reproduced components of 3,905, 9,387 and 19,839 rows. The isolated 30-million-fingerprint fixture accepted 7,500 rows in three 2,500-row groups. That fixture exercises capacity and grouping with disjoint source cohorts. |
| AC-02 | Real signer, split build and replay entry points passed against isolated compact fixtures. One test corrupted packed bytes and confirmed rejection before creation of a new signature, with the original signed output unchanged. The focused tests also rejected quota excess, bad links, altered metadata, stale and revoked consent. |
| AC-03 | Ordinary v1 receipt replay and existing independent split and trainer fixtures passed. |

| Local command | Result |
| --- | --- |
| `python -m unittest discover -s training/splits -p test_disk_inventory.py -v` | 10 passed |
| `python -m unittest discover -s training/splits -p test_splits.py -v` | 21 passed |
| `python -m unittest discover -s training/finetune/tests -v` | 27 passed |
| `/usr/bin/time -l python "$ITEM/evidence/replay_scale.py" "$PRIVATE_INPUTS" "$PRIVATE_OUTPUT"` | Passed exact unsigned replay of the three verified source projections |
| `python "$ITEM/evidence/verify_scale_boundary.py" "$OWNED_PRIVATE_SCRATCH"` | Passed with exactly 30,000,000 packed fingerprints |

The 33,131-row replay used 670,269,401 bytes of compact storage. Packing
took 50.085 seconds and verified grouping took 178.852 seconds. Maximum
resident set size was 1,860,141,056 bytes, including mapped data. The exact
inventory manifest digest was
`65371c9bba89456991377159874bb5bbe8580ed1647b4d8bb296c4f66cfc024a`.

The scale replay produced an unsigned inventory. Signed split and consent
checks used isolated software fixtures. Owned scale outputs were removed.
The public commit contains the implementation, synthetic tests and
aggregate evidence. No private records or fingerprints are in it. The
existing model consumers still require their own compact integration.
