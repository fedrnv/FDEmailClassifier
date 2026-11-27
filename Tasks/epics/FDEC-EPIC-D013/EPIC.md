---
schema: fdtasks-epic/v4
id: FDEC-EPIC-D013
title: "Stable 1.0 prerequisite and second-round classifier improvement"
initial_status: Planned
initial_dependencies: [FDEC-EPIC-D010]
created_at: 2026-11-27T21:01:44Z
created_by: "project-owner-authorized planning"
---

# Stable 1.0 prerequisite and second-round classifier improvement

## Outcome
Improve first-round topic/action/priority/security results with audited additional
data, reproducible second-round LoRA and independently measured library-compatible
model artifacts, strictly AFTER a working stable 1.0 release built on GitHub.

## Mandatory owner ordering
First complete existing D004-D010 library, Rust/C/C++/Python APIs, documented REST
API, installation and API documentation, local acceptance and independent review.
Then build/package on GitHub with successful manually dispatched Actions and
publish stable 1.0 packages. FDEC-239 verifies that concrete release milestone.
Only after FDEC-239 is Done may any FDEC-240..246 work or real round-2 training,
validation/model selection begin. A green build alone, beta, scaffold, draft or
planned release never unlocks training. The owner explicitly prioritizes this
sequence over optional further training in D011/D012; no extra optimizer run may
be hidden inside completion of first-round D003. Existing accepted evidence and
necessary original-artifact verification remain valid.

No new training is a prerequisite of 1.0: release the functioning library with
honest first-round quality limits and a lawful usable model installation path.
The existing release/model rights boundaries remain binding. If they prevent a
usable stable release, record the blocker; do not bypass it or start training.

## Accepted membership
- FDEC-239
- FDEC-240
- FDEC-241
- FDEC-242
- FDEC-243
- FDEC-244
- FDEC-245
- FDEC-246

## Dependency graph and scope
FDEC-239 -> diagnosis FDEC-240 -> rights FDEC-241 -> corpus FDEC-242 ->
training FDEC-243 -> validation selection FDEC-244 -> local integration/evaluation
FDEC-245 -> independent review FDEC-246. Every round-2 functional item also
directly depends on FDEC-239. Six functional items, one gate and one review.
No duplicate implementation of prior SDK/build/documentation/training tasks.

## Baseline and data candidates
Use the 2026-11-27 FDEC-087 report: 1,950 reviewed train examples, 1,500 steps,
1,653 held-out messages, topic micro-F1 0.8763/all-12 macro-F1 0.2134,
action 316/619 versus archive 428/619, priority 1450/1560 with high 24/32,
spam 0/6 and phishing 0/5 with all positives abstained. These are historical
measurements, not guaranteed production quality. Recover full private evidence
before claiming causes. Audit MeAJOR, SpaPhish, SpamShield and email intent data;
reuse approved prior TRAIN data, never final-test labels. Candidate license tags
do not constitute project admission.

## Gate, review and completion
Follow FDTasks 5.7 and applicable repository rules. Keep this Epic Planned until
its prerequisite and one-active-Epic scheduling permit activation. Freeze quality
objectives on validation before final-test access. Exactly one changed-area local
gate and a separate independent review are mandatory. All members Done, passing
current gate, Accepted current review and no blocking findings precede closure.
A failed improvement experiment is reported honestly and does not silently ship
new weights or replace 1.0. Publication of improved weights is not authorized by
this planning record. No version allocation or task completion is claimed here.
