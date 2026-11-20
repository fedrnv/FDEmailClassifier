"""Versioned, metadata-only training annotation mapping; no mailbox effects."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
VERSION = "fdec-annotation-mapping/v1"
TOPICS = ("work", "personal", "finance", "shopping", "travel", "social", "newsletters", "marketing", "education", "health", "legal", "other")
PRIORITIES = ("low", "normal", "high", "urgent")
ACTIONS = ("none", "review", "reply", "archive")
DIMENSIONS = ("topics", "priority", "spam", "phishing", "malware", "action")
SEED_ID = "weijianzhg/email-triage-action-seed"
SEED_REVISION = "8c98baa8b10a1dddd676c860d9e1b86c89141c38"
SEED_HASH = "9ea7c656d016012f7e800a9612d399114ca081bfcbdce4101d1999cb6c293854"


class MappingError(ValueError):
    """Static diagnostic codes only; caller data must never enter errors."""


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def decision(state="missing", values=()):
    return {"state": state, "values": sorted(set(values)), "supervise": state == "mapped"}


def token(value):
    if not isinstance(value, str) or len(value) > 256:
        raise MappingError("invalid_label")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        raise MappingError("invalid_label") from None
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise MappingError("invalid_label")
    # Exact source vocabulary: no fuzzy matching, case folding or semantic guess.
    return value


def scalar(value, table):
    value = token(value)
    if value in ("", "unknown"):
        return decision("unknown")
    if value == "abstain":
        return decision("abstained")
    return deepcopy(table.get(value, decision("unmapped")))


def profile(source):
    if not isinstance(source, dict) or set(source) != {"dataset_id", "revision", "artifact", "sha256"}:
        raise MappingError("invalid_source")
    if any(not isinstance(value, str) or len(value) > 256 for value in source.values()) or not re.fullmatch("[a-f0-9]{64}", source["sha256"]):
        raise MappingError("invalid_source")
    if source["dataset_id"] == SEED_ID:
        if source != dict(dataset_id=SEED_ID, revision=SEED_REVISION, artifact="data/train.parquet", sha256=SEED_HASH):
            raise MappingError("unsupported_source_revision")
        return "triage-seed/v1"
    if source["dataset_id"] == "fdec/canonical-annotations" and source["revision"] == "1" and source["artifact"] == "annotations.jsonl":
        return "canonical/v1"
    raise MappingError("unsupported_source")


def one_annotation(annotation, selected):
    if not isinstance(annotation, dict) or not {"source_row", "labels"} <= set(annotation) or set(annotation) - {"source_row", "labels", "source_round"}:
        raise MappingError("invalid_annotation")
    if type(annotation["source_row"]) is not int or not 0 <= annotation["source_row"] < 100_000:
        raise MappingError("invalid_source_row")
    if "source_round" in annotation:
        token(annotation["source_round"])
    labels = annotation["labels"]
    allowed = {"category", "priority", "action"} if selected == "triage-seed/v1" else {"category", "labels", "priority", "action", "security", "status"}
    if not isinstance(labels, dict) or set(labels) - allowed:
        raise MappingError("unsupported_annotation_fields")
    dimensions = {name: decision() for name in DIMENSIONS}
    status = "classified"
    if "status" in labels:
        status = token(labels["status"])
        if status not in ("classified", "unknown", "abstained"):
            raise MappingError("invalid_status")
    if selected == "canonical/v1":
        supplied = []
        if "category" in labels:
            supplied.append(token(labels["category"]))
        if "labels" in labels:
            if not isinstance(labels["labels"], list) or len(labels["labels"]) > 32:
                raise MappingError("invalid_topic_labels")
            supplied.extend(token(value) for value in labels["labels"])
        if supplied:
            if all(value in TOPICS for value in supplied):
                dimensions["topics"] = decision("mapped", supplied)
            else:
                state = "abstained" if "abstain" in supplied else "unknown" if all(value in ("", "unknown") for value in supplied) else "unmapped"
                dimensions["topics"] = decision(state, [value for value in supplied if value in TOPICS])
        elif "labels" in labels:
            dimensions["topics"] = decision("unknown")
        priority_table = {value: decision("mapped", [value]) for value in PRIORITIES}
        action_table = {value: decision("mapped", [value]) for value in ACTIONS}
        if "security" in labels:
            security = token(labels["security"])
            for dimension in ("spam", "phishing"):
                # "normal" is a local explicit assessment of these two tasks;
                # it says nothing about malware, language or topic quality.
                table = {"normal": decision("mapped", ["clear"]), dimension: decision("mapped", ["flagged"])}
                dimensions[dimension] = scalar(security, table)
    else:
        category_table = {
            "finance": decision("mapped", ["finance"]), "travel": decision("mapped", ["travel"]),
            "newsletter": decision("mapped", ["newsletters"]), "promotion": decision("mapped", ["marketing"]),
            "personal": decision("mapped", ["personal"]),
            "meeting_request": decision("ambiguous", ["work", "social"]),
            "customer_support": decision("ambiguous", ["work", "shopping"]),
            "system_update": decision("unmapped"), "spam": decision("missing"), "phishing": decision("missing"),
        }
        if "category" in labels:
            category = token(labels["category"])
            dimensions["topics"] = scalar(category, category_table)
            if category in ("spam", "phishing"):
                dimensions[category] = decision("mapped", ["flagged"])
        priority_table = {value: decision("mapped", ["normal" if value == "medium" else value]) for value in ("low", "medium", "high", "urgent")}
        action_table = {value: decision("mapped", [target]) for value, target in (("reply", "reply"), ("archive", "archive"), ("flag", "review"), ("ignore", "none"))}
    for field in ("priority", "action"):
        if field in labels:
            dimensions[field] = scalar(labels[field], priority_table if field == "priority" else action_table)
    return {"source_annotation": deepcopy(annotation), "status": status, "dimensions": dimensions}


def consensus(decisions):
    # Missing evidence is not a contradiction. Explicit uncertainty is retained.
    observed = [item for item in decisions if item["state"] != "missing"]
    if not observed:
        return decision()
    if len({canonical(item) for item in observed}) == 1:
        return deepcopy(observed[0])
    return decision("ambiguous", [value for item in observed for value in item["values"]])


def validate_projection(value):
    if set(value) != {"schema_version", "status", "topics", "priority", "security", "suggested_action"} or value["schema_version"] != "1":
        raise MappingError("invalid_projection")
    if value["status"] not in ("classified", "unknown", "abstained") or value["priority"] not in (*PRIORITIES, "unknown") or value["suggested_action"] not in ACTIONS:
        raise MappingError("invalid_projection")
    if not isinstance(value["topics"], list) or any(item not in TOPICS for item in value["topics"]) or len(set(value["topics"])) != len(value["topics"]):
        raise MappingError("invalid_projection")
    if set(value["security"]) != {"spam", "phishing", "malware"} or any(item not in ("unknown", "clear", "flagged") for item in value["security"].values()):
        raise MappingError("invalid_projection")
    if value["status"] == "classified":
        if not value["topics"]:
            raise MappingError("invalid_projection")
    elif value["topics"] or value["priority"] != "unknown" or value["suggested_action"] != "review":
        raise MappingError("invalid_projection")


def map_annotations(*, content_id, source, annotations):
    """Return private metadata. Mapping is not source licensing or ingestion admission."""
    if not isinstance(content_id, str) or not re.fullmatch("[a-f0-9]{64}", content_id):
        raise MappingError("invalid_content_id")
    selected = profile(source)
    if not isinstance(annotations, list) or not 1 <= len(annotations) <= 100_000:
        raise MappingError("invalid_annotations")
    mapped = [one_annotation(item, selected) for item in annotations]
    if len({item["source_annotation"]["source_row"] for item in mapped}) != len(mapped):
        raise MappingError("duplicate_source_row")
    mapped.sort(key=lambda item: item["source_annotation"]["source_row"])
    dimensions = {name: consensus([item["dimensions"][name] for item in mapped]) for name in DIMENSIONS}
    statuses = {item["status"] for item in mapped}
    topic_state = dimensions["topics"]["state"]
    if "abstained" in statuses or len(statuses) > 1:
        status = "abstained"
    elif statuses == {"unknown"}:
        status = "unknown"
    elif topic_state == "mapped":
        status = "classified"
    else:
        status = "unknown" if topic_state in ("missing", "unknown") else "abstained"
    projection = {"schema_version": "1", "status": status, "topics": [], "priority": "unknown", "security": {name: dimensions[name]["values"][0] if dimensions[name]["supervise"] else "unknown" for name in ("spam", "phishing", "malware")}, "suggested_action": "review"}
    if status == "classified":
        projection["topics"] = sorted(dimensions["topics"]["values"], key=TOPICS.index)
        for dimension, field in (("priority", "priority"), ("action", "suggested_action")):
            if dimensions[dimension]["supervise"]:
                projection[field] = dimensions[dimension]["values"][0]
    validate_projection(projection)
    # Masks apply to independent training heads. The wire projection's review
    # fallback is never supervision. Explicit status withholding disables the
    # topic/priority/action heads but retains observed security evidence.
    masks = {name: value["supervise"] for name, value in dimensions.items()}
    if statuses != {"classified"}:
        for name in ("topics", "priority", "action"):
            masks[name] = False
    return {"schema": VERSION, "profile": selected, "mapping_sha256": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), "content_id": content_id, "source": deepcopy(source), "annotations": mapped, "dimensions": dimensions, "training_mask": masks, "classification": projection}


def map_normalized_record(record):
    """Bridge FDEC-009 output without copying or inspecting the message content."""
    if not isinstance(record, dict) or record.get("schema") != "fdec-normalized-email/v1" or not {"content_id", "source", "annotations"} <= set(record):
        raise MappingError("invalid_normalized_record")
    return map_annotations(content_id=record["content_id"], source=record["source"], annotations=record["annotations"])
