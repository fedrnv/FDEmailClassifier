# Verified development Epic closure requests

FDEC-081 repairs offline request admission under the existing FDTasks 5.6 rule.
The validator accepts `epic_closed` only for a development Epic with a verified
Done transition. S001/S002 never close. Version allocation, network publication,
release/major transitions and generated version history remain separate work.
Request acceptance alone does not assign a version or authorize publication.

FDEC-082 independently inspects the current index, working changes and nonignored
new paths. Restoring working bytes does not hide staged content. Staged ledger
changes may only add permitted completion files and must match their inspected
working content. Unmerged/nonregular index entries and sparse/assume-unchanged
flags are unsupported and reject; Git inspection errors also reject. Historical
proof replay remains tied to its recorded source instead of today's index.

FDEC-083 disables rename/copy detection in committed candidate-to-closure path
comparisons as well. Both the original and destination paths are checked, so
committing a move of implementation into a completion directory cannot turn
implementation removal into an allowed ledger addition. This is independent of
the repository's `diff.renames` setting. Committed inspection uses the same
checked Git invocation as current index/working inspection.

Before closing, inspect every effective member and dependency, current gate and
independent review. Changes after the tested candidate require a repeated gate
and review unless they are strictly append-only completion/review bookkeeping
for that Epic. Production implementation, task specifications and unrelated
changes cannot be smuggled through the ledger exception. The executor must
actually inspect acceptance evidence; the JSON schema is mechanical provenance.

Append an Epic-local `evidence/<unique>.json` with schema
`fdec-epic-closure/v1` and these fields:

| Field | Meaning |
| --- | --- |
| `epic_id` | Development Epic identity |
| `source_sha` | Exact current HEAD before the closure commit |
| `candidate_sha`, `candidate_tree`, `policy_sha256` | Same identities as the latest passing gate and Accepted independent round |
| `gate_task_id`, `review_task_id` | Distinct member identities; gate depends on every implementation/correction member, review depends on gate |
| `epic_state` | Exact path/SHA256 bindings for Epic specification and events preceding this Done event |
| `members` | Exactly one `{id, state}` per effective member; `state` binds its specification and events through closure time |
| `gate_result` | Path/SHA256 of the successful `fdec-gate-result/v1` in the latest gate Done closure proof |
| `review_result` | Path/SHA256 of the latest requested round's Accepted `RESULT.md` |
| `verification` | Nonempty Epic-local evidence path/SHA256 bindings |

Use `Get-IdentityHash` from `identity.ps1` for new bindings. Every member must be
Done at this closure timestamp and have its own first-closure request. State
snapshots include dependency/membership amendments; no member or event may be
omitted or duplicated. The Epic's own new closing event is excluded from
`epic_state` to avoid a self-referential hash. Its front matter binds this proof
using `closure_proof: evidence/<unique>.json` and `closure_proof_sha256`.

The latest gate Done event must bind its task-local closure readiness, which
directly binds the selected result. The latest review Done event must bind its
task-local readiness and a `fdec-review-reconciliation/v1` artifact with matching
task/candidate/Accepted result and an `artifacts` binding to `RESULT.md`.
Request and result front matter must agree on round, review task, Epic,
candidate, tree, policy and gate-result identity. The independent session and
its reasoning must be disclosed in the actual result; populated fields are not
an independent review. Gate completion precedes review completion.

Append one `Tasks/version-requests/<epic-id>.json`, with schema
`fdtasks-version-request/v1`, unique `request_id`, `type: epic_closed`,
`epic_id` and `work_item_id` both equal to the Epic, summary and verification
paths matching the proof. Append the Done event and request together, then run
`powershell -NoProfile -File scripts/validate_tasks/repository.ps1` before commit.
Do not edit `Tasks/version.json` or allocate an integer in the closing agent.

Every Epic Done transition requires its own current proof. On reopening, retain
the original request and all proofs. Historical proofs are checked at their
closure timestamps and source commits; later work does not invalidate a valid
first request. Reclosure requires renewed evidence and creates no second request.

Run `powershell -NoProfile -File scripts/validate_tasks/test-epic-closure.ps1`
for focused synthetic positive/negative cases. The existing
`test-reopened-requests.ps1` also invokes this suite, so the D001 gate includes
the shared item/Epic lifecycle boundary without another hosted workflow.
