# Opt-in training ingestion

Install the verified Windows CPython 3.14 environment once:

```powershell
py -3.14 -m venv .venv/ingestion
./.venv/ingestion/Scripts/python.exe -m pip install --only-binary=:all: --require-hashes -r training/datasets/requirements-ingestion.txt
```

See [dependency evidence](DEPENDENCIES-ingestion.md). No dataset is downloaded by
installation, import, `--help` or tests. Download requires both `--opt-in` and
`--download`; a local cached artifact requires `--opt-in` and `--input` instead.
Every mode first invokes the current FDEC-008 audited inclusion guard. The CLI
uses the repository audit; there is no unchecked descriptor or policy override.

```powershell
./.venv/ingestion/Scripts/python.exe training/scripts/ingest_dataset.py `
  --dataset-id weijianzhg/email-triage-action-seed `
  --revision 8c98baa8b10a1dddd676c860d9e1b86c89141c38 `
  --artifact data/train.parquet --purpose commercial_training `
  --target specialized-email-classifier --opt-in --download `
  --output-dir training/data/seed-run
```

The hash/size-verified bytes are copied into the exclusively-created output
directory before any parser runs. HTTPS download starts only at the audited
revision URL and follows HTTPS redirects within Hugging Face domains. No Hub
script is executed, and no model/data publication is performed. Local input is
read-only and verified afresh; reuse a previous run's `source.parquet` via `--input`
when a private cache is preferred. Credentials and remote signed redirect URLs
are never printed or saved in the receipt.

Inside the repository output must be untracked and ignored beneath
`training/data/` or `training/outputs/`. A private directory outside every Git
worktree is also supported. Existing runs, other repositories, unignored paths,
symlinks and junctions reject. Runtime APIs may accept an explicitly trusted
policy root for isolated integrations/tests; the command line always uses this
repository's policy. Policy authors and the local filesystem writer are trusted;
this utility is not a sandbox against a concurrent privileged writer.

## Versioned result

A completed run contains the verified `source.<format>`, `records.jsonl` and a
`fdec-ingestion-receipt/v1` `receipt.json`. A local ownership marker supports
guarded cleanup. Receipt creation is the final atomic file replacement after
source/record writes are flushed. Consumers must require a complete receipt and
verify its record hash/version before use. A directory alone is not completion.
Normal failures remove only the new owned run and empty parents it created;
previous runs and input bytes are preserved. Abrupt process termination may leave
an incomplete private run: without a valid receipt it must not be consumed or
silently resumed. Choose a new run directory after inspection/owned cleanup.

Records use `fdec-normalized-email/v1`. NFC and collapsed whitespace normalize
subject/body. MIME extraction decodes charset/transfer encoding, prefers plain
multipart alternatives, falls back to visible HTML text and ignores attachments
and nested attached messages. HTML is never executed or fetched. Plain structured
bodies remain plain unless `body_format: html` is explicit. Formatting/HTML link
attributes are not retained in normalized text; original bytes remain in the
private verified source copy. No PII sanitization is claimed by extraction.

Content IDs bind the normalization version and normalized subject/body, excluding
source labels. Output is ordered by ID. Every original row index and source label
is retained in `annotations`; `source_round` is separate provenance. Conflicting
labels set `annotation_conflict` instead of overwriting or selecting a label.
Canonical label mapping, ambiguity policy, splits and privacy sanitization remain
FDEC-010..012 work. A declared classifier target does not inspect future training.

The receipt binds the exact audited source/revision/artifact/hash, attribution,
audit hash, Python/decoder and implementation identity, records hash and counts.
It contains no local input path, timestamp, signed URL or message content.
Repeated ingestion of identical bytes under identical code/environment yields
identical records and receipts. Synthetic test policies cover JSON/JSONL/EML
adapters as well as the real Parquet reader; the production registry currently
admits only the previously audited Parquet artifact. Unsupported formats/fields,
malformed content, checksum/size mismatch and limits reject rather than truncate.

Run local synthetic acceptance:

```powershell
./.venv/ingestion/Scripts/python.exe -m unittest discover -s training/scripts -p test_ingestion.py -v
powershell -NoProfile -File training/datasets/test-allowlist.ps1
# Or run both checks and dependency consistency together:
powershell -NoProfile -File training/datasets/test-ingestion.ps1
```

Fixtures create their messages/data/policies under checked temporary paths and
perform no real corpus download or model training. Public code contains no stored
email rows. Stdout reports only counts and checksums; errors are static codes.
