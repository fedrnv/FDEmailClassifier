# Explicit dependency interpretation 1.0

Governing implementation Correction: FDEC-101, permanent S001. This compatible
local envelope contract implements FDTasks 5.6 append-only dependency changes
and renewed admission. It does not modify the pinned upstream lifecycle/adoption,
acceptance criteria, old specifications or identity-collision replacements.
Owner standing instructions permit necessary append-only contract corrections;
no separate owner approval, data right or machine confirmation is invented.

A nonterminal Task may contain a dependency-amended event referencing one
strict fdec-dependency-amendment/v1 JSON record under Tasks/dependency-amendments.
The record binds the immutable target specification, current ancestor source,
exact previous and new dependency sets, separate S001 Correction specification,
this versioned contract, reason and explicit S001 adoption event. The adoption
event binds the amendment and contract hashes without circular hash references.
Each record is referenced by exactly one target event and adoption. No implicit
removal, unknown/duplicate field/key, stale prior set, path escape, changed spec,
terminal target, unsupported record/file, orphan record, duplicate amendment,
unrelated/inactive governance or dependency cycle is accepted.

The governing Correction must be InProgress or Done and must itself be included
in the new dependency set. Thus a proposal can be validated while implementation
is reviewed, but ordinary shared admission cannot dispatch its target until the
Correction is verified Done. Only a separate Correction may govern a change;
the target cannot authorize itself. S001 stays Active. Global graph, accepted
source, readiness, existing relationship migration and closure/request checks
remain mandatory. Changed dependencies and their evidence invalidate old
readiness. The original TASK.md and acceptance criteria remain unchanged.

Initial adopted case: FDEC-087 changes [FDEC-016] to [FDEC-019, FDEC-101].
This makes MLX preparation follow the verified export contract and verified
process correction. FDEC-016 still needs original supported-GPU acceptance and
remains in FDEC-020's dependencies, as do FDEC-015 and FDEC-087. No D003 gate,
independent review or Epic closure can skip those original outcomes. Explicit
Mac confirmation, private transfer, actual data/annotation/consent and public
weight license gates are unchanged. This is not training or device readiness.

The immutable contract and S001 adoption event form this local extension's
history entry. Future semantic changes require a new versioned successor and
separate governing Correction; never edit this accepted 1.0 document in place.
