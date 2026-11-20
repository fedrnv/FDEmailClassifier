# FDEC-004 verification and checkpoint

Source baseline: 3225ce0bf6a68e2d6cf91b7b551335490863de9e; policy source 00a0d019c1e73d5ecf4c4e75c42c38497c154e50.
Policy SHA256 ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Environment: Windows PowerShell 5.1, local Git, no network or registry dependencies.

AC-01 PASS: powershell -NoProfile -File scripts/validate_tasks/repository.ps1
validates all 85 current records, graph and requests. Shared admission dispatch
for FDEC-004 passes. Specs, old evidence and governing root rules unchanged.
AC-02 PASS: powershell -NoProfile -File scripts/validate_tasks/test-validation.ps1
checks positive claim/dispatch/resume/execute/close, stale source rejection on all
five paths, altered immutable record, unmet gate dependency, new unbound scoped
rule, duplicate request, competing Active Epic and unreviewed hosted workflow.
Fixtures restored and final repository validation PASS; owned temporary tree
removed. Missing readiness and tampered root rules additionally covered by:
powershell -NoProfile -File scripts/validate_tasks/check-adoption.ps1 => PASS.

Implementation failures corrected before acceptance: event sorting required
explicit dictionary-key expressions in PowerShell; original historical FDEC-073
has same-second start/closure, resolved by documented start-before-closure order.
Legacy adoption fixture needed a Git baseline after introducing immutable checks.
Gate fixture needed actual bindings for its completed dependencies before it
could reach the intended unmet dependency. Final runs pass after these corrections;
no unchanged retries or flaky checks accepted. Final status parser rejects unknown
semantics and multiple transitions instead of silently projecting them.
Git diff --check PASS. Actual script/docs diff inspected. No independent item
review required; Epic review remains FDEC-007.

## Limitations
Restricted front-matter/prose adapters match current accepted records, not a full
YAML engine. Semantic atomicity and scope review remain explicit executor duties.
Hosted workflows fail closed until FDEC-050 supplies graph validation. Release and
Epic version requests require a dedicated verified publisher; no external effects
are performed by validation. Pending item requests stay unallocated; FDEC-055 owns
allocator/version implementation. No adopted normative rule changed. The new
implementation document clarifies the provisional FDEC-004 allocator reference in
historic adoption notes without editing them. FDTasks source redistribution rights
remain unresolved; this does not block local FDEC-005 development.

## Raw candidate hashes
- scripts/validate_tasks/admission.ps1: f16398862150d57f3ef528e5a2ee7d1206df735468d7f1a03c21b3ed699c9039
- scripts/validate_tasks/check-adoption.ps1: 841734826db6b71f77cd7d447856e74dede5215eca2dbacab1c93d0a230d3c00
- scripts/validate_tasks/repository.ps1: 32704ac26a58e2e845f3f8bb73d6d4afe3f511c39ff5426330a7a4d3b9340f28
- scripts/validate_tasks/test-validation.ps1: f13f2c762c947636275f1742f4bacf269e142abd0ab2bd1b4ff53fe2913d4f4f
- Tasks/policy/implementation-004.md: 27bd4d0ce4e6b40f4093f3a1dfe0210ac2c46e044be21acbcbe22c1fd365d70d

## Durable checkpoint
FDEC-004 verified for closure and one task_closed request. Next fresh turn:
admit FDEC-005 using new allowed_paths and complete readiness bindings, then
implement its architecture/backend ADR outcome. D001 alone Active. No running
process, server or temporary fixture. Preserve unrelated .idea directory.
User authorizes sequential local development; releases/models still require
explicit operator authorization. Goal active; no external blocker for next task.
