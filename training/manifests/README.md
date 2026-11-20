# Consent ledger authority for split manifests

This is a technical record/control contract, not a determination of external
privacy or license rights. A trusted data owner/preparer must record the actual
permission basis, verify upstream ingestion provenance, preserve relationships
and provide the explicit ledger. The source inclusion guard remains mandatory.
No real permissions, personal identity mappings, email bodies or keys belong in
this repository. The production CLI does not fabricate or infer consent.

The private `fdec-consent-ledger/v1` payload contains:

| Field | Contract |
| --- | --- |
| revision | Positive integer, increasing by one on activation |
| previous_snapshot_sha256 | Null for revision 1; canonical SHA256 of the previous signed envelope thereafter |
| inventory_sha256 | Canonical JSON SHA256 of the exact private split inventory |
| issued_at, valid_until | UTC second timestamps (`YYYY-MM-DDTHH:MM:SSZ`) bounding validity |
| grants | Unique per-record decisions; omitted entries are denied |

Each grant has `record_id`, matching opaque `consent_id`, `evidence_sha256`,
`status` (granted/revoked), `purposes` (commercial_training and/or evaluation)
and `expires_at`. The training pipeline requires both purposes. Revoked,
partially scoped, expired or missing decisions quarantine all related records.
Unknown values, duplicates, invalid evidence hashes, out-of-snapshot record IDs
and invalid time ranges reject. Revocation does not require granting another
purpose, so a revoked entry can have an empty purpose list.

The `fdec-signed-consent/v1` envelope holds `payload` and `hmac_sha256` over its
canonical UTF-8 JSON. Authorized signers and trusted consumers share a 32-byte
secret via `FDEC_CONSENT_KEY`. HMAC authenticates that trust boundary; it is not
encryption, public-key identity proof or independent proof of a person's consent.
Keep the authority key, protected current-anchor directory and original evidence
under the data owner's access controls. A key holder can sign new decisions;
untrusted clients must not receive the signing key or write access to authority.

`sign_consent.py` signs an explicitly drafted payload and checks it against the
inventory. Its output path must be new, private and outside the current anchor.
It never creates default grants or sends any data to a service. The optional
`--activate` performs the separately explicit current-state update in the same
authorized local operation; it is not a new permission request to the user.

```powershell
py -3.14 training/manifests/sign_consent.py `
  --inventory training/data/prepared/inventory.json `
  --payload training/data/prepared/consent-draft.json `
  --output training/data/prepared/consent-signed-002.json --activate
```

Prepare the containing private output directory first. The environment supplies
the existing authority key; the script does not print or generate a production
key. Signing alone does not activate an archive or authorize a source. Every
build/verification compares its supplied envelope against the fixed trusted
`training/data/consent/current.json` anchor.

Activation verifies the signature, inventory binding, current time and explicit
grants, then requires the next revision and previous-snapshot identity. It writes
an immutable `revision-<n>-<hash>.json` history file and atomically replaces only
the current pointer. An exclusive local lock prevents simultaneous activation;
failed writes preserve the prior pointer. Exact retries are safe, including an
archive written before a failed pointer replacement. An already active identical
snapshot is an idempotent operation. Revisions cannot be skipped, rolled back or
silently attached to another parent.

After abrupt process termination, an activation lock may require reconciliation
by the authority owner. Do not treat a lock file as proof of a running process
or remove another process's lock automatically. Signed history remains unchanged;
verify the pointer and actual process state before an authorized recovery.

A changed snapshot immediately makes older split manifests ineligible for use,
even if their signatures and immutable files remain intact. Build checks current
authority again before publishing completion; verification checks again before
returning a validated snapshot. This prevents archive replay under a newer
protected anchor. It cannot prevent deliberate rollback by an administrator who
controls that anchor and its trust boundary. Consumers must validate current
authority at actual data-use boundaries and honor revocation thereafter.
