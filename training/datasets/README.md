# Audited dataset admission

Run `powershell -NoProfile -File training/datasets/assert-allowlist.ps1` to validate
the complete registry and its bound audit/report/observations. This succeeds when
blocked sources are correctly excluded; it does not download or approve all data.

Before any opt-in ingestion, request one exact descriptor:

```powershell
powershell -NoProfile -File training/datasets/assert-allowlist.ps1 -Action include `
  -DatasetId weijianzhg/email-triage-action-seed `
  -Revision 8c98baa8b10a1dddd676c860d9e1b86c89141c38 `
  -ArtifactPath data/train.parquet -Purpose commercial_training `
  -Target specialized-email-classifier
```

Inside PowerShell, invoking the script with `&` returns a descriptor object.
Only success permits the later loader to consider that pinned artifact. Verify
its SHA256/size before parsing, preserve source/license/audit attribution and apply
privacy/content checks. No Hub script may be executed. Data belongs outside Git,
under the existing ignored `training/data/` convention or a private external cache.

Unknown sources, changed revisions/files, other targets and redistribution reject.
`imnim` and `talby` remain blocked. General chatbot/generative training or weight
publication is outside this audit. A target argument declares intended use; it
does not inspect a training implementation. Changes to rights require a new
reviewed audit and updated binding, not an unchecked inclusion switch.

See [the source-specific audit](../../docs/legal/datasets/audit-2026-11-20.md).
Run `test-allowlist.ps1` for metadata-only positive/negative acceptance fixtures.

FDEC-009's [opt-in ingestion](INGESTION.md) consumes this guard before transfer or
parsing, verifies artifact bytes, normalizes MIME/body text and preserves duplicate
annotations in ignored private runs. It does not broaden any rights decision.
