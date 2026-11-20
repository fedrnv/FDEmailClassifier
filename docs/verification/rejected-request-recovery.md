# Audited recovery of a rejected closure type

FDEC-100 addresses one malformed original FDEC-099 request. The original JSON
stays unchanged at `Tasks/version-requests/FDEC-099.json`, canonical SHA-256
`fb50e63332b571b04e1ad7635ea013a7d8076ab77913a7de93cdd1ffa740ef0c`.
It remains an invalid standalone input. The original rejection is retained;
the recovered **effective** type is `correction_closed`, derived from the
unchanged Correction specification. Request ID and all other fields survive.

`Tasks/request-recoveries/FDEC-099-R001.json`, its S001 scope event and local
contract `Tasks/policy/rejected-request-recovery-1.0.md` explicitly record the
repair. The resolver requires actual ancestry, the original request creation
commit, unchanged historical source blobs, first closure/proof and bound local
rejection evidence. It checks the separate governing process Correction and
exact adopted record. It rejects recovery of a valid request and unsupported
fields; there is no arbitrary JSON overlay. Duplicate or escaped duplicate JSON
keys reject before PowerShell's otherwise lossy conversion.

All request consumers in the current validator use `Get-ResolvedClosureRequests`
from `scripts/validate_tasks/request-recovery.ps1`. The repository passes those
same resolved requests to Epic closure checks; it does not separately reread
raw mismatched types. Identity deduplication runs before recovery, then all
ordinary schema, parent, proof, artifact and historical closure checks run.
No allocator exists yet. Future allocation must use the same validated effective
requests and original IDs, or fail explicitly until recovery support exists.

The local evidence says this malformed request was rejected, unallocated and
unpublished. These are recorded facts of local execution, not independently
authenticated remote service attestations. The original creation commit is
also checked for allocated-state files; there is no license or publication
permission inferred from absence of such files. This process repair does not
replace pinned FDTasks 5.6 or permit edits to accepted immutable records.

Run focused checks locally:

```powershell
powershell -NoProfile -File scripts/validate_tasks/test-request-recovery.ps1
powershell -NoProfile -File scripts/validate_tasks/test-reopened-requests.ps1
```

The first uses a tiny owned Git fixture and counterfactual metadata. The second
includes existing Epic closure/index/history checks. Tests that copy historical
Tasks into a new repository now fetch ancestry **locally** from the source
repository and retain checkout normalization; they do not invent source commits,
download corpora or bypass the production recovery boundary. Cleanup is limited
to resolved owned temporary fixture paths. The process task's recorded command
also checks directly affected admission, matrix, identity and plan fixtures.

FDEC-100's initial normal validation was blocked by the demonstrated malformed
input; bounded bootstrap evidence discloses that fact. After repair, ordinary
admission is mandatory. FDEC-100 completion does not reclose FDEC-099, accept
R001 or close D002. FDEC-099 still requires current reclosure proof; its old
implementation-preservation check predates this separate process change and
must be reconciled honestly on resumption. Then rerun the D002 gate and obtain
fresh independent acceptance. Source licensing, training data, models, inference,
quality, paid resources and release actions are unchanged by this repair.
