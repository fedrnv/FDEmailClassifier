# FDTasks 5.6 adoption

FDEC-073 adopts the existing upstream 5.6 contract without changing its version.
The source snapshot is byte-bound by `adoption-5.6.json`; accepted initial records
are inventoried there and remain immutable. No numeric legacy Epics, pending
closure requests, hosted workflows or transitive hosted commands existed at adoption.
S001 and S002 already exist; new work uses D001+ and FDEC-NNN identities.

Run `powershell -NoProfile -File scripts/validate_tasks/admission.ps1` offline.
All agent claim/dispatch/resume/execute/close actions must use that same entrypoint
with `-TaskId FDEC-NNN -Action <action>`, plus the semantic review required below.
There are no other automated admission entrypoints at adoption.

Before dispatch, append accepted readiness and its immutable `evidence/readiness.json`:
task/policy hashes, current source SHA, atomicity, exact AC matrix, governing rule
source hashes, dependency revisions and Epic state evidence (arrays of path/sha256),
and `semantic_review: accepted`. Closure additionally binds verification evidence.
The executor must resolve all applicable AGENTS.md/DEVELOPMENT.md, inspect statuses
from all events, confirm dependencies Done and one active development Epic, and
assess atomicity and scope. The script validates identities and stale inputs; it
does not substitute for that semantic review. Source/rule/dependency changes require
new append-only readiness with a new evidence filename selected with
`-ReadinessFile evidence/<unique-name>.json`.

FDEC-004 retains its wider product-specific policy and release guardrail scope.
Version allocation is deferred to that implementation; requests are emitted on
first closure and no allocated state is hand-written. No external publication is
authorized by this adoption. A successor requires a new S001 Correction and history
entry; never edit the snapshot or accepted evidence. Adoption has no rollback by
deletion: publish a successor Correction instead.
