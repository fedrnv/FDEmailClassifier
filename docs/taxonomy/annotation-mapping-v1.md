# Training annotation mapping v1

`training/labels/map_annotations.py` maps annotation metadata into the existing
[classification v1 taxonomy](../api/classification-v1.md). It does not classify
message text, perform an action, authorize a source, or assert model quality.
The twelve topics, four assessed priorities, three security classes and four
advisory actions retain their existing meanings. Runtime schema v1 is unchanged.

The output uses `fdec-annotation-mapping/v1`, a fixed profile version and the
canonical-LF SHA256 of the mapping implementation. Its structural contract is
[annotation-mapping-v1.schema.json](../../schemas/annotation-mapping-v1.schema.json).
Changing mapping semantics requires a new version; the implementation hash also
distinguishes bug fixes within that version. It is private training metadata:
original labels and source-round strings can contain sensitive information.
Never log the returned metadata or place actual annotations in Git.

## Inputs and rights boundary

Call `map_normalized_record(record)` on the verified normalized output from
[FDEC-009 ingestion](../../training/datasets/INGESTION.md). Only its schema,
content ID, source identity and annotations are consumed. Subject/body are neither
read nor copied. Mapping does not replace verification of the ingestion receipt,
artifact checksums, allowlist, purpose, provenance or future sanitization rules.
It never downloads or writes data. An invalid call raises a static `MappingError`
without logging labels or mutating input. Results contain copies of source data.

The lower-level `map_annotations(content_id=..., source=..., annotations=...)`
accepts the same source identity and source-row annotation list. Each annotation
has a nonnegative unique `source_row`, a `labels` object and optional `source_round`.
The annotation list is nonempty and bounded at 100,000; labels are bounded strings
with no control characters. Unknown fields, invalid types and duplicate row
identities reject. New source vocabulary is retained as `unmapped` rather than
silently accepted as a canonical label. Matching is exact and case-sensitive.

Two explicit source profiles are supported:

| Profile | Identity and permitted input |
| --- | --- |
| `canonical/v1` | Local `fdec/canonical-annotations`, revision `1`, artifact `annotations.jsonl`, SHA256 supplied by the audited caller. This is a contract for explicitly annotated local data, not an approval for arbitrary external datasets. Labels may contain `category`, topic `labels`, `priority`, `action`, `security`, `status`. |
| `triage-seed/v1` | `weijianzhg/email-triage-action-seed`, revision `8c98baa8b10a1dddd676c860d9e1b86c89141c38`, artifact `data/train.parquet`, SHA256 `9ea7c656d016012f7e800a9612d399114ca081bfcbdce4101d1999cb6c293854`. Only its declared `category`, `priority`, `action` columns are accepted. |

Unapproved source identities (including imnim and talby), changed seed revisions,
artifacts or hashes reject. The local profile cannot be selected merely by
changing an external dataset's display name: doing so violates the caller's
provenance contract and does not grant ingestion rights.

The seed vocabulary comes from its [pinned author card](https://huggingface.co/datasets/weijianzhg/email-triage-action-seed/blob/8c98baa8b10a1dddd676c860d9e1b86c89141c38/README.md),
whose SHA256 is `2bb851c855d60a96ef3f648bb078afd0d09f280486bdbac0e0a090ec4fa64aaa`
in the [rights audit](../legal/datasets/audit-2026-11-20.md). These are project
mapping decisions, not an upstream claim that the taxonomies are equivalent.
No row contents or third-party generator code are copied into this implementation.

## Topics

Local canonical `category` is a topic; `labels` is an explicitly asserted
multi-label topic list. The two fields are combined within a single annotation.
All twelve canonical topics map identically; repeated labels are collapsed.
`other` is supported only when explicitly supplied. It is never an uncertainty
fallback. A mixed list containing an unrecognized label retains known candidates
but is not supervised as a complete multi-label target.

| Seed category | Canonical topic decision |
| --- | --- |
| finance, travel, personal | Corresponding identical topic |
| newsletter | newsletters |
| promotion | marketing; no spam assessment |
| meeting_request | Ambiguous candidates work/social; no topic target |
| customer_support | Ambiguous candidates work/shopping; no topic target |
| system_update | Unmapped; insufficient topical specificity |
| spam, phishing | Security evidence only; topic missing |
| unknown or empty string | Explicit topic unknown |
| Any new value | Unmapped, preserved in original annotation |

Ambiguous candidates are alternatives, not multi-label positive targets.
No text heuristics, guessed class frequencies or majority votes resolve them.

## Priority, security and action

Local priority labels low/normal/high/urgent and action labels
none/review/reply/archive map identically. Seed priorities low/high/urgent map
identically and medium maps to normal. No absent priority defaults to normal.

| Seed action | Project advisory interpretation |
| --- | --- |
| reply | reply |
| archive | archive |
| flag | review: attention requested, not execution of a mailbox flag |
| ignore | none: no suggested action, not deletion or mark-as-read |
| forward, mark_read | Unmapped; v1 has no corresponding action |

Local `security: normal` is an explicit annotation of spam and phishing as clear.
`security: spam` or `phishing` flags only that dimension. The other remains
unassessed. The seed spam/phishing categories flag only the corresponding
dimension; ordinary seed categories never imply clear. Malware always remains
unknown for these profiles. Security assessments are independent of topic,
priority and action. Clear is a label, not a guarantee of safety.

The special field value `unknown` or empty string retains unknown evidence;
`abstain` deliberately withholds that field. Missing, unknown, abstained,
unmapped and ambiguous remain distinct. Unsupported actions and security labels
do not become negative or no-action training examples.

## Consensus, masks and runtime projection

Every original annotation is copied with its source row and round. Results are
ordered by source row for reproducibility. Each dimension records a `state`,
known `values` or candidate alternatives, and a `supervise` flag indicating
mapped evidence. Missing annotations do not contradict an observed value.
Any disagreement among nonmissing annotations, including explicit uncertainty,
becomes ambiguous. No annotation is dropped; no majority vote is taken. Different
multi-label sets remain conflicting sets rather than a union of positive labels.

The top-level `training_mask` is authoritative for each independent training
head. Never train from wire fallbacks. When a topic alone is unknown, supported
priority/action or security heads can still be trained from `dimensions`, even
though the safe wire projection withholds priority/action. An explicit local
`status: unknown` or `abstained` disables topic/priority/action masks. Conflicting
statuses force abstention. Independently observed security evidence is retained.

The `classification` field is a safe existing v1 projection. Mapped topics give
classified status; missing/unknown topics give unknown; unmapped/ambiguous or
deliberately withheld topics give abstained. Unknown and abstained projections
have empty topics, unknown priority and review action. Classified records with
unsupported or missing actions also project review, with action training disabled.
Security conflicts project unknown with supervision disabled. A review fallback
is not an observed label. There is no automatic mailbox operation or deployment.

## Local verification

Run `powershell -NoProfile -File training/labels/test-mapping.ps1` with CPython
3.14 and the existing locally cached `ajv-cli@5.0.0`. Ajv runs offline, as a
disposable local verifier, and adds no production dependency. The suite covers
all canonical enums, the pinned seed vocabulary, missing and contradictory
labels, explicit withholding, source binding, malformed metadata, input
immutability and the metadata-only ingestion bridge. It independently checks
generated mapping JSON and classification projections with JSON Schema and
rejects malformed output fixtures. Only synthetic label metadata is generated
under ignored `training/outputs`; the test wrapper removes its own fixture run.
There are no hosted acceptance tests, corpus downloads, training or publication.
