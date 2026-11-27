"""Independent-source admission; Codex examples remain software fixtures only."""

from contextlib import closing
import hashlib
import io
from pathlib import Path
import re
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import ingest_dataset as ingestion
from normalize_email import VERSION, canonical_json, deduplicate

POLICY_PATH = "training/config/independent-training-sources-v1.json"
FIXTURE_PACKS = frozenset(("codex-fixture-v1", "fdec-native-templates-v1"))
PURPOSES = ("commercial_training", "evaluation")
PROVIDERS = ("anthropic-via-openrouter-uploader-declared", "human-authored-reviewed", "non-openai-model-reviewed")


class TrainingBoundaryError(ValueError):
    """Static diagnostics without data, labels, input paths or parser excerpts."""


def prohibit_codex_training(pack_id, origin, purpose):
    if purpose in PURPOSES and (pack_id in FIXTURE_PACKS or isinstance(origin, str) and re.match(r"(?:codex|openai|gpt)(?:$|[-_/ :])", origin.casefold())):
        raise TrainingBoundaryError("openai_derived_training_data_forbidden")


def text_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read_json(path, limit=1_000_000):
    try:
        path = ingestion.reject_links(path)
        with path.open("rb") as source:
            data = source.read(limit + 1)
        if len(data) > limit:
            raise TrainingBoundaryError("training_proof_size_limit")
        return ingestion.strict_json(data.decode("utf-8-sig", errors="strict"))
    except TrainingBoundaryError:
        raise
    except Exception:
        raise TrainingBoundaryError("invalid_training_proof") from None


def bound(root, binding):
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"} or not isinstance(binding["path"], str) or not isinstance(binding["sha256"], str):
        raise TrainingBoundaryError("invalid_independent_source_binding")
    relative = binding["path"]
    if not re.fullmatch(r"docs/legal/datasets/[^/]+\.(?:json|md)|training/augmentation/DATA-USAGE-v2\.md", relative):
        raise TrainingBoundaryError("independent_source_binding_escapes_scope")
    path = ingestion.reject_links(Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()) or not path.is_file() or text_hash(path) != binding["sha256"]:
        raise TrainingBoundaryError("independent_source_evidence_changed")
    return path


def assert_training_source(identity, *, purpose, policy_root=ROOT):
    """Rights/origin only. Split integrity and consent remain separate requirements."""
    try:
        if purpose not in PURPOSES:
            raise TrainingBoundaryError("unsupported_training_purpose")
        if not isinstance(identity, dict) or set(identity) != {"dataset_id", "revision", "artifact", "sha256"} or any(not isinstance(value, str) for value in identity.values()):
            raise TrainingBoundaryError("invalid_training_source_identity")
        if identity["dataset_id"] == "sinabis-group/sinabis-10k-synthetic-emails":
            # A separate exact-artifact CC BY review; the legacy guard is not
            # broadened and no unfiltered Sinabis ingestion receipt is admitted.
            from sinabis_source import assert_source
            return assert_source(identity, purpose=purpose, policy_root=policy_root)
        policy = read_json(Path(policy_root) / POLICY_PATH)
        if not isinstance(policy, dict) or set(policy) != {"schema", "scope", "codex_data_usage", "policy_evidence", "sources"} or policy["schema"] != "fdec-independent-training-sources/v1" or policy["scope"] != "specialized-email-classifier" or policy["codex_data_usage"] != "software_fixture_only" or not isinstance(policy["sources"], list):
            raise TrainingBoundaryError("invalid_independent_source_policy")
        bound(policy_root, policy["policy_evidence"])
        identities = set()
        selected = None
        for entry in policy["sources"]:
            if not isinstance(entry, dict) or set(entry) != {"identity", "authoring_provider", "openai_derived", "allowed_purposes", "evidence"} or not isinstance(entry["identity"], dict) or set(entry["identity"]) != set(identity):
                raise TrainingBoundaryError("invalid_independent_source_entry")
            key = canonical_json(entry["identity"])
            if key in identities:
                raise TrainingBoundaryError("duplicate_independent_source")
            identities.add(key)
            if entry["identity"] == identity:
                selected = entry
        if selected is None:
            raise TrainingBoundaryError("unapproved_independent_source")
        if selected["openai_derived"] is not False or selected["authoring_provider"] not in PROVIDERS or not isinstance(selected["allowed_purposes"], list) or set(selected["allowed_purposes"]) != set(PURPOSES) or len(selected["allowed_purposes"]) != 2 or not isinstance(selected["evidence"], list) or len(selected["evidence"]) < 3:
            raise TrainingBoundaryError("independent_source_origin_not_admitted")
        for evidence in selected["evidence"]:
            bound(policy_root, evidence)
        # The origin policy adds restrictions, never replaces the license guard.
        descriptor = ingestion.inclusion(identity["dataset_id"], identity["revision"], identity["artifact"], purpose, policy["scope"], policy_root)
        if descriptor["sha256"] != identity["sha256"]:
            raise TrainingBoundaryError("independent_source_artifact_changed")
        return {"schema": "fdec-independent-source-admission/v1", "descriptor": descriptor, "origin_policy_sha256": text_hash(Path(policy_root) / POLICY_PATH), "authoring_provider": selected["authoring_provider"], "scope": "source-integrity-and-origin-only", "requires_split_and_consent": True}
    except TrainingBoundaryError:
        raise
    except Exception:
        raise TrainingBoundaryError("independent_source_admission_failed") from None


def byte_hash(path, limit):
    digest = hashlib.sha256()
    length = 0
    path = ingestion.reject_links(path)
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            length += len(chunk)
            if length > limit:
                raise TrainingBoundaryError("training_artifact_size_limit")
            digest.update(chunk)
    return digest.hexdigest(), length


class FrozenArtifact:
    """The shared ingestion decoder reads exactly the bytes whose hash passed."""
    def __init__(self, data, suffix):
        self.data = data
        self.suffix = suffix

    def open(self, mode):
        if mode != "rb":
            raise TrainingBoundaryError("training_snapshot_is_read_only")
        return io.BytesIO(self.data)

    def read_bytes(self):
        return self.data

    def read_text(self, encoding, errors):
        return self.data.decode(encoding, errors=errors)

    def stat(self):
        return SimpleNamespace(st_size=len(self.data))


def admit_training_run(run_directory, *, purpose="commercial_training", policy_root=ROOT, include_records=False):
    """Return a verified snapshot only from current audited non-OpenAI ingestion."""
    try:
        directory = ingestion.reject_links(run_directory)
        receipt = read_json(directory / "receipt.json", 65536)
        if isinstance(receipt, dict) and receipt.get("schema") == "fdec-sinabis-reviewed-run/v1":
            from sinabis_source import replay_run

            expected, records = replay_run(directory / "source.parquet", purpose=purpose, policy_root=policy_root)
            if receipt != expected:
                raise TrainingBoundaryError("sinabis_training_receipt_changed")
            result = {"schema": "fdec-independent-training-admission/v1",
                      "records_sha256": receipt["records_sha256"], "rows": len(records),
                      "scope": "source-integrity-and-origin-only", "requires_split_and_consent": True}
            if include_records:
                result["records"] = records
            return result
        required = {"schema", "normalization_version", "implementation_sha256", "python_version", "decoder", "input", "source_file", "records_file", "records_sha256", "input_rows", "unique_rows", "duplicates", "annotation_conflicts"}
        if not isinstance(receipt, dict) or receipt.get("schema") != "fdec-ingestion-receipt/v1":
            raise TrainingBoundaryError("technical_fixture_not_training_data")
        if set(receipt) != required or receipt["normalization_version"] != VERSION or not isinstance(receipt["input"], dict) or not {"dataset_id", "revision", "artifact", "sha256", "purpose"} <= set(receipt["input"]):
            raise TrainingBoundaryError("unsupported_training_ingestion_proof")
        if receipt["input"]["purpose"] != purpose:
            raise TrainingBoundaryError("training_ingestion_purpose_changed")
        identity = {name: receipt["input"][name] for name in ("dataset_id", "revision", "artifact", "sha256")}
        admitted = assert_training_source(identity, purpose=purpose, policy_root=policy_root)
        if admitted.get("requires_origin_projection"):
            raise TrainingBoundaryError("reviewed_source_requires_dedicated_preparation")
        if receipt["input"] != admitted["descriptor"]:
            raise TrainingBoundaryError("training_ingestion_rights_changed")
        implementation = hashlib.sha256()
        for name in ("ingest_dataset.py", "normalize_email.py"):
            implementation.update((ROOT / "training/scripts" / name).read_bytes().replace(b"\r\n", b"\n"))
        suffix = Path(identity["artifact"]).suffix.lower()
        if receipt["implementation_sha256"] != implementation.hexdigest() or receipt["source_file"] != "source" + suffix or receipt["records_file"] != "records.jsonl" or receipt["decoder"] != ("pyarrow/" + ingestion.PYARROW_VERSION if suffix == ".parquet" else "python-stdlib"):
            raise TrainingBoundaryError("training_ingestion_implementation_changed")
        source_path = directory / receipt["source_file"]
        source_path = ingestion.reject_links(source_path)
        with source_path.open("rb") as source:
            source_bytes = source.read(admitted["descriptor"]["size"] + 1)
        if (hashlib.sha256(source_bytes).hexdigest(), len(source_bytes)) != (identity["sha256"], admitted["descriptor"]["size"]):
            raise TrainingBoundaryError("training_source_checksum_mismatch")
        # Regenerate text AND annotations from pinned independent bytes, so copied
        # Codex labels cannot be hidden behind an updated normalized-file checksum.
        with closing(ingestion.rows(FrozenArtifact(source_bytes, suffix))) as source_rows:
            records, count = deduplicate(source_rows, identity)
        expected_hash = hashlib.sha256()
        for record in records:
            expected_hash.update((canonical_json(record) + "\n").encode("utf-8"))
        normalized_hash, _ = byte_hash(directory / "records.jsonl", 250_000_000)
        if receipt["records_sha256"] != expected_hash.hexdigest() or normalized_hash != expected_hash.hexdigest():
            raise TrainingBoundaryError("normalized_training_text_or_labels_changed")
        counters = {"input_rows": count, "unique_rows": len(records), "duplicates": count - len(records), "annotation_conflicts": sum(row["annotation_conflict"] for row in records)}
        if any(type(receipt[name]) is not int or receipt[name] != expected for name, expected in counters.items()):
            raise TrainingBoundaryError("training_ingestion_counts_changed")
        result = {"schema": "fdec-independent-training-admission/v1", "source": admitted, "records_sha256": normalized_hash, "rows": len(records), "scope": "source-integrity-and-origin-only", "requires_split_and_consent": True}
        if include_records:
            result["records"] = records
        return result
    except TrainingBoundaryError:
        raise
    except Exception:
        raise TrainingBoundaryError("training_source_verification_failed") from None
