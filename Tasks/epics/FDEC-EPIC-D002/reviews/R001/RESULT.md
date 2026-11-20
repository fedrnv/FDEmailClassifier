---
schema: fdec-independent-review-result/v1
review_id: R001
review_task_id: FDEC-014
epic_id: FDEC-EPIC-D002
candidate_sha: 0bcd4c4f377af86ee8b83d1d0bf770f0eb448ad8
candidate_tree: 558697de3b18fd1bea8358a144bae90a90231c76
ledger_sha: 7868e944c7a9c5e721b0a435acd0ae572055789d
policy_sha256: ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403
gate_result_sha256: 0702e6c97126247f79ab5184b1c4b1e74d453877346fac3b776800ea882b9f10
reviewer: Codex independent model session /root/review_d002_r001
result: ChangesRequired
---

Decision: **ChangesRequired**. The software evidence passes the focused independent checks, but the accepted Epic outcome has not been reconciled with the narrower delivered scope. This is one acceptance-completeness blocker; it is not a finding that the safeguards should be weakened or that model training must occur during review.

Independence: this is a separate reviewer model session with the repository rules, review request and executor messages, without implementation-author conversation history. The executor supplied the frozen workspace and runtime. I inspected their contents critically; I did not author candidate implementation, delegate review, or accept previous Done labels as proof. Shared filesystem/runtime and the supplied gate evidence are the practical independence limits.

## B1: Epic outcome exceeds the delivered and effectively accepted Task scope

Location: `Tasks/epics/FDEC-EPIC-D002/EPIC.md:14`; the sole D002 event is its activation. Compare FDEC-011's `independent-data-acceptance-v2.json` and `sinabis-acceptance-v3.json`, its final preparation report, and `docs/verification/d002-gate.md:40`.

The immutable Epic promises to produce provenance-tracked, lawful, reproducible **training/evaluation data**. The valid FDEC-011 amendments instead accept generator/preparation software independently of actual source admission. That distinction is correctly implemented, but there is no append-only Epic outcome refinement adopting it. Request wording, Task amendments and passing technical fixtures cannot silently substitute a different accepted Epic outcome.

Reproduction: run `probe-scope-v1.py` with the command below. The frozen Epic has one activation event and no outcome refinement. Its pinned Sinabis report records `training_ready: false`, zero independently supervised records, one source cohort and pending annotation, quality, consent/split integration and training admission. Directly invoking the unchanged production inclusion guard for that exact Sinabis identity returns `rights_not_approved`; attempting one-group allocation returns `insufficient_independent_groups`. Both Codex packs correctly reject training/evaluation. The independent source registry contains one seed source; no real admitted train/validation/test deliverable is evidenced. The passing gate explicitly excludes actual dataset train/test admission. The gap is contractual and evidentiary, rather than an inference from missing private files.

Impact: an Accepted D002 review would permit lifecycle closure against an unachieved or ambiguously reduced accepted outcome. It could make later work rely on training/evaluation data that this candidate does not establish. Software success alone does not discharge that outcome.

One bounded remediation outcome: **make D002's effective accepted outcome and completion evidence agree**. If the owner's intended D002 deliverable is the demonstrated software/preparation scope, record an explicitly owner-authorized append-only Epic outcome refinement, preserving the original specification and identifying the deferred actual-data admission boundary. Otherwise provide the actual-data acceptance evidence required by the retained outcome. Reconcile the candidate/evidence identities through the normal gate and a fresh independent review round. This does not require making optional D011/D012 enhancements prerequisites, buying data, training a model, or promoting Codex/Sinabis data through existing denials. The reviewer has made no such changes.

## Inspection and positive findings

Read root/Task rules, DEVELOPMENT.md, pinned FDTasks 5.6 lifecycle and identity policy, D002 specification/events, FDEC-008 through FDEC-014 specifications, their relevant events, FDEC-011's three effective amendments and AC-01 through AC-09 reconciliation, component verification/results, complete gate transcript and closure proof. Inspected rights observations/audits and registries, ingestion/normalization, annotation mapping/schema boundary, augmentation/native/translation/input admission, Sinabis source/preparation, signed consent/grouping/manifests, source freeze scripts and direct pipeline tests. No hosted workflow was introduced by the reviewed gate; its acceptance commands are local.

Verified exact candidate SHA/tree and policy. Candidate-to-ledger delta is nine additions restricted to FDEC-013 completion metadata and its version request. Independently verified all 182 closure-proof bindings at the frozen ledger, including the canonical gate-result identity, full transcript identity, Done event's closure hash and source-state identity. Text identities use the documented CRLF-to-LF policy, not raw checkout hashes. The stored transcript contains all eight passing stages; its reported 139 Python and four Rust tests were inspected, not independently rerun wholesale.

The independent six-test pipeline run passed with real guard interactions across Parquet, JSONL and EML, annotation content-ID joining, signed grouping, changed-label/checksum rejection, current revocation, rebound assignment rejection and fixture/Sinabis boundaries. Reviewer probes also confirmed all four prohibited pack-purpose selections reject, conflicting topics abstain while retaining independently assessed priority, and Sinabis near-pair enumeration agrees with exhaustive comparison on 160 deterministic sets (12,720 comparisons, 80 matches).

Source metadata is publisher-declared evidence, not forensic authorship or historical provider-account certification. The seed allowance remains specialist-only. Sinabis 10K is exact-source, conditional whole-case preparation; generic origins quarantine, all canonical dimensions remain missing, and 10M remains unadmitted. Commercial training, inference and public weight distribution remain separate decisions. No actual release clearance is implied. Fixture provider and consent declarations remain explicitly counterfactual; no model consumes their texts or labels. Current signed authority and complete source/thread/duplicate/family components are mandatory under the unchanged split policy. No additional reproducible code/security blocker was established within this review.

## Commands, evidence and limits

From `C:/GitHub/FDEmailClassifier`, both commands exited 0:

```powershell
& C:/GitHub/FDEmailClassifier/.venv/ingestion/Scripts/python.exe -B Tasks/epics/FDEC-EPIC-D002/reviews/R001/check-identities-v1.py
& C:/GitHub/FDEmailClassifier/.venv/ingestion/Scripts/python.exe -B Tasks/epics/FDEC-EPIC-D002/reviews/R001/probe-scope-v1.py
```

From the detached candidate, this command exited 0 under monitor `7567417d-08ff-4e92-8fce-564b4a3e7d97`: six tests in 39.545 seconds, no truncated output. Full output is in `pipeline-output-v1.txt`; probe observations are in `probe-results-v1.json` and both executable proof scripts accompany this result.

```powershell
C:/GitHub/FDEmailClassifier/.venv/ingestion/Scripts/python.exe -B -m unittest discover -s tests/d002 -p test_pipeline.py -v
```

Environment: Windows PowerShell, approved existing CPython 3.14.5/PyArrow 26.0.1 runtime. An initial exploratory unquoted PowerShell `HEAD^{tree}` command was misparsed and failed; the quoted form and read-only verifier independently confirmed the exact tree. No passing evidence is attributed to that failed invocation. Later FDEC-014 metadata is absent from the frozen candidate as expected.

Primary web checks accessed [Anthropic's specialist-classifier clarification](https://support.claude.com/en/articles/12326764-can-i-use-my-outputs-to-train-an-ai-model) and [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode.en). These support the documented limited interpretations; they do not authenticate upstream accounts or source authorship. Browser access to both pinned Hugging Face README URLs failed, so their remote bytes were not independently re-fetched. Rights assessment additionally relies on the hash-bound public observations and audits. No corpus or model was read/downloaded, and the private Sinabis preparation measurements were not independently regenerated. Actual legal permission, real annotation quality, semantic paraphrase independence, training readiness, accuracy and artifact release remain unverified. Upstream FDTasks redistribution rights remain a release limitation.

Cleanup: pipeline fixtures completed their guarded cleanup; reviewer probes created no corpus/output fixtures. Detached checkout remains clean and retained. Only new reviewer-owned files in this R001 folder were written; existing main-worktree IDE/executor files were preserved. No task state, accepted record, request, implementation, policy, consent anchor or source registry was changed. No purchase, external message, publication or model training occurred. FDEC-014 and D002 must not close on this result.
