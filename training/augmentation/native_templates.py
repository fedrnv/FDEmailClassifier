"""Original native grammar software candidate; source rights remain explicit."""

from collections import Counter
import re
from string import Formatter
import sys
import unicodedata

SCHEMA = "fdec-native-parallel-grammar/v1"
VERSION = "fdec-native-renderer/v1"
ORIGIN = "codex-assisted-original-native-grammar"
FIELDS = {"topic", "person", "sender", "email", "reference", "project", "item", "amount", "date", "count", "account"}


def validate(catalog, api):
    if set(catalog) != {"schema", "authorship", "license", "languages"} or catalog["schema"] != SCHEMA or catalog["authorship"] != ORIGIN or catalog["license"] != "Apache-2.0":
        raise api.AugmentationError("invalid_native_catalog")
    languages = catalog["languages"]
    if not isinstance(languages, dict) or not 1 <= len(languages) <= 128:
        raise api.AugmentationError("invalid_native_languages")
    for language, section in languages.items():
        if not isinstance(language, str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Z][a-z]{3})?", language) or not isinstance(section, dict) or set(section) != {"script", "subject_forms", "topic_names", "facts", "greetings", "notes", "priority", "action", "security", "closings"}:
            raise api.AugmentationError("invalid_native_language")
        if not isinstance(section["script"], str) or not re.fullmatch("[A-Z][a-z]{3}", section["script"]):
            raise api.AugmentationError("invalid_native_script")
        strings = []
        for key in ("subject_forms", "greetings", "notes", "closings"):
            values = section[key]
            if not isinstance(values, list) or not 2 <= len(values) <= 16 or any(not isinstance(value, str) for value in values) or len(set(values)) != len(values):
                raise api.AugmentationError("invalid_native_alternatives")
            strings.extend((value, False) for value in values)
        for key, names in (("topic_names", api.TOPICS), ("facts", api.TOPICS), ("priority", api.PRIORITIES), ("action", api.ACTIONS), ("security", api.SECURITY)):
            values = section[key]
            if not isinstance(values, dict) or set(values) != set(names):
                raise api.AugmentationError("incomplete_native_labels")
            for name, value in values.items():
                if key == "facts":
                    if not isinstance(value, list) or not 2 <= len(value) <= 16 or any(not isinstance(item, str) for item in value) or len(set(value)) != len(value):
                        raise api.AugmentationError("invalid_native_facts")
                    strings.extend((item, False) for item in value)
                else:
                    strings.append((value, key == "security" and name == "normal"))
        for value, empty in strings:
            api.phrase(value, empty=empty)
            try:
                for _, field, spec, conversion in Formatter().parse(value):
                    if field is not None and (field not in FIELDS or spec or conversion):
                        raise ValueError("unsupported placeholder")
            except ValueError:
                raise api.AugmentationError("unsafe_native_placeholder") from None


def render(pack, *, topic, language, seed, index, api):
    if not isinstance(topic, str) or not isinstance(language, str) or topic not in api.TOPICS or language not in pack["catalog"]["languages"] or not api.integer(seed, 2**32 - 1) or not api.integer(index, 999):
        raise api.AugmentationError("invalid_synthetic_controls")
    section = pack["catalog"]["languages"][language]
    choice = bytes.fromhex(api.digest([VERSION, seed, topic, index]))
    cycle = (index + int(api.digest([seed, topic])[:8], 16)) % 48
    security = api.SECURITY[cycle % 3]
    priority = api.PRIORITIES[(cycle // 3) % 4]
    action = "review" if security == "phishing" else "archive" if security == "spam" else api.ACTIONS[cycle // 12]
    variant = choice[0] % len(section["facts"][topic])
    reference = "FDEC-CASE-" + choice[4:16].hex().upper()
    person = "FDEC-PERSON-" + choice[8:20].hex().upper()
    email = "person-" + choice[8:20].hex() + "@mail.invalid"
    values = dict(topic=section["topic_names"][topic], person=person, sender="FDEC-SENDER-" + choice[10:22].hex().upper(), email=email, reference=reference, project="FDEC-PROJECT-" + choice[12:24].hex().upper(), item="FDEC-ITEM-" + choice[14:26].hex().upper(), account="FDEC-ACCOUNT-" + choice[16:28].hex().upper(), amount=str(100 + int.from_bytes(choice[22:25], "big") % 90_000), count=str(1 + choice[25] % 50), date=f"2000-{1 + choice[26] % 12:02d}-{1 + choice[27] % 28:02d}")
    greeting = section["greetings"][choice[1] % len(section["greetings"])].format_map(values)
    fact = section["facts"][topic][variant].format_map(values)
    note = section["notes"][choice[2] % len(section["notes"])].format_map(values)
    priority_text = section["priority"][priority].format_map(values)
    action_text = section["action"][action].format_map(values)
    security_text = section["security"][security].format_map(values)
    closing = section["closings"][choice[3] % len(section["closings"])].format_map(values)
    layouts = ((greeting, fact, priority_text, action_text, security_text, closing), (greeting, note, fact, security_text, priority_text, action_text, closing), (greeting, priority_text, fact, action_text, security_text, closing), (greeting, fact, note, priority_text, security_text, action_text, closing))
    body = "\n".join(value for value in layouts[choice[28] % len(layouts)] if value)
    subject = section["subject_forms"][choice[29] % len(section["subject_forms"])].format_map(values)
    identity = api.digest([VERSION, language, subject, body])
    capsule = dict(schema="fdec-synthetic-capsule/v1", pack_id=pack["context"]["pack_id"], purpose=pack["context"]["purpose"], context_sha256=pack["context_sha256"], seed=seed, topic=topic, index=index, language=language, content_id=identity)
    provenance = dict(capsule=capsule, origin_id=api.digest([pack["context_sha256"], topic, seed, index]), family_id=api.digest(["fdec-native-template-family/v1", pack["context"]["catalog_sha256"], topic, variant]), template_id=f"native.{topic}.{variant}", translation_parent_id=None, context=pack["context"], authoring_origin=ORIGIN, declared_source_license=pack["audit"]["declared_source_license"], training_allowed=pack["context"]["purpose"] == "commercial_training", redistribution="separate-review", quality_review="required", variation=dict(fact=variant, greeting=choice[1] % len(section["greetings"]), note=choice[2] % len(section["notes"]), closing=choice[3] % len(section["closings"]), layout=choice[28] % len(layouts), subject=choice[29] % len(section["subject_forms"])))
    return dict(schema="fdec-native-synthetic-email/v1", content_id=identity, subject=subject, body=body, language=language, script=section["script"], labels=dict(category=topic, priority=priority, security=security, action=action), synthetic_identity=dict(namespace="fdec.invalid/v1", person_label=person, email=email, account_reference=values["account"]), provenance=provenance)


def quality_report(records, pack, api):
    """Software quality evidence, not linguistic sign-off or training permission."""
    if not isinstance(records, list) or not 1 <= len(records) <= api.MAX_ROWS:
        raise api.AugmentationError("invalid_native_quality_input")
    ids, text_hashes, layouts, families, labels = set(), set(), set(), set(), Counter()
    for row in records:
        try:
            capsule = row["provenance"]["capsule"]
            expected = render(pack, topic=capsule["topic"], language=capsule["language"], seed=capsule["seed"], index=capsule["index"], api=api)
            parent = row["provenance"]["translation_parent_id"]
            if parent is not None:
                parents = {render(pack, topic=capsule["topic"], language=language, seed=capsule["seed"], index=capsule["index"], api=api)["content_id"] for language in pack["catalog"]["languages"]}
                if parent not in parents:
                    raise api.AugmentationError("unverified_native_translation_parent")
                expected["provenance"]["translation_parent_id"] = parent
            if row != expected:
                raise api.AugmentationError("native_annotation_or_provenance_changed")
            normalized = " ".join(unicodedata.normalize("NFKC", row["subject"] + "\n" + row["body"]).casefold().split())
            text_hash = api.sha(normalized.encode("utf-8"))
            if row["content_id"] in ids or text_hash in text_hashes:
                raise api.AugmentationError("duplicate_native_message")
            ids.add(row["content_id"])
            text_hashes.add(text_hash)
            families.add(row["provenance"]["family_id"])
            layouts.add(api.canonical(row["provenance"]["variation"]))
            for field, value in row["labels"].items():
                labels[field + ":" + value] += 1
        except api.AugmentationError:
            raise
        except Exception:
            raise api.AugmentationError("invalid_native_quality_record") from None
    return dict(schema="fdec-native-quality/v1", rows=len(records), unique_messages=len(ids), structural_variants=len(layouts), template_families=len(families), label_counts=dict(sorted(labels.items())), training_rights_established=pack["context"]["purpose"] == "commercial_training", human_language_review="not_asserted")


def validate_partition(records, assignments, pack, api):
    """Retain the accepted source-held-out policy; no one-pack split bypass."""
    quality_report(records, pack, api)
    sys.path.insert(0, str(api.ROOT / "training/splits"))
    import split_data
    ids = {row["content_id"] for row in records}
    if not isinstance(assignments, dict) or set(assignments) != ids or any(role not in split_data.ROLES for role in assignments.values()):
        raise api.AugmentationError("invalid_native_partition")
    graph = [dict(record_id=row["content_id"], content_sha256=api.digest([row["subject"], row["body"]]), source=dict(dataset_id=pack["context"]["pack_id"]), thread_id=None, family_ids=[row["provenance"]["family_id"], row["provenance"]["origin_id"]], shingles=split_data.features(row["subject"], row["body"])) for row in records]
    for group in split_data.components(graph):
        if len({assignments[row["record_id"]] for row in group}) > 1:
            raise api.AugmentationError("native_train_test_leakage")
    return dict(schema="fdec-native-partition-check/v1", rows=len(records), source_groups=1, cross_split_components=0)
