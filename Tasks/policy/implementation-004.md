# FDEC-004 offline validation

This implementation enforces the pinned upstream 5.6 contract without changing
normative rules. Original specifications, adoption evidence and root rules remain
unchanged. `repository.ps1` validates the current restricted v3/v4 record envelopes,
identity, atomicity declarations, AC rows, relationship graph, status transitions,
single active development Epic, permanent special Epics and item version requests.
It compares tracked immutable records against HEAD with Git normalization and
rejects edits/deletions; the original adoption inventory remains hash-bound too.

Run `powershell -NoProfile -File scripts/validate_tasks/repository.ps1` offline.
All claim/dispatch/resume/execute/close entrypoints use `admission.ps1`, which also
checks source/task/policy hashes, bounded `allowed_paths`, complete governing rules,
current Epic revisions and dependency revisions/status, AC commands and closure
evidence hashes. Readiness files are append-only: select replacements with
`-ReadinessFile evidence/<new-name>.json`. State changes invalidate affected inputs.
The existing readiness records remain historical evidence, not reusable permission.

The parser intentionally accepts the repository's simple front-matter subset and
inline dependency/atomicity lists, not arbitrary YAML. Relationship prose adapters
support the accepted `Add FDEC-NNN` amendments. Status prose must contain exactly
one transition; events are ordered by UTC time, with work-started before closure
at the same historical timestamp. Ambiguous/unsupported forms must fail closed
and need an explicit compatible adapter rather than rewriting history. Semantic
outcome/impact review remains the executor's responsibility, not a boolean proof.

No hosted workflows exist at foundation. Any hosted workflow is rejected until
FDEC-050 implements manual-trigger and complete reachable command-graph validation.
This blocks direct test steps, opaque wrappers and automatic trigger bypasses.
No validator publishes anything. Model/data audit and integrity checks plus explicit
operator authorization remain necessary for release/model publication. There is no
foundation publication entrypoint to bypass those requirements.

Only first verified item closure requests are admitted here, with unique request
and item identities, Done state, correct parent and existing verification references.
Epic/release requests require the later dedicated verified closure publisher.
FDEC-055 owns allocator implementation and semantic version surfaces; the adoption
README's provisional reference to FDEC-004 did not create an allocator requirement
in its immutable task. Pending requests are retained, never hand-allocated, and
no hosted allocator or external push is introduced by this task.

Run `test-validation.ps1` locally for fixture-based positive and rejection tests.
Temporary fixture repositories are owned by that script and removed after checks.
No acceptance/integration checks run in hosted workflows.
