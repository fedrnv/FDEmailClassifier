# FDEC-101 dependency correction verification

Source: `c693cf61625ba970610d46da7d7233303fcdbaf4`.
Source state: `0f575672228333789442134546e8da13359c9e2769ba09b869923edec40546a8`.
FDTasks 5.6 policy: `ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403`.
Initial and frozen execute admissions passed; final admission is
`frozen-readiness-v4.json`. Source state was rechecked after all six final runs.

| Criterion | Actual final verification | Result |
| --- | --- | --- |
| AC-01: exact adopted MLX dependency correction with original criteria/gate preserved | FDEC-087 resolves to [FDEC-019, FDEC-101], original specification hashes unchanged; FDEC-020 still includes FDEC-015/016/087; historical snapshot before amendment retains [FDEC-016] and excludes future artifacts; after amendment binds new dependencies/artifacts; five admission actions reject unfinished governing Correction | PASS |
| AC-02: invalid amendments and ordinary admission/history boundaries | 25 negative amendment cases, contract omission, current/legacy readiness, complete acceptance matrices, tracked/index/new source binding, owner-plan migration and Epic closure/reclosure suites | PASS |

All six components ran at the final frozen source and exited 0. Exact commands,
monitor IDs and output paths are in `components-v1.json`; combined output is
`test-output-v1.txt` and component logs are retained separately.

| Command under scripts/validate_tasks | Monitor |
| --- | --- |
| test-dependency-amendments.ps1 | 9daa2a7e-5555-4288-90e4-b836451367fe |
| test-plan-sync.ps1 | 5ee5762b-e15d-4332-af16-8846af487269 |
| test-epic-closure.ps1 | 6ee0d9ec-6da7-439d-8b74-bd5645415315 |
| test-readiness-events.ps1 | 71c9deec-3c97-42d3-9702-6f462a599058 |
| test-acceptance-matrix.ps1 | eedf3521-eacc-457b-8c1e-338566b5410e |
| test-source-readiness.ps1 | 0be1c6a9-fd97-43dc-ae14-1c05ba72c104 |

Environment: local Windows PowerShell, existing Git history, owned metadata-only
temporary Git fixtures. No model, training runtime or external host is used by
these checks. Three long-output logs were copied from the complete monitor log
files after terminal success and checked for the expected final footer; no
truncated tail substitutes for full evidence. The small dependency log combines
the returned text from two waits in order and explicitly disclaims byte-exact
stream export. Git line-ending warnings are preserved, not hidden as test output.

## Implementation and authority

The immutable local contract is `Tasks/policy/dependency-amendment-1.0.md`.
Its exact initial amendment is `Tasks/dependency-amendments/FDEC-087-D001.json`,
bound by explicit S001 adoption and the separate FDEC-087 dependency event.
`graph-observation-v1.json` records the initial/current sets, source/spec hashes,
unchanged original training/gate specifications and unchanged rights boundaries.

Strict interpretation checks the exact prior set, target specification, ancestor
source, separate S001 Correction, versioned contract and unique adopted record.
The new set must include its governing Correction. A proposal can be validated
while that Correction is InProgress, but shared claim/dispatch/resume/execute/
close admission rejects until it is Done. Bare Done without a first closure
request rejects; the ordinary complete request resolver still validates that
request/proof. This is not a status-only self-approval mechanism. Readiness for
an amended target must also bind the dependency contract as a governing rule.

The 25 adverse cases cover stale/non-array prior sets, unknown fields, duplicate
dependencies, missing governor/self dependency, non-ancestor source, stale and
rebound source specification, wrong governor/target, unsafe/missing/changed
adoption, terminal target, inactive governor, wrong contract, missing target,
cycle, orphan/duplicate amendment, duplicate JSON keys, ambiguous event fields,
duplicate adoption and bare Done. Existing graph, duplicate event, source,
accepted readiness, first-request identity, proof and closure checks remain.

Historical replay consumes the same already validated amendment nodes and adds
their artifact bindings only when their target event is effective at the cutoff.
External JSON/contracts/governing specs are evidence, not misparsed task events.
Older snapshots and ordinary identity-collision relationship replacements retain
their original interpretation. The Epic suite verifies missing proof, unfinished
members, non-Accepted review, changed/staged/new/renamed implementation, index-only
rewrites, hidden flags, unmerged state, failed Git inspection and reclosure.

The owner authorized necessary append-only task-contract corrections. This
bounded S001 Correction applies the pinned lifecycle rather than editing it or
asserting a new upstream lifecycle version. The immutable 1.0 document plus S001
adoption event are the local extension/history entry. No separate owner approval
of an exception, dataset right or host switch is claimed. The interrupted D003
checkpoint and exact FDEC-087 Stage A restart predicate are in preemption-v1.md.

## Exploratory failures and cleanup

The first readiness-authoring helper misused a .NET regex replacement token and
stopped before writing readiness or starting work. Its immutable file is retained;
the literal-line successor v2 authored all accepted decisions. The first test
fixture needed its missing evidence directory created. Another negative scenario
initially triggered the existing duplicate UUID guard rather than the intended
duplicate amendment-reference guard; a fresh UUID now exercises the latter.
The initial owner-plan test also asserted its old D002 Active stage/current
FDEC-016 dependency. It now accepts legitimate D002 completion and verifies both
historical original and current adopted dependency projections explicitly.

Snapshot tests initially called helpers outside the repository script's scope;
they now dot-source in an isolated child scope, preserving the actual source
root. Production historical replay needed explicit validated amendment metadata
and cutoff bindings; that direct consumer is included in this Correction. Earlier
candidate runs are exploratory only; all acceptance claims use the six final
passing components at c693cf6. No failed run is recast as a pass.

Fixtures were removed only after verifying their absolute owned temporary paths.
No historical spec/event/evidence/request was overwritten. Existing .idea is
untouched. No email, secret, private training data, weight, machine serial or
credential enters these records. Original model/dataset rights guards, both
prohibited Codex packs and source/consent checks are unchanged. No data approval,
GPU success, MLX run, Mac switch, publication, allocation or expense is asserted.

After FDEC-101 verification, resume D003 at FDEC-087 Stage A under fresh readiness
on the original workstation. FDEC-015 and FDEC-016 remain incomplete; FDEC-020
still requires them. Explicit owner confirmation precedes machine-specific Mac
execution and the original private transfer/return requirements remain intact.
Close only this Correction; keep S001 open and D003 the sole Active dev Epic.
