# FDEC-010 acceptance verification

Command: `powershell -NoProfile -File training/labels/test-mapping.ps1`.
Final monitored task a4f48e36-ae32-4940-a962-2f3c0f330fd5 completed with exit 0.
Source revision and tree are recorded in result.json and closure-readiness.json.
Policy SHA256: ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Environment: Windows x64, CPython 3.14.5, Node 24.22.1 and existing cached
ajv-cli 5.0.0. Standard-library training implementation; no new runtime package.

AC-01 PASS: 21 semantic tests cover all 12 topics, four assessed priorities,
normal/spam/phishing annotations and four actions. Canonical metadata maps
directly; the pinned seed's supported labels map by the documented policy.
Ambiguous seed topics retain alternative candidates; unsupported actions never
become asserted canonical targets. Missing, explicit unknown, abstained, unmapped
and contradictory annotations remain distinguishable. Source-row annotations
and rounds are retained without majority voting or false positive label unions.
Independent masks preserve useful assessed heads while withholding unsupported
ones. Explicit status abstention preserves security evidence. Safe classification
v1 projection obeys existing cross-field restrictions and is advisory only.

Independent Ajv validation accepted 28 generated mapping metadata records and
their 28 classification projections. Five invalid output fixtures were rejected
(future version, inconsistent mapped-state flag, unsafe action, noncanonical
priority, unexpected field). Existing runtime schema bytes were not changed.

AC-02 PASS: malformed types/fields, duplicate source rows, empty annotations,
invalid controls/UTF-8 labels, unsupported source identities, changed revisions,
artifacts and hashes reject with static MappingError codes and no payload logs.
Tests verify original input preservation and output copy isolation. The bridge
ignores body/subject and does not copy message content. Unknown source labels
remain private provenance with disabled supervision rather than disappearing.
The mapping API performs no transfer, file write, action or publication.

Initial run failed one negative fixture because it contained literal backslash-n
instead of an actual control character. initial-test-output.txt records that run.
The fixture was corrected, preserving the implementation's exact-vocabulary
behavior, and the complete suite passed. Stored logs normalize trailing whitespace
only; outcomes and diagnostics are retained.

Generated schema fixtures contained synthetic label metadata only, lived in an
ignored training/outputs run, and were removed by the wrapper's bounded cleanup.
No emails or dataset rows were downloaded or committed. Only the pinned public
author card was fetched to verify its declared vocabulary, with its existing
audit hash confirmed in source-card-observation.json; no card body is committed.
Rights admission and receipt verification remain mandatory caller prerequisites;
this mapping does not authorize ingestion or create new source rights.

Scope remains training/labels, the new metadata schema and docs/taxonomy, plus
own task events/evidence/version request. No split generation, privacy policy,
training, hosted acceptance, publication, deployment or Epic review is claimed.
