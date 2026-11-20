# Multilingual synthetic augmentation infrastructure

Status: software implementation candidate; **FDEC-011 is not complete**.
The only checked-in source pack is a software fixture, not approved training or
evaluation data. See [the source rights assessment](RIGHTS.md). It must not feed
model training, including through a later reuse of fixture annotations.

This standard-library Python tool builds messages from original parallel phrase
resources, bounded generated case identifiers and explicit annotation metadata.
It makes no remote generation or translation calls, reads no mailbox, and has no
interface for importing a real message for translation. There are no third-party
model weights or generation-time dependencies. Shared path/privacy helpers come
from the completed ingestion implementation; production Rust APIs are unchanged.

## Source admission

`training/config/augmentation-sources-v1.json` is the trusted repository registry.
It binds each pack's catalog and rights audit by canonical-LF SHA256. The audit
also binds the original source license/notice and explanatory evidence, declares
authoring provenance, confirms no real-mail inputs and states the allowed
purposes. Every generation and translation checks those identities before output.
No CLI option can approve a source or replace a rights audit.

The current `codex-fixture-v1` pack permits only `software_fixture`.
`commercial_training`, `evaluation`, redistribution and unrecognized purposes
reject before output creation. A declared Apache-2.0 source-code license does
not override these purpose restrictions. Every receipt and sample marks training
disallowed. Adding a genuinely approved pack is a separate audited repository
change, with evidence applicable to the source and intended model distribution.
It is not enough to edit its purpose string. The software does not authenticate
a repository writer or establish legal facts independently of that audit.

## Quota planning and rendering

Plans use `fdec-augmentation-plan/v1` with an integer `seed` and nonempty `quotas`.
Each cell has exactly `language`, canonical `topic`, integer `target` and aggregate
integer `observed`. Generation creates `max(target - observed, 0)` rows per cell;
it never reads the counted messages. Duplicate cells, unknown languages/topics,
extra fields, malformed numbers and excessive work reject. Targets are bounded
at 1,000 per cell and total output at 10,000. A satisfied plan deliberately emits
an empty run with an explicit zero-row receipt, rather than silently claiming
that messages were generated.

The demonstration default has 72 cells across en/de/ru/es/zh/ar and all twelve
topics. It requests 288 fixture rows, with higher illustrative targets for
education/health/legal/other. Its observed zeros are not measured dataset counts
or proof of weakness. A real approved run needs measured aggregate counts and a
source pack admitted for its intended use.

There are two scenario variants per topic in each language, plus corresponding
priority, action and security phrases. The seed/topic/index hash selects the
same controls in every language. Priority has explicit urgency cues. Spam and
phishing simulations add matching cues; phishing advises review and spam advises
archive. Normal examples carry no automatically asserted malware assessment.
Case identifiers are generated, not personal names or real addresses. Catalog
validation rejects contacts, digits, control/format characters, HTML and URL
schemes; any domain must end in `.invalid`. The audited catalog, rather than a
universal PII detector, is the trust boundary for the remaining text.

These short compositional examples are not a diverse natural-email corpus.
Every record is marked `quality_review: required`. Script identifiers describe
the configured resources, not detected language confidence. There is no measured
per-language classification quality, human linguistic sign-off or 119-language
coverage claim. Increase diversity only through audited and reviewed sources.

## Private local commands

With CPython 3.14, an explicit software-fixture run is:

```powershell
py -3.14 training/augmentation/generate.py `
  --plan training/config/augmentation-default-v1.json `
  --pack-id codex-fixture-v1 --purpose software_fixture --opt-in `
  --output-dir training/outputs/augmentation-fixture-001
```

Translation accepts only `fdec-synthetic-capsule/v1` JSONL descriptors containing
enum controls, numeric seed/index and identity hashes. It regenerates the source
and verifies the entire descriptor before rendering the target language from
the same audited parallel pack. It never accepts arbitrary subject/body text.
This is template translation, not a general machine-translation engine.

```powershell
py -3.14 training/augmentation/translate_synthetic.py `
  --capsules training/outputs/augmentation-fixture-001/capsules.jsonl `
  --source-language en --language ru `
  --pack-id codex-fixture-v1 --purpose software_fixture --opt-in `
  --output-dir training/outputs/augmentation-fixture-ru-001
```

The source-language slice prevents multiple parallel inputs from collapsing into
duplicate target messages. All input descriptors, including excluded languages,
are still validated. Empty selections, tampered descriptors, duplicate targets
and changed generator/catalog/audit identities reject. An unsupported language
requires a reviewed source-resource change, not a remote fallback.

New output directories must be private: inside this repository only ignored
training/data or training/outputs paths are accepted; an external directory must
be outside any Git repository. Existing directories and linked paths reject.
The writer exclusively creates its run and writes `samples.jsonl`,
`capsules.jsonl`, `annotations.jsonl`, then `receipt.json` last. Receipt hashes
bind every stream and its row count. A random ownership marker guards rollback;
normal failures remove only the newly owned run. Abrupt termination may leave an
incomplete private run: consumers must require and verify the completion receipt.
No result is published automatically. CLI output contains only counts, hashes
and the training permission flag; errors use static codes without input text.

## Provenance and later integration

Records bind the generator version/implementation, source registry, catalog,
rights audit, declared license, authoring origin, purpose and rendering controls.
`origin_id` links parallel instances with the same seed/topic/index;
`family_id` conservatively groups all cosmetic variants of the same catalog
scenario, even across seeds and languages. `translation_parent_id` records the
immediate source identity. These are inputs for later leakage-safe splitting,
not a completed split policy. Do not split the parallel or template family
members independently.

`annotations.jsonl` contains content IDs and canonical source-row annotations.
Its receipt supplies an actual hash-bound `annotation_source` compatible with
FDEC-010's local canonical profile. Mapping validates the annotation shape, not
source rights. In particular, valid fixture labels must never be mistaken for
training-approved data merely because the mapper accepts their structure.
Callers must retain the receipt's purpose, training flag and rights provenance.

## Focused verification

Run `powershell -NoProfile -File training/augmentation/test-augmentation.ps1`.
Only software fixtures are rendered, under ignored disposable directories.
The checks cover quota deficits, all languages/classes, repeatability, translation
semantics and family IDs, canonical metadata compatibility, rights refusals,
malformed input, no network calls, static diagnostics and rollback. A passing
software suite does not satisfy the task's unresolved source-rights requirement.
