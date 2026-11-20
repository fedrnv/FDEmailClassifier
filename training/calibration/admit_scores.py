"""Current independently reviewed score/label admission; no self-approval CLI."""
from datetime import datetime, timezone
import hashlib
import hmac
from pathlib import Path
import sys

from calibrate import ROOT, CalibrationError, validate, SCORE_KIND
for area in ("training/splits", "training/augmentation"):
    sys.path.insert(0, str(ROOT / area))
import split_data as splits
import training_boundary as boundary
from ingest_dataset import strict_json

ANCHOR = "training/data/calibration-review/current.json"
DOMAIN = b"fdec-calibration-score-review/v1\0"


def admit(*, inventory_path, consent_path, split_dir, observations_path, source_runs, key, policy_root=ROOT, now=None):
    try:
        fixed_now = now
        now = datetime.now(timezone.utc) if now is None else now
        inventory, signed = splits.read_json(inventory_path), splits.read_json(consent_path)
        split = splits.verify(split_dir, inventory, signed, key=key, policy_root=policy_root, now=now, include_manifest=True)
        records = {row["record_id"]: row for row in inventory["records"]}
        expected = {row["provenance"]["ingestion_receipt_sha256"] for row in records.values()}
        seen, replayed_ids = set(), set()
        if not isinstance(source_runs, list) or not 1 <= len(source_runs) <= len(records):
            raise ValueError()
        for directory in source_runs:
            receipt = splits.read_json(Path(directory) / "receipt.json", 65536)
            receipt_id = splits.digest(receipt)
            if receipt_id not in expected or receipt_id in seen:
                raise ValueError()
            replayed = boundary.admit_training_run(directory, purpose=receipt["input"]["purpose"], policy_root=policy_root, include_records=True)
            if receipt != splits.read_json(Path(directory) / "receipt.json", 65536):
                raise ValueError()
            identity = {name: receipt["input"][name] for name in ("dataset_id", "revision", "artifact", "sha256")}
            for purpose in ("commercial_training", "evaluation"):
                boundary.assert_training_source(identity, purpose=purpose, policy_root=policy_root)
            seen.add(receipt_id)
            for normalized in replayed["records"]:
                rid = splits.digest([identity, normalized["content_id"], sorted(item["source_row"] for item in normalized["annotations"])])
                if rid in records:
                    record = records[rid]
                    if splits.prepare_record(normalized, receipt, consent_id=record["consent_id"], thread_id=record["thread_id"], family_ids=record["family_ids"]) != record or rid in replayed_ids:
                        raise ValueError()
                    replayed_ids.add(rid)
        if seen != expected or replayed_ids != set(records):
            raise ValueError()
        raw = splits.read_bytes(observations_path, 50_000_000)
        bundle = strict_json(raw.decode("utf-8-sig", errors="strict"))
        validate(bundle)
        boundary.prohibit_codex_training(bundle["model"]["id"], bundle["model"]["id"], "evaluation")
        assignments = {row["record_id"]: row for row in split["manifest"]["assignments"] if row["split"] in ("validation", "test")}
        if {row["record_id"] for row in bundle["rows"]} != set(assignments):
            raise ValueError()
        for row in bundle["rows"]:
            assigned = assignments[row["record_id"]]
            if row["role"] != assigned["split"] or row["group_id"] != assigned["group_id"]:
                raise ValueError()
        review = splits.read_json(Path(policy_root) / ANCHOR, 65536)
        if not isinstance(review, dict) or set(review) != {"schema", "payload", "hmac_sha256"} or review["schema"] != "fdec-signed-calibration-review/v1" or not splits.is_hash(review["hmac_sha256"]):
            raise ValueError()
        payload = review["payload"]
        if not hmac.compare_digest(review["hmac_sha256"], hmac.new(key, DOMAIN + splits.canonical_json(payload).encode(), hashlib.sha256).hexdigest()):
            raise ValueError()
        fields = {"schema", "inventory_sha256", "consent_sha256", "split_receipt_sha256", "observations_sha256", "score_kind", "origin", "evidence_sha256", "issued_at", "valid_until"}
        if not isinstance(payload, dict) or set(payload) != fields or payload["schema"] != "fdec-calibration-score-review/v1" or payload["origin"] != "independently-reviewed-non-openai" or payload["score_kind"] != SCORE_KIND or not splits.is_hash(payload["evidence_sha256"]) or not splits.utc(payload["issued_at"]) <= now < splits.utc(payload["valid_until"]):
            raise ValueError()
        bindings = dict(inventory_sha256=splits.digest(inventory), consent_sha256=splits.digest(signed), split_receipt_sha256=splits.digest(split["receipt"]), observations_sha256=hashlib.sha256(raw).hexdigest())
        if any(payload[name] != value for name, value in bindings.items()):
            raise ValueError()
        end_now = datetime.now(timezone.utc) if fixed_now is None else fixed_now
        splits.consent(inventory, signed, key, end_now)
        if not splits.utc(payload["issued_at"]) <= end_now < splits.utc(payload["valid_until"]) or splits.read_json(Path(policy_root) / ANCHOR, 65536) != review:
            raise ValueError()
        splits.active_consent(policy_root, signed, key)
        return bundle, dict(**bindings, review_sha256=splits.digest(review))
    except Exception:
        raise CalibrationError("calibration_score_admission_rejected") from None
