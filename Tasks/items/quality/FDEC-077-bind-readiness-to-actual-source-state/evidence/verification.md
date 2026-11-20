# FDEC-077 actual source readiness acceptance

Source baseline 34cd962ebf35293084e03a45e0ed2758ad8c03cf plus exact working candidate identities below.
Actual source-state algorithm fdec-source-state/v1; digest 44283a9f6e76f3e0d13736cdb9b8ece2423a91902e69f976e036dd9e687e6da3.
Policy SHA256 ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403,
upstream 00a0d019c1e73d5ecf4c4e75c42c38497c154e50. Windows PowerShell 5.1/Git.

AC-01 PASS: powershell -NoProfile -File scripts/validate_tasks/test-source-readiness.ps1
Final monitor f17fd36b-1125-4f45-9368-d37ca35ffd71 exit 0. Current source admitted on
all claim/dispatch/resume/execute/close actions. Explicit renewed readiness admits
authorized changed working source; another change invalidates that renewal. Own
append-only evidence and recognized untracked IDE config do not invalidate source.
Git index and actual working content/path list are both bound. No arbitrary caller
exclusion list and no blanket accept-dirty rule. Material changes require fresh
readiness under standing task authority, not an approval cycle per internal edit.

AC-02 PASS: tracked implementation edit, staged-only edit with restored working
bytes, deletion, new nonignored source and arbitrary source under .idea all reject
stale readiness on each of the five actions while HEAD remains unchanged. Matching
original state restored admits again. LF/CRLF-equivalent Rust source preserves
canonical identity. Recognized source text extensions use strict UTF-8 CRLF-to-LF
identity with BOM preserved; binary remains exact. Earlier focused run passed;
final run added EOL compatibility and narrow IDE-exclusion negative coverage.
No failed candidate or unchanged functional retry accepted.

Direct interactions PASS: scripts/validate_tasks/test-validation.ps1, monitor
a485913b-92cf-48e1-b5dd-e797402098f9 exit 0; scripts/validate_tasks/test-identity.ps1,
monitor a9dfa9e9-b676-4509-a162-d3e5f17d8607 exit 0. Existing graph, immutable history,
source-HEAD, scoped-rule, dependency, request and migration safeguards preserved.
Fixtures now prepare current source-state fields and task-local readiness filenames;
scoped-rule scenario renews only source digest to reach the intended rule omission.
Actual authorized in-progress FDEC-077 execute admission PASS. git diff --check PASS.

## Exact candidate canonical file identities
- scripts/validate_tasks/source-state.ps1: 5af9d9643a125cbfc5f7c9b26e46136b7554dd292bd905407cf2bcbf698d9734
- scripts/validate_tasks/admission.ps1: 09f0e362a69f88d88a7891cc5164db6cb4936ff5bccb1fe0b24c3550e2f2aa2a
- scripts/validate_tasks/identity.ps1: 853424e839519852302be8e9f8b625b1b716118026f1b813f78ffbd3a5f6769f
- scripts/validate_tasks/test-source-readiness.ps1: f4a8c234e2e84acd8d472bc6cf01246a21cc73909e4d5899da8fdb3261d0c4bf
- scripts/validate_tasks/test-validation.ps1: ea65c4633d02cda529e686afd88af8282e7a96dc300128643936d7aafd564103
- scripts/validate_tasks/test-identity.ps1: b3606f30eebb6cb556b437c4e12026fb289c7027b4f8290eee54681ece369921
- scripts/validate_tasks/README.md: 7176fc97083a6033ecf9d29e8f05b8395d80b794e4f1130541ac3546fdc72a26

## Scope and limits
Excludes only the selected task's events/evidence/one request; immutable repository
validation separately rejects edits/deletions of already accepted records. Includes
tracked files even when ignored, plus nonignored new files. Recognized untracked
IDE XML/IML/config and Git-ignored build caches are not production source inputs.
Tracked IDE files and arbitrary untracked code under .idea remain bound. Unsupported
index stages/types, ambiguous path encoding and reparse paths fail closed. Fingerprint
is compact, deterministically sorted and includes staged modes/object IDs as well
as working identities. Current root stage/working state is explicitly captured.
Known R001 readiness-event acceptance and complete AC coverage remain FDEC-078/079;
self-declared current digest is not claimed to replace those authority checks.
No normative version/rule changes, original history edits or external publication.

## Cleanup and next turn
All monitor tasks terminal; fixture repositories removed by validated owned cleanup.
No build/server/watcher or external blocker. Unrelated .idea unchanged. Primary is
only retained worktree. FDEC-077 verified for one correction_closed request. Next
fresh turn owns FDEC-078, then 079, current D001 integration gate and independent
R002. FDEC-007 remains Blocked, FDEC-006 Planned, D001 sole Active. Goal active.
