"""Local synthetic-template infrastructure; never accepts real message content."""

import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
from ingest_dataset import private_output, reject_links, remove_owned, strict_json
from normalize_email import IngestionError

VERSION = "fdec-synthetic-augmentation/v1"
TOPICS = ("work", "personal", "finance", "shopping", "travel", "social", "newsletters", "marketing", "education", "health", "legal", "other")
PRIORITIES = ("low", "normal", "high", "urgent")
ACTIONS = ("none", "review", "reply", "archive")
SECURITY = ("normal", "spam", "phishing")
MAX_ROWS = 10_000
REGISTRY = ROOT / "training/config/augmentation-sources-v1.json"


class AugmentationError(ValueError):
    """Only static codes; never include supplied paths, labels or message text."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return sha(canonical(value).encode("utf-8"))


def file_hash(path):
    return sha(path.read_bytes().replace(b"\r\n", b"\n"))


def read_json(path, limit=1_000_000):
    try:
        path = reject_links(path)
        with path.open("rb") as source:
            data = source.read(limit + 1)
        if len(data) > limit:
            raise AugmentationError("input_size_limit")
        return strict_json(data.decode("utf-8-sig", errors="strict"))
    except AugmentationError:
        raise
    except Exception:
        raise AugmentationError("invalid_json_input") from None


def integer(value, maximum):
    return type(value) is int and 0 <= value <= maximum


def bound(binding):
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"} or not isinstance(binding["path"], str) or not isinstance(binding["sha256"], str):
        raise AugmentationError("invalid_pack_binding")
    path = reject_links(ROOT / binding["path"]).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file() or file_hash(path) != binding["sha256"]:
        raise AugmentationError("changed_pack_binding")
    return path


def phrase(value, empty=False):
    if not isinstance(value, str) or not (0 if empty else 1) <= len(value) <= 1024:
        raise AugmentationError("invalid_template_phrase")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        raise AugmentationError("invalid_template_phrase") from None
    if any(unicodedata.category(char).startswith("C") or char.isdigit() for char in value) or any(char in value for char in "@<>") or "://" in value:
        raise AugmentationError("unsafe_template_phrase")
    hosts = re.findall(r"\b[a-zA-Z][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}\b", value)
    if any(not host.endswith(".invalid") for host in hosts):
        raise AugmentationError("unsafe_template_domain")


def check_catalog(catalog):
    if isinstance(catalog, dict) and catalog.get("schema") == "fdec-native-parallel-grammar/v1":
        import native_templates
        native_templates.validate(catalog, sys.modules[__name__])
        return
    if not isinstance(catalog, dict) or set(catalog) != {"schema", "authorship", "license", "languages"} or catalog["schema"] != "fdec-original-parallel-templates/v1":
        raise AugmentationError("invalid_catalog")
    languages = catalog["languages"]
    if not isinstance(languages, dict) or not 1 <= len(languages) <= 128:
        raise AugmentationError("invalid_catalog_languages")
    for language, section in languages.items():
        if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z][a-z]{3})?", language) or not isinstance(section, dict) or set(section) != {"script", "case_prefix", "subjects", "scenarios", "priority", "action", "security"}:
            raise AugmentationError("invalid_catalog_language")
        if not isinstance(section["script"], str) or not re.fullmatch("[A-Z][a-z]{3}", section["script"]):
            raise AugmentationError("invalid_script")
        phrase(section["case_prefix"])
        for field, keys in (("subjects", TOPICS), ("scenarios", TOPICS), ("priority", PRIORITIES), ("action", ACTIONS), ("security", SECURITY)):
            if not isinstance(section[field], dict) or set(section[field]) != set(keys):
                raise AugmentationError("incomplete_parallel_catalog")
            for key, value in section[field].items():
                if field == "scenarios":
                    if not isinstance(value, list) or len(value) != 2 or any(not isinstance(item, str) for item in value) or len(set(value)) != 2:
                        raise AugmentationError("invalid_scenario_variants")
                    for item in value:
                        phrase(item)
                else:
                    phrase(value, empty=field == "security" and key == "normal")


def load_pack(pack_id, purpose):
    registry = read_json(REGISTRY)
    if not isinstance(registry, dict) or set(registry) != {"schema", "packs"} or registry["schema"] != "fdec-augmentation-sources/v1" or not isinstance(registry["packs"], list):
        raise AugmentationError("invalid_source_registry")
    entries = registry["packs"]
    if any(not isinstance(item, dict) or set(item) != {"id", "catalog", "audit", "allowed_purposes"} or not isinstance(item["id"], str) for item in entries) or len({item["id"] for item in entries}) != len(entries):
        raise AugmentationError("invalid_source_registry")
    selected = [item for item in entries if item["id"] == pack_id]
    if len(selected) != 1:
        raise AugmentationError("unapproved_template_pack")
    entry = selected[0]
    catalog_path, audit_path = bound(entry["catalog"]), bound(entry["audit"])
    audit = read_json(audit_path)
    required = {"schema", "pack_id", "catalog_sha256", "declared_source_license", "authoring_origin", "allowed_purposes", "real_mail_inputs", "training_scope", "redistribution", "license_file", "notice_file", "review", "evidence"}
    if not isinstance(audit, dict) or set(audit) != required or audit["schema"] != "fdec-augmentation-rights/v1" or audit["pack_id"] != pack_id or audit["catalog_sha256"] != entry["catalog"]["sha256"] or audit["real_mail_inputs"] is not False or audit["allowed_purposes"] != entry["allowed_purposes"]:
        raise AugmentationError("invalid_rights_audit")
    if not isinstance(audit["allowed_purposes"], list) or not audit["allowed_purposes"] or any(value not in ("software_fixture", "commercial_training", "evaluation") for value in audit["allowed_purposes"]) or audit["training_scope"] != "specialized-email-classifier" or audit["redistribution"] != "separate-review":
        raise AugmentationError("invalid_rights_scope")
    bound(audit["license_file"])
    bound(audit["notice_file"])
    bound(audit["evidence"])
    from training_boundary import prohibit_codex_training, TrainingBoundaryError
    try:
        prohibit_codex_training(pack_id, audit["authoring_origin"], purpose)
    except TrainingBoundaryError:
        raise AugmentationError("template_training_rights_not_approved") from None
    # Ownership of generated source code does not silently grant training rights.
    if purpose not in audit["allowed_purposes"]:
        raise AugmentationError("template_training_rights_not_approved")
    catalog = read_json(catalog_path)
    check_catalog(catalog)
    if catalog["license"] != audit["declared_source_license"] or catalog["authorship"] != audit["authoring_origin"]:
        raise AugmentationError("catalog_rights_mismatch")
    implementation_files = ["augment.py", "generate.py", "translate_synthetic.py", "training_boundary.py"]
    if catalog["schema"] == "fdec-native-parallel-grammar/v1":
        implementation_files.append("native_templates.py")
    implementation = sha(b"".join((ROOT / "training/augmentation" / name).read_bytes().replace(b"\r\n", b"\n") for name in implementation_files))
    context = {"generator_version": VERSION, "implementation_sha256": implementation, "registry_sha256": file_hash(REGISTRY), "catalog_sha256": file_hash(catalog_path), "audit_sha256": file_hash(audit_path), "pack_id": pack_id, "purpose": purpose}
    return {"catalog": catalog, "audit": audit, "context": context, "context_sha256": digest(context)}


def render(pack, *, topic, language, seed, index):
    if pack["catalog"]["schema"] == "fdec-native-parallel-grammar/v1":
        import native_templates
        return native_templates.render(pack, topic=topic, language=language, seed=seed, index=index, api=sys.modules[__name__])
    if not isinstance(topic, str) or not isinstance(language, str) or topic not in TOPICS or language not in pack["catalog"]["languages"] or not integer(seed, 2**32 - 1) or not integer(index, 999):
        raise AugmentationError("invalid_synthetic_controls")
    choice = bytes.fromhex(digest([VERSION, seed, topic, index]))
    variant = choice[0] % 2
    priority = PRIORITIES[choice[1] % 4]
    security = SECURITY[choice[2] % 3]
    action = "review" if security == "phishing" else "archive" if security == "spam" else ACTIONS[choice[3] % 4]
    section = pack["catalog"]["languages"][language]
    origin = digest([pack["context_sha256"], topic, seed, index])
    case_id = "CASE-" + digest([seed, topic, index])[:16].upper()
    subject = f"{section['subjects'][topic]} — {section['case_prefix']} {case_id}"
    body = " ".join(value for value in (section["scenarios"][topic][variant], section["priority"][priority], section["action"][action], section["security"][security]) if value)
    identity = digest([VERSION, language, subject, body])
    capsule = {"schema": "fdec-synthetic-capsule/v1", "pack_id": pack["context"]["pack_id"], "purpose": pack["context"]["purpose"], "context_sha256": pack["context_sha256"], "seed": seed, "topic": topic, "index": index, "language": language, "content_id": identity}
    record = {"schema": "fdec-synthetic-email/v1", "content_id": identity, "subject": subject, "body": body, "language": language, "script": section["script"], "labels": {"category": topic, "priority": priority, "security": security, "action": action}, "provenance": {"capsule": capsule, "origin_id": origin, "family_id": digest(["fdec-template-family/v1", pack["context"]["catalog_sha256"], topic, variant]), "template_id": f"{topic}.{variant}", "translation_parent_id": None, "context": pack["context"], "authoring_origin": pack["audit"]["authoring_origin"], "declared_source_license": pack["audit"]["declared_source_license"], "training_allowed": pack["context"]["purpose"] == "commercial_training", "redistribution": "separate-review", "quality_review": "required"}}
    return record


def plan_rows(plan, pack):
    if not isinstance(plan, dict) or set(plan) != {"schema", "seed", "quotas"} or plan["schema"] != "fdec-augmentation-plan/v1" or not integer(plan["seed"], 2**32 - 1) or not isinstance(plan["quotas"], list) or not 1 <= len(plan["quotas"]) <= 1536:
        raise AugmentationError("invalid_quota_plan")
    cells, total = {}, 0
    for cell in plan["quotas"]:
        if not isinstance(cell, dict) or set(cell) != {"language", "topic", "target", "observed"} or not isinstance(cell["language"], str) or cell["language"] not in pack["catalog"]["languages"] or not isinstance(cell["topic"], str) or cell["topic"] not in TOPICS or not integer(cell["target"], 1000) or not integer(cell["observed"], 100_000_000):
            raise AugmentationError("invalid_quota_cell")
        key = (cell["language"], cell["topic"])
        if key in cells:
            raise AugmentationError("duplicate_quota_cell")
        cells[key] = max(cell["target"] - cell["observed"], 0)
        total += cells[key]
    if total > MAX_ROWS:
        raise AugmentationError("augmentation_row_limit")
    records = [render(pack, topic=topic, language=language, seed=plan["seed"], index=index) for (language, topic), count in sorted(cells.items()) for index in range(count)]
    return records, [{"language": language, "topic": topic, "generated": count} for (language, topic), count in sorted(cells.items())]


def translate_capsule(capsule, language, pack):
    keys = {"schema", "pack_id", "purpose", "context_sha256", "seed", "topic", "index", "language", "content_id"}
    if not isinstance(capsule, dict) or set(capsule) != keys or capsule["schema"] != "fdec-synthetic-capsule/v1" or not isinstance(capsule["topic"], str) or not isinstance(capsule["language"], str):
        raise AugmentationError("invalid_synthetic_capsule")
    original = render(pack, topic=capsule["topic"], language=capsule["language"], seed=capsule["seed"], index=capsule["index"])
    if capsule != original["provenance"]["capsule"]:
        raise AugmentationError("unverified_synthetic_capsule")
    if not isinstance(language, str):
        raise AugmentationError("invalid_target_language")
    translated = render(pack, topic=capsule["topic"], language=language, seed=capsule["seed"], index=capsule["index"])
    translated["provenance"]["translation_parent_id"] = original["content_id"]
    return translated


def read_capsules(path):
    try:
        source_path = reject_links(path)
        capsules = []
        with source_path.open("rb") as source:
            while line := source.readline(8193):
                if len(line) > 8192 or not line.strip() or len(capsules) >= MAX_ROWS:
                    raise AugmentationError("invalid_capsule_file")
                capsules.append(strict_json(line.decode("utf-8", errors="strict")))
        if not capsules:
            raise AugmentationError("empty_capsule_file")
        return capsules
    except AugmentationError:
        raise
    except Exception:
        raise AugmentationError("invalid_capsule_file") from None


def _write_file(path, data):
    with path.open("xb") as destination:
        destination.write(data)
        destination.flush()
        os.fsync(destination.fileno())


def _publish(records, pack, output_dir, request):
    if len({row["content_id"] for row in records}) != len(records):
        raise AugmentationError("duplicate_synthetic_output")
    native_quality = None
    if pack["catalog"]["schema"] == "fdec-native-parallel-grammar/v1":
        import native_templates
        native_quality = native_templates.quality_report(records, pack, sys.modules[__name__]) if records else {"schema": "fdec-native-quality/v1", "rows": 0, "unique_messages": 0, "structural_variants": 0, "template_families": 0, "label_counts": {}, "training_rights_established": pack["context"]["purpose"] == "commercial_training", "human_language_review": "not_asserted"}
    # Records originate exclusively in the bounded renderer above.
    usage = {"purpose": pack["context"]["purpose"], "authoring_origin": pack["audit"]["authoring_origin"], "training_allowed": pack["context"]["purpose"] == "commercial_training", "context_sha256": pack["context_sha256"]}
    streams = {"samples.jsonl": records, "capsules.jsonl": [row["provenance"]["capsule"] for row in records], "annotations.jsonl": [{"schema": "fdec-augmentation-annotation/v1", "content_id": row["content_id"], "annotations": [{"source_row": index, "labels": row["labels"]}], "data_usage": usage} for index, row in enumerate(records)]}
    output = private_output(output_dir, ROOT)
    pending, created = [], []
    parent = output.parent
    while not parent.exists():
        pending.append(parent)
        parent = parent.parent
    owned = False
    token = secrets.token_hex(16)
    try:
        for parent in reversed(pending):
            parent.mkdir(mode=0o700)
            created.append(parent)
        output.mkdir(mode=0o700)
        owned = True
        (output / ".owner").write_text(token, encoding="ascii")
        files = {}
        for name, values in streams.items():
            data = "".join(canonical(value) + "\n" for value in values).encode("utf-8")
            _write_file(output / name, data)
            files[name] = {"sha256": sha(data), "bytes": len(data), "rows": len(values)}
        receipt = {"schema": "fdec-augmentation-receipt/v1", "context": pack["context"], "rows": len(records), "files": files, "request": request, "annotation_source": {"dataset_id": "fdec/canonical-annotations", "revision": "1", "artifact": "annotations.jsonl", "sha256": files["annotations.jsonl"]["sha256"]}, "training_allowed": pack["context"]["purpose"] == "commercial_training", "redistribution": "separate-review", "quality_review": "required"}
        if native_quality is not None:
            receipt["schema"] = "fdec-native-augmentation-receipt/v1"
            receipt["quality"] = native_quality
        _write_file(output / ".receipt.part", (canonical(receipt) + "\n").encode("utf-8"))
        os.replace(output / ".receipt.part", output / "receipt.json")
        return receipt
    except Exception as error:
        if owned:
            remove_owned(output, token)
        for parent in reversed(created):
            try:
                parent.rmdir()
            except OSError:
                pass
        if isinstance(error, AugmentationError):
            raise
        raise AugmentationError("augmentation_write_failed") from None


def generate(plan, *, output_dir, pack_id, purpose, opt_in=False):
    if opt_in is not True:
        raise AugmentationError("explicit_opt_in_required")
    try:
        pack = load_pack(pack_id, purpose)
        records, counts = plan_rows(plan, pack)
        return _publish(records, pack, output_dir, {"kind": "generate", "plan_sha256": digest(plan), "quotas": counts})
    except AugmentationError:
        raise
    except Exception:
        raise AugmentationError("augmentation_failed") from None


def translate(capsules, *, language, output_dir, pack_id, purpose, opt_in=False, source_language=None):
    if opt_in is not True:
        raise AugmentationError("explicit_opt_in_required")
    try:
        pack = load_pack(pack_id, purpose)
        if not isinstance(capsules, list) or not 1 <= len(capsules) <= MAX_ROWS:
            raise AugmentationError("invalid_capsules")
        if source_language is not None and (not isinstance(source_language, str) or source_language not in pack["catalog"]["languages"]):
            raise AugmentationError("invalid_source_language")
        records = []
        # Validate even descriptors outside the requested source-language slice.
        for capsule in capsules:
            record = translate_capsule(capsule, language, pack)
            if source_language is None or capsule["language"] == source_language:
                records.append(record)
        if not records:
            raise AugmentationError("empty_translation_selection")
        records.sort(key=lambda row: row["content_id"])
        return _publish(records, pack, output_dir, {"kind": "translate", "language": language, "source_language": source_language, "capsules_sha256": digest(sorted(capsules, key=canonical))})
    except AugmentationError:
        raise
    except Exception:
        raise AugmentationError("translation_failed") from None
