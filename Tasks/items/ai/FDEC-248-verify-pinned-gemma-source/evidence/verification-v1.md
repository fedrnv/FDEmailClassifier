# FDEC-248 pinned Gemma source verification

The inspected candidate was `809e0c8eb4b33e2ccb7ee9d2e38adf7c7979baac`.
Manual publication followed FDTasks 5.7. The local admission validator
used its qualified 5.6 policy. Verification used Apple Silicon macOS,
CPython 3.14.10, PyArrow 26.0.1 and PowerShell 7.7.0.

The 21,844,808-byte JSONL artifact was verified before decoding. Its SHA-256
is `349c6afd429f2d55eaaece9794ee0a9d625771e4369c8fb45c5e8392f6af31c7`.
The pinned 551-byte publisher card matched the historical SHA-256
`59fcae5f2d8d7414f8751213a5ca39e34ad58eaf89df7e6a4df688cb0305da58`.
The card declares Apache-2.0 and describes generation with Gemma 3-4B-it
through an MLX conversion. The card gives no independent generator
attestation or exact generating-model revision. Section 3.3 of Google's
terms disclaims claims to generated outputs and assigns responsibility for
subsequent use. Treat this as bounded source evidence for guarded replay.
Training still requires admitted reviewed inputs and separate consent.
Any proposed dataset or trained-weight distribution needs its own review.
[Pinned publisher card](https://huggingface.co/datasets/Kamisori-daijin/email-datasets-20k/blob/7c615780b64770697e8e517c9d3e70db470cadf1/README.md)
· [Gemma terms](https://gemma.ai/resources/terms/)
· [Google prohibited-use policy](https://policies.google.com/terms/generative-ai/use-policy)

| Criterion | Local result |
| --- | --- |
| AC-01 | The inspector replayed 19,849 source rows and retained 19,839 distinct normalized pairs. It excluded one record for output structure and nine for contact or URL patterns. Exact matching against 3,905 triage and 9,387 Sinabis rows found zero overlaps. The deterministic sample of 32 candidate rows found zero near matches at Jaccard 0.8 against either previous run. The aggregate was byte-identical to the historical audit. |
| AC-02 | An exact-size altered input failed the identity check before parsing. The committed inspector and aggregate expose only the method, fixed artifact identity, opaque digests and counts. |

The test sample cannot establish absence of near duplicates outside those
32 candidates. The screening does not establish absence of PII or confer
permission for individual records. Guarded production integration must
replay the exact source, verify consent and perform complete grouping for
its admitted inventory.

Executed locally with the pinned interpreter.

```sh
python "$ITEM/evidence/inspect-v1.py" --self-test
python "$ITEM/evidence/inspect-v1.py" "$PRIVATE_ARTIFACT" \
  --prior-run "$PRIVATE_TRIAGE_RUN" --prior-run "$PRIVATE_SINABIS_RUN"
```

Aggregate SHA-256
`c94e31d7a8e211ef646fd24be00ccd6e890602871410bd57c1349d253d850dad`.
Historical source bytes were read from protected storage. No decoded
rows or labels were persisted or published and no model ran.
