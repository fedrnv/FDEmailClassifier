# Original native template grammar v1

The `fdec-native-templates-v1` software candidate is a distinct original grammar
with six language resources: en/de/ru/es/zh/ar. See
[its separate rights assessment](NATIVE-RIGHTS-v1.md). Its original code is
Apache-2.0; it is currently admitted for software fixtures only and does not
resolve FDEC-011's commercial-training requirement.

The existing v1 fixture renderer remains supported without changing its catalog,
audit, license evidence or purpose restrictions. A separate native catalog schema
`fdec-native-parallel-grammar/v1` uses typed, bounded placeholders and forbids
attribute/index access, format conversions and arbitrary input text. Unknown
fields, missing label resources, contacts or external URLs in templates reject.
Every language supplies two original facts for each of the twelve canonical
topics, subject forms, greetings/closings, notes and priority/action/security cues.
Rendering combines those resources through four body layouts; diversity is
measured from actual structural choices, not only generated reference numbers.

The native renderer uses only numeric seed/index and canonical language/topic
controls. It fabricates FDEC-PERSON/SENDER/ACCOUNT/PROJECT/ITEM/CASE identifiers,
test-credit amounts, calendar dates and `person-<id>@mail.invalid` addresses.
They are not sampled real names, accounts or emails. Date values are fictional
scenario metadata, not current events or real appointment information.
Native output has schema `fdec-native-synthetic-email/v1`; its receipt uses
`fdec-native-augmentation-receipt/v1`. Message bodies remain in ignored private
output directories; the repository stores only original grammar/code resources.

A 48-position cycle covers all four priorities and three security labels per
topic, with all four actions in normal cases. Phishing simulations require review
and spam simulations require archive. Matching cues occur in the rendered text.
The same seed/topic/index selects the same labels, artificial identity and fact
in every language. The default native plan requests 3,456 software fixtures over
72 language/topic cells. It is a reproducible test plan, not measured weak-class
counts or an approved dataset. Real augmentation must still use measured deficits.

Generation validates each native row against exact regeneration before writing
any completion receipt. The quality report checks annotations/provenance, detects
full normalized text duplicates, counts structural variants, records label
coverage and identifies template families. It reports no human language review or
model accuracy. Short templates and compositional combinations are not evidence
of natural-email diversity or a validated training distribution.

Descriptor-only translation uses the existing verified capsule protocol. It
preserves artificial identities, labels, origin and template-family links; the
source parent ID must also correspond to an actual reproducible language variant.
No real message can be submitted for translation. No external model is invoked.

`native_templates.validate_partition` reuses the accepted FDEC-012 component
policy. Source peers, template families and translations cannot cross partitions.
One native pack is one source, so putting its own rows in both train and test is
rejected. This pack alone cannot provide three independent source-held-out
splits. A source-approved corpus and current consent authority are still needed
for real manifests; this software check does not bypass those admission controls
or modify accepted FDEC-012. It never claims that a one-pack train/test split is
safe merely because its reference IDs differ.

The catalog interface accepts up to 128 vetted language resources, and the quota
interface supports 1,536 cells, enough for 119 resources times twelve topics.
The [Qwen3 announcement](https://qwenlm.github.io/blog/qwen3/) describes 119
languages **and dialects**; that is not 119 completed translations in this pack.
Each extension needs an exact resource ID/script, complete topic/cue grammar,
provenance/rights review, bilingual semantic review and boundary tests. Private-use
IDs in capacity tests only demonstrate parser/quota limits, not linguistic
coverage. Missing resources fail instead of silently substituting English.

For software verification run:

```powershell
powershell -NoProfile -File training/augmentation/test-native.ps1
```

It runs existing fixture regressions and native-only checks. Software tests render
no real personal data and do not train a model. Temporary artifacts are removed.
The positive commercial_training prerequisite is checked separately and remains
unmet until documented applicable rights exist; a denial is not task completion.
