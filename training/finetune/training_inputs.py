"""Training-only frozen admission; no evaluation rows or Codex-generated gold."""
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
from disk_inventory import DiskInventory
from source_replay import record_matcher
import training_boundary as boundary
from baseline_metrics import validate_gold
from ingest_dataset import strict_json
from trainer_config import TrainerError

REVIEW_ANCHOR = "training/data/training-review/current.json"
DOMAIN = b"fdec-training-label-review/v1\0"


@dataclass
class Inputs:
    inventory: dict | DiskInventory
    consent: dict
    split: dict
    rows: list
    texts: dict
    system: str
    annotations_sha256: str
    prompt_sha256: str
    review_sha256: str


def check_review(review, inventory, consent, split, annotations_sha256, prompt_sha256, key, now):
    try:
        if not isinstance(review, dict) or set(review) != {"schema", "payload", "hmac_sha256"} or review["schema"] != "fdec-signed-training-review/v1" or not splits.is_hash(review["hmac_sha256"]):
            raise ValueError()
        payload = review["payload"]
        expected = hmac.new(key, DOMAIN + splits.canonical_json(payload).encode(), hashlib.sha256).hexdigest()
        fields = {"schema", "inventory_sha256", "consent_sha256", "split_receipt_sha256", "annotations_sha256", "prompt_sha256", "reviewer_kind", "evidence_sha256", "issued_at", "valid_until"}
        if not hmac.compare_digest(expected, review["hmac_sha256"]) or not isinstance(payload, dict) or set(payload) != fields or payload["schema"] != "fdec-training-label-review/v1" or payload["reviewer_kind"] != "independently-reviewed-non-openai" or not splits.is_hash(payload["evidence_sha256"]):
            raise ValueError()
        bindings = dict(inventory_sha256=splits.inventory_digest(inventory), consent_sha256=splits.digest(consent), split_receipt_sha256=splits.digest(split["receipt"]), annotations_sha256=annotations_sha256, prompt_sha256=prompt_sha256)
        if any(payload[name] != value for name, value in bindings.items()) or not splits.utc(payload["issued_at"]) <= now < splits.utc(payload["valid_until"]):
            raise ValueError()
    except Exception:
        raise TrainerError("training_review_not_current") from None


def admit(*, inventory_path, consent_path, split_dir, annotations_path, prompt_path, source_runs, key, policy_root=ROOT, now=None):
    try:
        now = datetime.now(timezone.utc) if now is None else now
        inventory, signed = splits.read_inventory(inventory_path), splits.read_json(consent_path)
        split = splits.verify(split_dir, inventory, signed, key=key, policy_root=policy_root, now=now, include_manifest=True)
        records = {row["record_id"]: row for row in splits.inventory_rows(inventory)}
        expected = {row["provenance"]["ingestion_receipt_sha256"] for row in records.values()}
        if not isinstance(source_runs, list) or not 1 <= len(source_runs) <= len(records):
            raise TrainerError("invalid_training_source_runs")
        seen, texts = set(), {}
        with record_matcher(inventory) as matches:
            for directory in source_runs:
                receipt = splits.read_json(Path(directory) / "receipt.json", 65536)
                receipt_id = splits.digest(receipt)
                if receipt_id not in expected or receipt_id in seen:
                    raise TrainerError("unexpected_training_source_run")
                replayed = boundary.admit_training_run(directory, purpose=receipt["input"]["purpose"], policy_root=policy_root, include_records=True)
                if splits.read_json(Path(directory) / "receipt.json", 65536) != receipt:
                    raise TrainerError("training_receipt_changed")
                identity = {name: receipt["input"][name] for name in ("dataset_id", "revision", "artifact", "sha256")}
                boundary.assert_training_source(identity, purpose="commercial_training", policy_root=policy_root)
                seen.add(receipt_id)
                for normalized in replayed["records"]:
                    rid = splits.digest([identity, normalized["content_id"], sorted(item["source_row"] for item in normalized["annotations"])])
                    if rid not in records:
                        continue
                    target = records[rid]
                    prepared = splits.prepare_record(normalized, receipt, consent_id=target["consent_id"], thread_id=target["thread_id"], family_ids=target["family_ids"])
                    if not matches(prepared, target) or rid in texts:
                        raise TrainerError("training_text_binding_changed")
                    texts[rid] = (normalized["subject"], normalized["body"])
        if seen != expected or set(texts) != set(records):
            raise TrainerError("incomplete_training_source_inventory")
        raw = splits.read_bytes(annotations_path, 50_000_000)
        annotations = strict_json(raw.decode("utf-8-sig", errors="strict"))
        if not isinstance(annotations, dict) or set(annotations) != {"schema", "rows"} or annotations["schema"] != "fdec-training-annotations/v1" or not isinstance(annotations["rows"], list) or not 1 <= len(annotations["rows"]) <= splits.MAX_ROWS:
            raise TrainerError("invalid_training_annotations")
        rows = [validate_gold(row) for row in annotations["rows"]]
        # Whole-JSON SFT cannot turn unknown heads into targets. Partial masks
        # fail explicitly in v1; they are never filled from heuristic mappings.
        if any(not all(row["mask"].values()) for row in rows):
            raise TrainerError("whole_json_training_requires_fully_reviewed_heads")
        train_ids = {row["record_id"] for row in split["manifest"]["assignments"] if row["split"] == "train"}
        if len({row["record_id"] for row in rows}) != len(rows) or {row["record_id"] for row in rows} != train_ids:
            raise TrainerError("annotations_not_exact_train_partition")
        prompt_raw = splits.read_bytes(prompt_path, 65536)
        prompt = strict_json(prompt_raw.decode("utf-8-sig", errors="strict"))
        if not isinstance(prompt, dict) or set(prompt) != {"schema", "system", "origin"} or prompt["schema"] != "fdec-independent-training-prompt/v1" or prompt["origin"] != "independently-reviewed-non-openai" or not isinstance(prompt["system"], str) or not 1 <= len(prompt["system"]) <= 8192:
            raise TrainerError("independent_training_prompt_required")
        annotations_sha256, prompt_sha256 = hashlib.sha256(raw).hexdigest(), hashlib.sha256(prompt_raw).hexdigest()
        review = splits.read_json(Path(policy_root) / REVIEW_ANCHOR, 65536)
        check_review(review, inventory, signed, split, annotations_sha256, prompt_sha256, key, now)
        result = Inputs(inventory, signed, split, sorted(rows, key=lambda row: row["record_id"]), {rid: texts[rid] for rid in train_ids}, prompt["system"], annotations_sha256, prompt_sha256, splits.digest(review))
        recheck(result, key=key, policy_root=policy_root, now=now)
        return result
    except TrainerError:
        raise
    except Exception:
        raise TrainerError("training_input_admission_failed") from None


def recheck(snapshot, *, key, policy_root=ROOT, now=None):
    try:
        now = datetime.now(timezone.utc) if now is None else now
        splits.active_consent(policy_root, snapshot.consent, key)
        allowed, _ = splits.consent(snapshot.inventory, snapshot.consent, key, now)
        if not set(snapshot.texts) <= allowed:
            raise ValueError()
        for identity in {splits.canonical_json(row["source"]): row["source"] for row in splits.inventory_rows(snapshot.inventory)}.values():
            for purpose in ("commercial_training", "evaluation"):
                boundary.assert_training_source(identity, purpose=purpose, policy_root=policy_root)
        review = splits.read_json(Path(policy_root) / REVIEW_ANCHOR, 65536)
        if splits.digest(review) != snapshot.review_sha256:
            raise ValueError()
        check_review(review, snapshot.inventory, snapshot.consent, snapshot.split, snapshot.annotations_sha256, snapshot.prompt_sha256, key, now)
    except Exception:
        raise TrainerError("training_authority_changed") from None
