# First closure and reopening

FDEC-079 requires every effective AC exactly once, with `criterion_sha256` from
`Get-EffectiveCriteria` in acceptance-matrix.ps1 and nonempty string `scenario`,
`level`, `command`, `environment`, `expected`. IDs/hashes bind the accepted wording;
populated fields do not replace semantic executor review. Never use the synthetic
fixture-matrix helper as real acceptance evidence. Hash-bound scope-amended events
may reference `acceptance_file` under own evidence plus `acceptance_sha256`.
Supported fdec-acceptance-amendment/v1 contains task_id and additions/updates of
id+criterion. IDs cannot be removed; unsupported or ambiguous changes fail closed.
Readiness must bind event and amendment paths/hashes in `criteria_revisions`.
Prose-only mentions of changed ACs cannot silently redefine criterion coverage.

FDEC-078 requires the latest task-local `readiness-accepted` event to bind
`readiness_file: evidence/<unique>.json` and canonical `readiness_sha256`.
Use `Write-ReadinessAcceptance <root> <task-relative-directory> <readiness-file>`
from readiness-events.ps1 only after the executor actually accepts that exact
brief under standing authority. The helper records a decision; it does not conduct
semantic review or bypass source/dependency/criterion checks. Record this event
before calling admission, including direct closure. A newer decision supersedes
older briefs; identical bytes at another filename are still another decision.
Missing/malformed bindings, changed evidence and tied newest timestamps reject.
Older prose-only events remain immutable history but cannot authorize new dispatch.
This is repository acceptance provenance, not cryptographic authentication of the
human/agent actor; the authorized append-only writer boundary remains unchanged.

FDEC-077 readiness includes `source_state_algorithm: fdec-source-state/v1` and
`source_state_sha256` from `Get-SourceState <root> <task-id>` in source-state.ps1.
It binds the actual index plus tracked and nonignored new file paths/content,
including deletion. HEAD alone is insufficient. Every admission action recomputes
the digest. Material source changes require fresh task readiness before another
claim/dispatch/resume/execute/close, including authorized in-progress edits; no
human approval per edit is added. Only this task's append-only events/evidence and
single version request are excluded (immutable history still validates them).
Only recognized untracked .idea XML/IML/config state is excluded as unrelated IDE
data; arbitrary source under .idea and all tracked IDE files remain bound. Ignored
build/cache files follow Git's ignore rules, while ignored-but-tracked
source is always included. Reparse points, unmerged/index-unsupported entries and
ambiguous path encodings fail closed. There is no arbitrary caller exclusion list.

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
