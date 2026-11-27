# FDEC-015 stock Qwen baseline observation

The protected Mac run executed the production stock Qwen3-0.6B benchmark
at source `1c2d1d36805947b1f691ef34aed252b80fc06554`. It used model
revision `c1899de289a04d12100db370d81485cdf75e47ca`, a fixed prompt and
deterministic non-thinking decoding on an Apple M4 CPU. Current consent,
source rights and independently reviewed labels were checked on the exact
54-email held-out partition in four languages.

| Measure | Stock Qwen, stock prompt | Trained MLX, training prompt |
| --- | ---: | ---: |
| Schema-valid outputs | 0 of 54 | 54 of 54 |
| Correct priority | 0 of 53 | 46 of 53 |
| Correct action | 0 of 23 | 1 of 23 |
| Topic micro-F1 | 0.000 | 0.667 |
| Supported-topic macro-F1 | 0.000 | 0.250 |

The two configurations used the same reviewed test assignments and labels.
Their prompts and execution runtimes differed. This comparison measures the
two configurations and cannot isolate the effect of the adapter. The holdout
contained no reviewed positive spam, phishing or malware examples. It is
separate from the later 1,653-email final test.

The readback authenticated the report and its commit marker, verified the
exact implementation hash from the historical source tree and reconciled the
input-identity commitments and metric denominators. The historical baseline
software suite passed its 11 local tests, including missing consent, changed
inputs, invalid output and rollback cases. The production measurement ran
separately from that suite.

| Evidence | SHA-256 |
| --- | --- |
| Historical stock benchmark report | `5d9998e49b07ba2fbf4f73cfb383a85dd82d8f331436a21fd95ce5251d81db91` |
| Benchmark commit marker | `703d5ba8a23322c2ef22caf999c9eeed5e867134b694a5bb97f13c3e9d923cc9` |
| Measured implementation | `6fc94d0d92af9b4a6fbc62c14ac6c9154dead090dd216ac327438ebfe317779d` |
| Frozen stock prompt | `092f1f97469ff380c6c9207813cdcbd9668f67f618ea5b0577f13cbbc2b46a67` |

## Public source reconciliation

The public source inspected at `d92ee452eed08c183471f0931f0221d8ad41f310`
accepts the earlier JSON inventory. The measured configuration used the compact
inventory, its authenticated split and source replay, and the later source
admission code. These are functional input and rights-check differences.
On this public source, `training/baseline/test-baseline.ps1` passed all 11
local software tests with CPython 3.14. No real model was initialized in
that check.
The historical result remains valid for its recorded source. Verification on the
public candidate requires reconciliation of those contracts and current approved
inputs. The result confers no public rights to email records, labels or weights.
