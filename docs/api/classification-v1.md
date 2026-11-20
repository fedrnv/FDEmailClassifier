# Classification contract v1

`fdemailclassifier_core::schema::Classification` is the Serde output contract;
`schemas/classification-v1.schema.json` is its JSON Schema 2020-12 description.
Every field is required. Version is the string `"1"`. Unknown fields, enum values,
duplicate labels and missing fields are rejected. Duplicate JSON object keys are
rejected by direct Serde decoding; consumers must reject them before JSON Schema
validation, since object parsers may otherwise discard duplicates.

## Taxonomy

These twelve stable snake_case labels form an initial project taxonomy, not a
claim of model quality. Labels may co-occur; they are not mutually exclusive.

| Label | Meaning |
| --- | --- |
| work | Employment, projects and professional collaboration |
| personal | Personal correspondence and household matters |
| finance | Payments, banking, invoices and financial administration |
| shopping | Orders, receipts, delivery and purchase support |
| travel | Transport, accommodation and itineraries |
| social | Social interactions, invitations and community updates |
| newsletters | Periodic subscribed informational publications |
| marketing | Promotions, advertising and sales outreach |
| education | Learning, courses and academic administration |
| health | Healthcare and wellbeing administration |
| legal | Legal notices, agreements and compliance correspondence |
| other | Assessed content outside the preceding topics |

`other` is a topic, not an uncertainty fallback. `classified` requires one to
twelve unique labels. `unknown` means the topic could not be determined;
`abstained` means a decision was deliberately withheld. Both require empty topics,
`priority: "unknown"` and `suggested_action: "review"`. Existing security evidence
can be retained even when topic classification abstains.

Priority is unknown/low/normal/high/urgent. Security has separate required spam,
phishing and malware fields, each unknown/clear/flagged. Unknown means not
assessed; clear is an assessment, never a guarantee. Security is independent of
topic and priority: urgent content can be malicious, and marketing is not
automatically spam. No score, calibrated probability or language-quality claim
is implied by these labels. Inference thresholds and calibration are later tasks.

Suggested actions are none/review/reply/archive. They are advisory data only;
this module has no filesystem, mailbox or network effects. Clients must not treat
a recommendation as authorization. There is deliberately no delete/execute action.
This output contains no raw email, address, subject, explanation or model prompt.

Rust deserialization and serialization validate cross-field invariants; manually
constructed invalid values cannot be serialized through this contract. Call
`validate()` when consuming a manually constructed value before using it locally.
Validation returns static messages; callers must avoid logging arbitrary Serde
parser errors or payloads because third-party parser errors can quote input.

Examples in `schemas/examples` are synthetic metadata only. Topic order is
preserved but has no ranking semantics. JSON object key order is insignificant.
Changing fields, label meanings or accepted values requires a new schema version;
v1 rejects future versions instead of silently downgrading them. No released API
or stable C ABI existed before this contract.

Run `cargo test --locked --offline -p fdemailclassifier-core schema` locally.
For independent schema checks run `npm exec --yes --package=ajv-cli@5.0.0 -- ajv
validate --spec=draft2020 --strict=false -s schemas/classification-v1.schema.json
-d "schemas/examples/*.json"`. Ajv is a disposable local verification tool and
is not included in the production dependency graph or hosted build stages.
