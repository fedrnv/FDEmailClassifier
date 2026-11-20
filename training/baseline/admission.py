"""Fail-closed held-out admission. No signing or source-approval CLI is exposed."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
for relative in ("training/scripts", "training/splits", "training/augmentation", "training/eval"):
    sys.path.insert(0, str(ROOT / relative))
import split_data as splits
import training_boundary as boundary
from baseline_metrics import EvaluationError, validate_gold
from ingest_dataset import strict_json

REVIEW_ANCHOR = "training/data/baseline-review/current.json"
REVIEW_DOMAIN = b"fdec-baseline-label-review/v1\0"


@dataclass
class Snapshot:
    inventory: dict
    consent: dict
    split: dict
    gold: list
    texts: dict
    annotations_sha256: str
    review_sha256: str


def review_check(review, inventory, signed, split, annotations_sha256, key, now):
    """Trusted operator attestation, not automatic proof of annotation truth.

    The externally protected current anchor binds review provenance and expiry
    to these exact bytes. Possession of the authority key is the trust boundary;
    software cannot establish real-world authorship from a signature alone.
    """
    try:
        if not isinstance(review, dict) or set(review) != {"schema", "payload", "hmac_sha256"} or review["schema"] != "fdec-signed-baseline-review/v1" or not splits.is_hash(review["hmac_sha256"]):
            raise ValueError()
        payload = review["payload"]
        expected = hmac.new(key, REVIEW_DOMAIN + splits.canonical_json(payload).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, review["hmac_sha256"]):
            raise ValueError()
        fields = {"schema", "inventory_sha256", "consent_sha256", "split_receipt_sha256", "annotations_sha256", "reviewer_kind", "evidence_sha256", "issued_at", "valid_until"}
        if not isinstance(payload, dict) or set(payload) != fields or payload["schema"] != "fdec-baseline-label-review/v1" or payload["reviewer_kind"] != "independently-reviewed-non-openai" or not splits.is_hash(payload["evidence_sha256"]):
            raise ValueError()
        bindings = dict(inventory_sha256=splits.digest(inventory), consent_sha256=splits.digest(signed), split_receipt_sha256=splits.digest(split["receipt"]), annotations_sha256=annotations_sha256)
        if any(payload[name] != value for name, value in bindings.items()) or not splits.utc(payload["issued_at"]) <= now < splits.utc(payload["valid_until"]):
            raise ValueError()
    except Exception:
        raise EvaluationError("independent_label_review_not_current") from None


def admit(*, inventory_path, consent_path, split_dir, annotations_path, source_runs, key, policy_root=ROOT, now=None):
    """Return frozen, replayed text only for the verified test partition.

    policy_root and now are library seams for isolated counterfactual software
    tests. The production CLI exposes neither. Existing license/origin/consent
    and split checks are reused and unchanged, including both fixture denials.
    """
    try:
        now = datetime.now(timezone.utc) if now is None else now
        inventory, signed = splits.read_json(inventory_path), splits.read_json(consent_path)
        split = splits.verify(split_dir, inventory, signed, key=key, policy_root=policy_root, now=now, include_manifest=True)
        records = {row["record_id"]: row for row in inventory["records"]}
        expected_receipts = {row["provenance"]["ingestion_receipt_sha256"] for row in records.values()}
        seen, texts = set(), {}
        if not isinstance(source_runs, list) or not 1 <= len(source_runs) <= len(records):
            raise EvaluationError("invalid_source_run_set")
        for directory in source_runs:
            receipt = splits.read_json(Path(directory) / "receipt.json", 65536)
            receipt_id = splits.digest(receipt)
            if receipt_id in seen or receipt_id not in expected_receipts:
                raise EvaluationError("unexpected_source_run")
            snapshot = boundary.admit_training_run(directory, purpose=receipt["input"]["purpose"], policy_root=policy_root, include_records=True)
            if splits.read_json(Path(directory) / "receipt.json", 65536) != receipt:
                raise EvaluationError("source_receipt_changed")
            identity = {name: receipt["input"][name] for name in ("dataset_id", "revision", "artifact", "sha256")}
            boundary.assert_training_source(identity, purpose="evaluation", policy_root=policy_root)
            seen.add(receipt_id)
            for normalized in snapshot["records"]:
                record_id = splits.digest([identity, normalized["content_id"], sorted(item["source_row"] for item in normalized["annotations"])])
                if record_id not in records:
                    continue
                target = records[record_id]
                replay = splits.prepare_record(normalized, receipt, consent_id=target["consent_id"], thread_id=target["thread_id"], family_ids=target["family_ids"])
                if replay != target or record_id in texts:
                    raise EvaluationError("inventory_text_binding_changed")
                texts[record_id] = (normalized["subject"], normalized["body"])
        if seen != expected_receipts or set(texts) != set(records):
            raise EvaluationError("source_inventory_not_complete")
        raw = splits.read_bytes(annotations_path, 50_000_000)
        annotations_sha256 = hashlib.sha256(raw).hexdigest()
        annotations = strict_json(raw.decode("utf-8-sig", errors="strict"))
        if not isinstance(annotations, dict) or set(annotations) != {"schema", "rows"} or annotations["schema"] != "fdec-baseline-annotations/v1" or not isinstance(annotations["rows"], list) or not 1 <= len(annotations["rows"]) <= splits.MAX_ROWS:
            raise EvaluationError("invalid_independent_annotations")
        gold = [validate_gold(row) for row in annotations["rows"]]
        test_ids = {row["record_id"] for row in split["manifest"]["assignments"] if row["split"] == "test"}
        if len({row["record_id"] for row in gold}) != len(gold) or {row["record_id"] for row in gold} != test_ids:
            raise EvaluationError("gold_is_not_exact_test_partition")
        if len({row["language"] for row in gold}) < 2:
            raise EvaluationError("multilingual_held_out_required")
        review = splits.read_json(Path(policy_root) / REVIEW_ANCHOR, 65536)
        review_check(review, inventory, signed, split, annotations_sha256, key, now)
        result = Snapshot(inventory, signed, split, sorted(gold, key=lambda row: row["record_id"]), {rid: texts[rid] for rid in test_ids}, annotations_sha256, splits.digest(review))
        recheck(result, key=key, policy_root=policy_root, now=now)
        return result
    except EvaluationError:
        raise
    except Exception:
        raise EvaluationError("held_out_admission_failed") from None


def recheck(snapshot, *, key, policy_root=ROOT, now=None):
    """Recheck current rights/authority before each use and before publishing."""
    now = datetime.now(timezone.utc) if now is None else now
    try:
        splits.active_consent(policy_root, snapshot.consent, key)
        allowed, _ = splits.consent(snapshot.inventory, snapshot.consent, key, now)
        if not set(snapshot.texts) <= allowed:
            raise ValueError()
        for identity in {splits.canonical_json(row["source"]): row["source"] for row in snapshot.inventory["records"]}.values():
            for purpose in ("commercial_training", "evaluation"):
                boundary.assert_training_source(identity, purpose=purpose, policy_root=policy_root)
        review = splits.read_json(Path(policy_root) / REVIEW_ANCHOR, 65536)
        if splits.digest(review) != snapshot.review_sha256:
            raise ValueError()
        review_check(review, snapshot.inventory, snapshot.consent, snapshot.split, snapshot.annotations_sha256, key, now)
    except Exception:
        raise EvaluationError("held_out_authority_changed") from None
