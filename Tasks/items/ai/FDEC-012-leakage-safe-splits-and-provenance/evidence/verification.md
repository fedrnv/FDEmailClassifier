# FDEC-012 acceptance verification

Command: `powershell -NoProfile -File training/splits/test-splits.ps1`.
Monitored task e3874ca4-dff2-46c5-a6a8-f4c80aec21db completed with exit 0.
All 21 tests passed. Exact source SHA/tree and environment are in result.json.
Policy SHA256: ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Windows x64 / CPython 3.14.5 / standard library only; local PowerShell rights
guard reused from completed ingestion. No hosted tests or remote corpus calls.

AC-01 PASS: declared source/thread/exact-content/near-duplicate/family relations
are unioned transitively, never assigned independently. Representative fixtures
exercise thread-to-near-duplicate chains, same-source peers, cross-source exact
copies and translation/template families. Three nonempty splits use whole
components and report actual count deviations. Impossible independent-group
counts reject. Versioned Unicode fingerprint policy, deterministic seed/ratios,
signed inventory, original ingestion/source-row hashes and current source grants
are bound into immutable manifests. Repeated builds produce identical bytes.

Consent controls require a current authenticated authority snapshot, per-record
evidence and both training/evaluation purposes. Missing, revoked, expired or
insufficiently scoped grants quarantine the entire related component. Activated
snapshots advance by one revision with the correct previous identity and retain
immutable history. Archived grant replay fails after revocation; earlier
manifests remain unchanged. Source-license denial remains independent of consent.
The actual existing rights guard was exercised for eight isolated synthetic
sources and both purposes (16 inclusion calls), plus a later source-denial case.
Other algorithm fixtures mock only source descriptors, not grouping or consent.

AC-02 PASS: malformed inventory/relationships/provenance, invalid signatures,
duplicate grants, invalid or expired times, missing authority, impossible split
policies, resource budget exhaustion, changed receipts and checksum-updated
cross-split contamination reject with static codes. Tests cover consent changes
during manifest writing, failed authority-pointer updates and exact retry,
failed output commits, existing directories and linked outputs. Prior authority,
history and split files are preserved. The verifier compares a freshly computed
current-source/current-consent plan with the exact manifest bytes it parsed;
consumers can use the returned validated snapshot without rereading the file.

Boundaries: trusted data preparation must verify the actual upstream ingestion
run, preserve known relationship metadata, and attest that derivation in the
inventory-bound consent ledger. The helper validates normalized content/source
consistency; it does not independently replay the entire upstream raw artifact.
HMAC authenticates the shared data-owner/consumer trust boundary, not external
legal facts or public-key identity. Protected current-anchor storage and key
custody are required. These limitations are explicit in both contract READMEs.

Near-duplicate safety is defined by the versioned five-character-shingle Jaccard
policy and supplied lineage, not universal semantic similarity. Single-source
corpora cannot form three independent source-held-out splits; grouping is never
weakened to force ratios. These tests approve software behavior, not a real
dataset, real consent, language quality or model readiness. FDEC-011 remains
Blocked and its fixture-only source is not promoted or admitted by this change.

All message/feature/permission fixtures were created at runtime beneath ignored
disposable paths and removed by guarded cleanup. Ephemeral authority keys existed
only in test memory/subprocess environment and were never printed or committed.
No production authority anchor, real permission record, personal mail, dataset,
model, release, push, publication or next-task execution was created here.

Scope is training/splits, training/manifests and own task events/evidence/request.
Existing accepted task specifications and blocked-augmentation evidence remain
unchanged. The focused suite and repository ledger validation are sufficient for
this diff; the D002 integration gate and independent review remain separate.
