# First closure and reopening

FDEC-076 adds `identity.ps1`: new bindings should use `Get-IdentityHash`. Explicit
UTF-8 text types normalize CRLF to LF only, preserving BOM and every other byte;
binary/NUL-containing input stays exact. Accepted legacy raw hashes remain intact.
`Tasks/policy/checkout-identities-076.json` binds their path-specific equivalents,
generated from the clean accepted source at its recorded SHA. It is an immutable
compatibility catalog, not permission to hash arbitrary changed content. Current
readiness must also bind this catalog as a governing identity source. New .gitattributes
stabilizes future text checkout; historical specs and evidence are not rewritten.

FDEC-080 separates current task state from validated closure history. A prior
first-closure request stays valid when an item reopens or recloses; it is not
deleted or emitted again. Duplicate request/work-item identities remain errors,
including duplicates encountered before their original in directory order.

For a new first closure, append a Done transition with front-matter fields
`closure_proof: evidence/<unique-closure-readiness>.json` and
`closure_proof_sha256: <exact SHA256>`. The proof is task-local and contains
`source_sha`, `task_sha256` and `verification` path/hash bindings. Each requested
verification file must be nonempty, under that task's evidence directory, and
match exactly one proof binding. New proof source must match current HEAD.
The first transition owns the proof; later reclosure cannot replace it.

Requests already accepted in HEAD retain their historical authority, including
older bootstrap records without these fields. Accepted request edits remain
forbidden by immutable-history validation. Existing proof fields are always
checked when present, even after a later commit or reopen. Never-closed targets,
wrong parent/type, missing evidence, bad hashes and duplicate identities reject.
This is mechanical provenance validation; it does not infer test success from a
file's existence or substitute for the executor's actual acceptance checks.

Run `powershell -NoProfile -File scripts/validate_tasks/test-reopened-requests.ps1`
locally. Identity-migration fixture baselines explicitly retain accepted historical
requests so their unrelated source/mapping tests do not fabricate new closures.
Current independent R001 findings remain queued for FDEC-076..079; this repair
does not claim to resolve checkout normalization, source readiness, readiness
acceptance history or matrix coverage. No normative rule version changed.
