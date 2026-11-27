# FDEC-087 Mac training and held-out quality

The Apple M4 run completed 1,500 native MLX LoRA optimizer updates on
1,950 reviewed training examples. The weighted schedule made 6,000 visits.
Independent CPU readback authenticated 150 checkpoint receipts and verified
resumption from step 10. The exact training source was
`91f4696c8b1513904e9b86fbeccc7fd2fe6a1bed`. The historical execution used the
FDTasks 5.6 policy with SHA-256
`ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403`.

## Held-out evaluation

The final configuration was selected on validation data before admission of
the fresh test cohort. It uses two previously measured Qwen3-0.6B adapters
for the general heads and the prior calibrated spam and phishing heads.
The newest 1,500-step checkpoint was evaluated on validation as a candidate.
The selected configuration scored 1,653 held-out emails in English, German,
French and Italian on the Mac. All outputs satisfied the v1 schema.
Independent CPU replay authenticated all 104 prediction blocks and reproduced
the masked metrics. Denominators differ because an email can have reviewed
labels for only some fields.

| Measurement | Result |
| --- | --- |
| Topics | Micro-F1 0.8763 and macro-F1 0.2134 across the 12-category taxonomy |
| Suggested action | 316 of 619 correct (51.1%). An always-archive baseline scores 428 of 619 on the same labels. |
| Priority | 1,450 of 1,560 correct (92.9%), including 24 of 32 high-priority examples. An always-normal baseline scores 1,528 of 1,560 and detects none of the high-priority examples. |
| Spam | 0 of 6 positives flagged, 1 of 1,557 reviewed clean examples flagged and 289 of 1,563 decisions made |
| Phishing | 0 of 5 positives flagged, 0 of 1,623 reviewed clean examples flagged and 161 of 1,628 decisions made |
| Malware | No reviewed positive examples and no decisions on 1,648 eligible emails |

The classifier abstained on all 11 spam and phishing positives. These results
describe this cohort and the frozen configuration. The topic output consists
of category labels. Moving emails in a mailbox requires a consuming integration.

## Local package and remaining acceptance

The private package contains checked PEFT and GGUF variants, the frozen
runtime contract, selected specialist weights and calibration, source notices,
aggregate metrics and a CycloneDX 1.6 SBOM. Independent CPU review authenticated
39 payload files totaling 4,050,248,343 bytes and reproduced the direct numeric
portability checks for the two selected adapters.

| Protected evidence | SHA-256 |
| --- | --- |
| Terminal optimizer checkpoint receipt | `b3507c477723abfc16e6dbd434e7b4f15beb33b38eb538fedc778264b31c991f` |
| Frozen validation selection | `2ed3378fbfada0cd3c09b31fbea8e28b64b13e7e0b1c71833f4a1f7b863f4f24` |
| Final held-out report | `a38b390a6a382ea194ef5e286c81292d7b268b4bc0f1f517054b679adf851b49` |
| Independent final metric replay | `eed7a6e986513dfa64cfffe880168626bb89a2af6bb3c27e5051cd2a9f251244` |
| Evaluated package manifest | `c5c9711c7c0e2fb8155ca8337cccf50c16de0e2300179540e1af407c8f024689` |

The original Windows workstation previously verified the numerical transfer
fixture. Verification of the actual trained artifact on that workstation
remains open under FDEC-087. The supported-GPU check under FDEC-016 and the
D003 integration and independent acceptance tasks FDEC-020 and FDEC-021
remain open.

This is an aggregate engineering report. The release-policy registry has no
accepted audit for the trained artifacts. Public weight distribution requires
artifact-specific rights and verification under the product release policy.
