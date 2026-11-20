# FDEC-079 complete effective acceptance matrix verification

Baseline 0a4b52a0f3424efdf10cdeecc90a84ec27421bc0 plus exact working candidate file identities below.
Actual source-state fdec-source-state/v1: e41709c2eaf68c75da646acc6ba7a3e2905a49979f8e2ca4dd15f56f7951728f.
Policy SHA256 ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403;
upstream 00a0d019c1e73d5ecf4c4e75c42c38497c154e50. Windows PowerShell 5.1/Git.

AC-01 PASS: powershell -NoProfile -File scripts/validate_tasks/test-acceptance-matrix.ps1
Monitor 18f7bc83-f520-4372-b3b5-8bcb17db3377 exit 0. All five action entrypoints admit
exact complete criterion coverage. Each row binds actual criterion wording hash
and explicit scenario, level, command, environment and expected result. Effective
criteria include immutable task matrix plus hash-bound accepted scope amendments;
new criterion becomes mandatory even when own ledger additions are excluded from
source-state digest. Amended event/evidence revisions must be bound in readiness.

AC-02 PASS: same test rejects omitted AC-02, duplicate ID, unknown ID, stale wording
identity, and separately blank scenario/level/command/environment/expected. Every
case exercises claim/dispatch/resume/execute/close with an actual accepted readiness
event so the relevant matrix check is reached. New amendment rejects stale matrix;
expanded matrix without amendment revision bindings rejects; fully bound current
matrix admits. Exact tasks and source unchanged outside owned synthetic fixtures.

Direct refinement boundary: powershell -NoProfile -File
scripts/validate_tasks/test-criterion-refinement.ps1 => PASS. Updating existing
AC-02 preserves IDs/count, changes criterion hash and binds both amendment/event
revisions; tampered or unknown-ID refinements reject. An earlier additional inline
probe was blocked by automatic command review before execution with no specific
reason; this bounded script completed the same verification safely. No approval
bypass, accepted-source edit or functional failed test relabeled PASS.

Direct admission interactions: test-validation.ps1, monitor
4736f7f4-3520-454a-8b23-90962e4abba3 exit 0; test-identity.ps1, monitor
1fed7da5-8825-44cf-ad7c-91911f0c56c5 exit 0. Five action paths, immutable history,
source/rules/dependencies, graph/requests and identity migration safeguards remain
passing. Fixture helper explicitly creates complete synthetic matrices for the
selected immutable target; it is not used as primary real-task acceptance.
Actual initial dispatch and full current execute admission PASS; git diff --check
PASS. Source diff inspected; no broad unchanged gate repeated in this item.

## Compatibility and scope
Stable case-sensitive AC IDs must match effective criteria exactly once. Hashes
bind criterion text. Complete string fields do not prove semantic adequacy; actual
executor review and verification remain mandatory. Restricted Markdown table
parsing rejects malformed column counts or duplicate base criteria. Structured
scope-amended evidence supports additions and same-ID refinements; silent removal,
unknown fields, duplicate IDs, bad hashes, ambiguous ordering or prose-only changed
AC definitions fail closed. All accepted specs/events/evidence remain unchanged.
Existing policy version 5.6 unchanged. No account, model/data or publication effect.

## Canonical candidate source identities
- scripts/validate_tasks/acceptance-matrix.ps1: 913c388f2dc1f323709e382da78e87d552128dc5ce431be655d32524c3047804
- scripts/validate_tasks/fixture-matrix.ps1: 1ca28f5e43388ff79c681568fc800d770dabf183fd5d0892c1c467b49937402e
- scripts/validate_tasks/admission.ps1: 1b3ea2963dfbaafa9f0e1ad7856cde672166b7018cfc36d888c1d544a1240169
- scripts/validate_tasks/test-acceptance-matrix.ps1: 6be4a779b89c04848e2e706c8602d7f275b9dab45e67a74551741c593f4d0556
- scripts/validate_tasks/test-criterion-refinement.ps1: 75ddb9253baefb33d7ef6b02794b8a759d3acd87a9b6f4ad1720ab67507cac2a
- scripts/validate_tasks/test-validation.ps1: a4c384bc4ae0a3ee2339a77dddf8dbcf05fd402a5538d790c2f7a4f25df5d617
- scripts/validate_tasks/test-identity.ps1: 0b87aea4f8f86d752935bf59a8d625635442856a997b36b6f24b5a8700a30354
- scripts/validate_tasks/test-source-readiness.ps1: 34421ac90d1f0b20c0c7f24b08979c96ce512042dfff9552678b215df9c739ed
- scripts/validate_tasks/test-readiness-events.ps1: 5ba0ed0f622ecd1ddea40a3eeae7957d367bd449cc92affbe08f7daa6dc717ee
- scripts/validate_tasks/README.md: b63b88ec897d8662d81e3be848abfa13911e3db16131289c01df173e2e908d1d

## Cleanup and next turn
Owned temporary fixtures cleaned by checked finally blocks. All monitors terminal,
no background server/watcher; unrelated .idea untouched. FDEC-079 verified for
first closure. All four R001 D001 corrections are now ready for their completion
ledger; FDEC-007 remains Blocked and FDEC-006 Planned pending fresh gate and R002.
Next fresh turn owns FDEC-006: update its local entrypoint to cover new checkout,
actual-source, accepted-decision and AC-contract boundaries; freeze exact source
commit; run targeted D001 integration once and retain original first gate request.
Then separate independent FDEC-007 R002 on that exact tested source. Do not claim
D001 closed or start D002. D001 sole Active; Goal active, no external blocker.
