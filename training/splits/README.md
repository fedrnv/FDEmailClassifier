# Leakage-safe grouped splits v1

`split_data.py` implements training-only partitioning of a private, signed
inventory. It emits train/validation/test references, not message contents.
The core Rust classification API is unchanged. There is no training, deployment,
corpus download, source-license expansion or hosted acceptance in this tool.

## Admission and preparation

A trusted data preparer first verifies FDEC-009's actual ingestion run: its
completion receipt, pinned raw-source bytes, normalized records hash and current
rights. The `prepare_record(normalized, receipt, consent_id=..., thread_id=...,
family_ids=...)` helper checks normalization/content identity, source consistency
and source-row provenance and computes versioned fingerprints. It does not
independently reread the entire upstream artifact or authenticate external facts.
The signed inventory attests the preparer's verified derivation; a random caller
cannot substitute that attestation with an unbound file hash or permission flag.

An inventory is `fdec-split-inventory/v1` with the exact `normalization_version`,
`feature_policy` and a nonempty `records` array. Each record contains only:

| Field | Meaning |
| --- | --- |
| record_id | SHA256 of source identity, normalized content ID and source-row indexes |
| content_sha256 | Normalized content ID from ingestion |
| source | Exact dataset_id/revision/artifact/sha256 identity |
| provenance | Bound ingestion receipt, normalized record stream and contributing source rows |
| thread_id | Shared opaque SHA256-sized thread identifier, or null when genuinely unavailable |
| family_ids | Shared opaque lineage IDs for translations, template families or other known derivations |
| shingles | Sorted unique SHA256 fingerprints from the declared feature algorithm |
| consent_id | Opaque identifier for the data owner's recorded permission basis |

Raw subjects, bodies, addresses and arbitrary fields are rejected in inventories.
The preparer must preserve known conversation/translation/family relationships,
including across sources; missing metadata is not inferred from arbitrary text.
For private identifiers, use stable keyed pseudonyms in the preparation system
and keep the key and original identity mapping out of Git and logs. Fingerprints
and content hashes are private metadata, not anonymization or a PII sanitizer.

At build and verification time the tool independently checks every source
against the current audited inclusion guard for both commercial_training and
evaluation. Consent never overrides a source-license denial or changed artifact.
The sole augmentation pack in blocked FDEC-011 remains fixture-only and cannot
be admitted as a source by this tool. Software fixtures use isolated test policy
roots; the production CLI has no policy-root or allowlist override.

## Consent authority

See [the consent ledger contract](../manifests/README.md). Every inventory is
bound by an authorized HMAC-SHA256 ledger with explicit per-record evidence,
purposes, expiry and granted/revoked status. Missing grants, expired grants,
revocation or absence of either training/evaluation purpose exclude the entire
connected component, including related copies and source peers. This is a
conservative quarantine, not deletion of historical artifacts or an assertion
that an already trained model has forgotten a record.

The protected current authority anchor is
`training/data/consent/current.json`. Both build and verification require the
supplied signed ledger to match that anchor. An archived, still-signed grant
cannot override a later activated revocation. A missing, invalid, future or
expired authority ledger fails closed. The complete inventory is bound by its
canonical JSON SHA256, so a permission snapshot cannot silently authorize a
different dataset. Grant evidence is a private external record hash; this tool
does not decide whether a human's underlying permission is legally sufficient.

## Grouping and deterministic allocation

First, union all records connected by any of these relations:

1. Same upstream dataset ID, across artifacts/revisions in the inventory.
2. Same known thread identifier.
3. Same normalized content hash.
4. Any shared lineage/template/translation family identifier.
5. Near-duplicate fingerprint Jaccard similarity of at least 80 percent.

Near-duplicate features apply Unicode NFKC and case folding, retain alphanumeric
characters, and hash every unique five-character shingle (or the whole shorter
string). This works without a whitespace tokenizer and has a versioned Unicode
database identity. Exact integer arithmetic tests the threshold. Candidate
indexing considers every pair with a shared shingle, skips already connected
source components and fails explicitly on resource limits. It does not silently
sample, truncate or discard comparisons. This declared detector is not a proof
that arbitrary semantic paraphrases are unrelated.

Relations are transitive: a thread link followed by a near-duplicate link is
one indivisible group. A withdrawal anywhere in a component quarantines it all.
At least three admitted independent groups are needed for three nonempty
splits; one-source corpora therefore cannot be divided under this policy. More
rows from that same source do not solve the independence requirement. Do not
fake independent source IDs to make the check pass.

Groups are ranked by size and a seeded deterministic hash. A greedy squared
row-count error objective assigns whole groups while reserving enough groups
to fill all three roles. Default ratios are 80/10/10; the Python API accepts
positive integer percentages summing to 100. Large groups can prevent exact
ratios. Manifests report actual counts and signed hundredths-of-row target error
instead of splitting a group or claiming stratification. Label balancing is not
implemented or implied. Seed changes can change tie assignments, not group
membership. Input order does not affect grouping; inventory ordering is itself
signed and cannot be altered under an old ledger.

Limits are 100,000 records, 4,096 unique features per record, 2,000,000 total
features, 2,000,000 necessary cross-component comparisons and 250 MB per JSON
input. Exceeding a budget rejects without output. Larger runs need an explicitly
reviewed implementation/policy change; unsafe pre-partitioning is not a fallback.

## Immutable manifests and current verification

An explicit build creates a new private run directory exclusively, writes
`manifest.json`, then a checksum-bound `receipt.json` last. Existing runs are
never overwritten. The manifest records inventory/consent/source grant hashes,
generator implementation, feature policy, seed/ratios, counts, assignments,
group IDs and excluded record IDs. It contains no raw messages, feature lists,
consent evidence text, names or local input paths. The same inputs, source
decisions and implementation give identical bytes, with no timestamp/path noise.

Normal write failures remove only the newly owned incomplete run and preserve
earlier artifacts. A crash can leave an incomplete private directory; consumers
must require and verify its receipt. Inside Git, output is allowed only in
ignored, untracked training/data or training/outputs directories; links reject.
Nothing is automatically redistributed or published.

`verify()` checks the receipt against the exact bytes it parses, recomputes the
entire current-source/current-consent plan, and compares every assignment and
provenance field. Changing assignments, counts or exclusions fails even if an
attacker recomputes the file checksum. Updated consent requires a new manifest;
old artifacts remain historical and immutable. Rights/consent revocation can
invalidate use without modifying the old files.

For consumption call `verify(..., include_manifest=True)` and use its returned
validated manifest snapshot rather than rereading a mutable file. Current
consent is checked again before returning and before a build publishes its
receipt. Training consumers must revalidate at data-use/checkpoint boundaries
and stop when authority changes; a single past verification does not grant
permanent permission. The current authority directory and key custody are trusted
inputs, not a defense against a malicious administrator who controls both.

## Commands and local tests

The authorized environment supplies `FDEC_CONSENT_KEY` as a private 32-byte key
encoded in hexadecimal. Never commit it, print it or put it into a command line.
After a data owner has signed/activated the inventory's actual permissions:

```powershell
py -3.14 training/splits/split_cli.py build `
  --inventory training/data/prepared/inventory.json `
  --consent training/data/consent/current.json `
  --output-dir training/outputs/splits-001 --seed 27 --opt-in
py -3.14 training/splits/split_cli.py verify `
  --inventory training/data/prepared/inventory.json `
  --consent training/data/consent/current.json `
  --output-dir training/outputs/splits-001
```

CLI output is receipt counts/hashes only; diagnostics are static codes. The
production CLI uses the current UTC clock and exposes no historical-time bypass.
Run `powershell -NoProfile -File training/splits/test-splits.ps1` for local
synthetic software fixtures, including actual source-guard integration,
transitive leakage, consent replay/withdrawal, tampering and transactional recovery.
All fixture artifacts are ignored and removed by bounded cleanup. This is
software acceptance, not approval of a real training dataset.

## Compact private inventory on macOS and POSIX

The v2 directory stores the same provenance fields as v1 in a bounded metadata
stream and keeps the full SHA-256 shingles packed separately. The manifest binds
both streams, their counts, the feature policy and the normalization version.
Use a private directory and a mode-0600 JSONL projection containing one
validated v1 record object per line. Packing neither issues consent nor grants
rights.

```sh
python training/splits/split_cli.py pack --opt-in \
  --inventory "$PRIVATE_PROJECTED_JSONL" --output-dir "$PRIVATE_PACKED_INVENTORY"
```

Set the drafted consent ledger's `inventory_sha256` to the value returned by
`pack`. For consent signing and split build/verify, pass the directory as
`--inventory`. The expected current consent, source grant checks, quarantine,
role assignment and split receipt remain the same. The inventory supports
100,000 records, 30 million packed fingerprints, and a separate 30 million
exact-comparison limit. Oversize, incomplete, altered or nonprivate inputs
fail explicitly. A private snapshot verified against the fingerprint digest is
used for grouping. Temporary storage needs space for that snapshot in addition
to the stored inventory.

A global prefix index restricts candidates by length and common fingerprints.
The final check still uses exact 0.80 Jaccard, and lineage joins include every
input cohort. The grouping index stores term counts and compact prefix postings
in memory. Full shingles remain on disk, with a bounded cache of decoded rows.
Packing v2 is supported on POSIX only. Training and evaluation entry points still
use v1 until their source replay paths support the compact inventory.
