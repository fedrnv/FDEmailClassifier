# Rejected closure-request interpretation 1.0

Governing Correction: FDEC-100 in permanent process Epic S001. This local
implementation contract applies FDTasks 5.6 immutable records and unique first
closure identity to a previously rejected, unallocated type mismatch. It does
not replace the pinned upstream/adoption documents, amend their normative
lifecycle, allocate versions or authorize rewriting accepted requests. Existing
owner instructions authorize continued corrective development and append-only
contract records; no separate owner approval of an exception is asserted.

An immutable request whose allowed item-closure enum disagrees with its
immutable work-item kind remains an invalid original request. A separate
`fdec-rejected-request-recovery/v1` record may document its rejection and bind
the exact request, specification, first closure event/proof, source commit,
rejection evidence, this contract and a separate active/completed S001
Correction. A S001 scope event binds that exact recovery record and contract.
No recovery is implicit. Recovery cannot apply to a request whose original type
already matches its kind, to an Epic/release request, or to a source commit
containing allocated version state. Recorded rejection must explicitly attest
that allocation, publication and acceptance did not occur; those attestations
are local evidence, not independently authenticated external service records.

The common resolver validates all original identities, exact bound artifacts,
actual ancestor/source blobs and adopted recovery. It derives only the effective
type from the immutable work-item kind in a detached in-memory copy. Request
ID, item, Epic, summary, verification and every other original field remain
unchanged. There is still exactly one on-disk first request and one deduplicated
identity. All ordinary duplicate, parent, proof, evidence and Epic-closure checks
run on the resolved requests. No recovery is itself verified task closure.

Malformed, stale, ambiguous, unsupported, orphan or duplicate recoveries reject.
A previously valid accepted request cannot use this route to alter any field.
Recovery files and their adoption events are immutable append-only records.
Never overwrite the rejected original, erase its failing validation, substitute
new proof for its historical first proof or create a second first request.
Reopening/reclosing the item retains the original request and adds current
verified closure evidence under the ordinary lifecycle.

The narrow bootstrap is explicit: FDEC-100's initial normal validator fails on
the malformed request, so its recorded bounded readiness authorizes only this
process repair. Once the resolver exists, normal repository/admission checks
must pass before accepting the Correction. The S001 recovery adoption binds
the proposal; FDEC-100's verified completion finalizes implementation. No other
task may treat this bootstrap as permission to skip normal admission.

Current repository validation and its Epic-closure consumers share the common
resolver. No allocator/publisher exists yet. Any future allocator must consume
these same validated effective requests and preserve original IDs for exactly
once allocation, or fail on recovery records until it implements that contract.
Reading the original JSON as independently valid is incorrect. This work neither
implements nor authorizes publication, and makes no source/data/model rights
change. The D002 gate and independent review must still pass on their current
candidate after FDEC-099 is validly reclosed.
