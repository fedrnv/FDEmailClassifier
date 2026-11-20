"""Exact-source rights admission and read-only unlabelled Sinabis preparation."""

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import unicodedata

import training_boundary as boundary
from inspect_sinabis_metadata import IDENTITY, SIZE
from normalize_email import canonical_json, text as normalize_text

ROOT = Path(__file__).resolve().parents[2]
PROFILE = "training/config/sinabis-reviewed-source-v1.json"
MAPPING = "training/config/sinabis-mapping-v1.json"
EVIDENCE = frozenset(("training/augmentation/SINABIS-AUDIT-v1.md", "training/augmentation/SINABIS-AUDIT-v2.md", "training/augmentation/sinabis-source-observations-v1.json", MAPPING, "docs/legal/COMMERCIAL_USE_POLICY.md"))
ORIGINS = {"qwen3.6-35b-a3b-awq": "reviewed_local_qwen", "deepseek-v4-flash": "reviewed_deepseek_api", "": "verified_rule_based_calendar_only"}
DOWNSTREAM = {"commercial_training": "compatible_subject_to_conditions", "commercial_inference": "compatible_subject_to_conditions", "public_model_distribution": "compatible_subject_to_separate_artifact_audit"}
LANGUAGES = tuple("en es ja zh ar de ko hi it fr pt nl pl id tr ru tl vi th he ro nb da uk el sv cs hu fi".split())
TOPICS = tuple("work personal finance shopping travel social newsletters marketing education health legal other".split())
DIMENSIONS = ("topics", "priority", "spam", "phishing", "malware", "action")
FAMILY = "sinabis-oil-source-family/v1"
MAX_ROWS = 20_000
MAX_FEATURES = 16_384
MAX_TOTAL_FEATURES = 16_000_000
MAX_COMPARISONS = 2_000_000
FIELDS = frozenset("idx file case_id case_kind case_size position lang subject text message_id in_reply_to model model_tag calendar_method duplicate_of".split())


class SinabisError(boundary.TrainingBoundaryError):
    """Static error codes only, never message bodies or parser excerpts."""


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def missing_dimensions():
    return {name: {"state": "missing", "values": [], "supervise": False} for name in DIMENSIONS}


def mapping(root=ROOT):
    config = boundary.read_json(Path(root) / MAPPING)
    expected = {"schema": "fdec-sinabis-mapping/v1", "label_status": "independent_review_required", "automatic_supervision": False,
                "topics": list(TOPICS), "priority": ["low", "normal", "high", "urgent"], "security": {key: ["clear", "flagged"] for key in ("spam", "phishing", "malware")},
                "action": ["none", "review", "reply", "archive"], "missing_policy": "missing_with_supervision_false_for_every_dimension", "languages": list(LANGUAGES),
                "annotation_requirements": ["independent_non_openai_origin", "source_row_binding", "reviewer_and_rights_evidence", "dimension_specific_review", "conflict_and_abstention_handling", "separate_quality_evaluation"],
                "source_metadata_only": ["case_kind", "calendar_method", "lang", "model"]}
    if not isinstance(config, dict) or set(config) != set(expected) | {"notes"} or any(config.get(key) != value for key, value in expected.items()) or not isinstance(config["notes"], str):
        raise SinabisError("sinabis_mapping_contract_changed")
    return config


def attribution():
    return {"creator": "Sinabis GmbH", "year": 2026, "title": "Sinabis Oil – Synthetic Email Dataset (10k Emails)",
            "source_uri": "https://huggingface.co/datasets/sinabis-group/sinabis-10k-synthetic-emails", "license_uri": "https://creativecommons.org/licenses/by/4.0/",
            "warranty_uri": "https://creativecommons.org/licenses/by/4.0/legalcode.en#s5", "synthetic_notice": "Publisher-declared AI-generated fictional correspondence; may contain errors.",
            "modifications": ["whole-component origin quarantine", "own-message extraction", "normalization", "exact-duplicate consolidation"], "endorsement": False}


def assert_source(identity, *, purpose, policy_root=ROOT):
    """Admit only source rights; mandatory row projection and later gates remain."""
    try:
        if identity != IDENTITY or purpose not in boundary.PURPOSES:
            raise SinabisError("unapproved_sinabis_source_or_purpose")
        root = Path(policy_root)
        profile = boundary.read_json(root / PROFILE)
        expected = {"schema": "fdec-reviewed-independent-source/v2", "identity": IDENTITY, "artifact_bytes": SIZE, "license": "CC-BY-4.0",
                    "status": "allowed_reviewed_whole_cases_only", "allowed_purposes": ["commercial_training", "evaluation"],
                    "provenance_basis": "publisher_declaration_and_primary_generator_terms_review", "openai_derived": False,
                    "origin_policy": ORIGINS, "unresolved_origin_policy": "quarantine_entire_connected_component", "source_family": FAMILY,
                    "observed_languages": ["en", "de", "fr", "it"], "downstream_rights": DOWNSTREAM, "release_approved": False, "attribution": attribution(),
                    "not_admitted": [{"dataset_id": "sinabis-group/sinabis-10m-synthetic-emails", "revision": "62385fbfe6aeb838305183215b55456ff5345cd5", "reason": "complete_artifact_and_row_origin_audit_not_performed"}]}
        if not isinstance(profile, dict) or set(profile) != set(expected) | {"evidence"} or any(profile.get(key) != value for key, value in expected.items()) or profile["openai_derived"] is not False or profile["release_approved"] is not False:
            raise SinabisError("sinabis_reviewed_profile_changed")
        bindings = profile["evidence"]
        if not isinstance(bindings, list) or len(bindings) != len(EVIDENCE) or any(not isinstance(item, dict) or set(item) != {"path", "sha256"} or not isinstance(item["path"], str) for item in bindings) or {item["path"] for item in bindings} != EVIDENCE:
            raise SinabisError("sinabis_evidence_incomplete")
        for item in bindings:
            path = boundary.ingestion.reject_links(root / item["path"]).resolve()
            if not path.is_relative_to(root.resolve()) or boundary.text_hash(path) != item["sha256"]:
                raise SinabisError("sinabis_evidence_changed")
        observations = boundary.read_json(root / "training/augmentation/sinabis-source-observations-v1.json")
        source, = [row for row in observations["datasets"] if row["dataset_id"] == IDENTITY["dataset_id"]]
        artifact, = [row for row in source["files"] if row["rfilename"] == IDENTITY["artifact"]]
        if source["revision"] != IDENTITY["revision"] or source["declared_license"] != "cc-by-4.0" or artifact["lfs"]["sha256"] != IDENTITY["sha256"] or artifact["size"] != SIZE:
            raise SinabisError("sinabis_observation_identity_changed")
        mapping(root)
        return {"schema": "fdec-independent-source-admission/v2", "descriptor": dict(IDENTITY, size=SIZE, license="CC-BY-4.0", purpose=purpose, target="specialized-email-classifier", row_scope="reviewed-whole-cases-only"),
                "origin_policy_sha256": boundary.text_hash(root / PROFILE), "authoring_provider": "sinabis-publisher-declared-reviewed-non-openai", "scope": "reviewed-row-source-rights-only",
                "requires_origin_projection": True, "requires_split_and_consent": True, "requires_independent_labels": True, "release_approved": False, "downstream_rights": deepcopy(DOWNSTREAM), "attribution": attribution()}
    except boundary.TrainingBoundaryError:
        raise
    except Exception:
        raise SinabisError("sinabis_source_admission_failed") from None


def source_snapshot(path):
    try:
        path = boundary.ingestion.reject_links(path)
        with path.open("rb") as stream:
            data = stream.read(SIZE + 1)
        if len(data) != SIZE or hashlib.sha256(data).hexdigest() != IDENTITY["sha256"]:
            raise SinabisError("sinabis_source_checksum_mismatch")
        return data
    except SinabisError:
        raise
    except Exception:
        raise SinabisError("invalid_sinabis_source") from None


def decode(data):
    try:
        import pyarrow
        import pyarrow.parquet as parquet
        if pyarrow.__version__ != "26.0.1":
            raise SinabisError("unapproved_sinabis_decoder")
        table = parquet.read_table(io.BytesIO(data), columns=sorted(FIELDS))
        if not 1 <= len(table) <= MAX_ROWS:
            raise SinabisError("sinabis_row_limit")
        return table.to_pylist()
    except SinabisError:
        raise
    except Exception:
        raise SinabisError("invalid_sinabis_parquet") from None


def features(subject, body):
    value = "".join(char for char in unicodedata.normalize("NFKC", subject + "\n" + body).casefold() if char.isalnum())
    if not value:
        raise SinabisError("sinabis_empty_feature_text")
    grams = {value[index:index + 5] for index in range(max(1, len(value) - 4))}
    if len(grams) > MAX_FEATURES:
        raise SinabisError("sinabis_feature_limit")
    return frozenset(hashlib.sha256(gram.encode("utf-8")).digest() for gram in grams)


def near_pairs(sets):
    """Exact Jaccard >=0.8 with pair-size prefixes and early impossibility bounds."""
    frequency = Counter(value for values in sets for value in values)
    rank = {value: index for index, value in enumerate(sorted(frequency, key=lambda value: (frequency[value], value)))}
    ordered_sets = [sorted(rank[value] for value in values) for values in sets]
    postings = defaultdict(list)
    comparisons = 0
    for index, ordered in enumerate(ordered_sets):
        size = len(ordered)
        prefix = ordered[:size - (4 * size + 4) // 5 + 1]
        candidates = set()
        for position, value in enumerate(prefix):
            for other, other_position in postings[value]:
                previous_size = len(ordered_sets[other])
                if min(size, previous_size) * 5 < max(size, previous_size) * 4:
                    continue
                required = (4 * (size + previous_size) + 8) // 9
                # An overlap >=required must share a token in these two prefixes
                # under one global order. Larger universal prefixes are only an
                # index; the pair-specific bounds avoid unnecessary candidates.
                if position <= size - required and other_position <= previous_size - required:
                    candidates.add(other)
        for other in sorted(candidates):
            comparisons += 1
            if comparisons > MAX_COMPARISONS:
                raise SinabisError("sinabis_comparison_limit")
            previous = ordered_sets[other]
            required = (4 * (size + len(previous)) + 8) // 9
            left = right = overlap = 0
            while left < size and right < len(previous):
                if overlap + min(size - left, len(previous) - right) < required:
                    break
                if ordered[left] == previous[right]:
                    overlap += 1
                    if overlap >= required:
                        yield other, index
                        break
                    left += 1
                    right += 1
                elif ordered[left] < previous[right]:
                    left += 1
                else:
                    right += 1
        for position, value in enumerate(prefix):
            postings[value].append((index, position))


def project_rows(rows, *, allowed_languages=LANGUAGES):
    """Untrusted review preparation, also testable on software-only fixtures.

    This pure helper cannot assert source rights or produce a training receipt.
    Only prepare() authenticates pinned independent bytes and source evidence.
    """
    try:
        if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS or not set(allowed_languages) <= set(LANGUAGES):
            raise SinabisError("invalid_sinabis_rows_or_languages")
        parent = list(range(len(rows)))
        def find(index):
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index
        def union(left, right):
            parent[find(right)] = find(left)
        cases = defaultdict(list)
        messages, files, exact = {}, {}, {}
        bad = defaultdict(set)
        normalized, shingle_sets = [], []
        total_features = 0
        seen_idx = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or set(row) != FIELDS or type(row["idx"]) is not int or row["idx"] < 0 or row["idx"] in seen_idx or not isinstance(row["case_id"], str) or not re.fullmatch("[a-f0-9]{64}", row["case_id"]):
                raise SinabisError("invalid_sinabis_record_identity")
            seen_idx.add(row["idx"])
            for key in ("case_size", "position"):
                if type(row[key]) is not int or not 1 <= row[key] <= 1000:
                    raise SinabisError("invalid_sinabis_case_position")
            for key in FIELDS - {"idx", "case_size", "position", "subject", "text"}:
                if not isinstance(row[key], str) or len(row[key]) > 4096 or any(ord(c) < 32 for c in row[key]):
                    raise SinabisError("invalid_sinabis_metadata")
            subject, body = normalize_text(row["subject"], 4096), normalize_text(row["text"], 200_000)
            if not body:
                raise SinabisError("sinabis_empty_own_message")
            content = digest([unicodedata.normalize("NFKC", subject).casefold(), unicodedata.normalize("NFKC", body).casefold()])
            normalized.append((subject, body, content))
            values = features(subject, body)
            total_features += len(values)
            if total_features > MAX_TOTAL_FEATURES:
                raise SinabisError("sinabis_total_feature_limit")
            shingle_sets.append(values)
            if row["case_id"] in cases:
                union(index, cases[row["case_id"]][0])
            cases[row["case_id"]].append(index)
            for table, key in ((messages, row["message_id"]), (files, row["file"]), (exact, content)):
                if not key:
                    bad[index].add("missing_source_link_identity")
                elif key in table:
                    union(index, table[key])
                else:
                    table[key] = index
            if row["lang"] not in allowed_languages or row["case_kind"] not in ("thread", "single", "meeting"):
                bad[index].add("unreviewed_language_or_case_kind")
            origin = row["model"]
            reviewed = (origin == "qwen3.6-35b-a3b-awq" and row["model_tag"] in {"V1", "V2", "V3", "V4", "V5", "V6"}
                        or origin == "deepseek-v4-flash" and row["model_tag"] == ""
                        or origin == "" and row["model_tag"] == "" and row["case_kind"] == "meeting" and row["calendar_method"] in {"REQUEST", "REPLY", "CANCEL"})
            if not reviewed:
                bad[index].add("unresolved_generation_origin")
        for indexes in cases.values():
            expected = rows[indexes[0]]["case_size"]
            if len(indexes) != expected or any(rows[index]["case_size"] != expected for index in indexes) or sorted(rows[index]["position"] for index in indexes) != list(range(1, expected + 1)):
                bad[indexes[0]].add("incomplete_or_inconsistent_case")
        for index, row in enumerate(rows):
            for key, table in (("in_reply_to", messages), ("duplicate_of", files)):
                if row[key]:
                    if row[key] not in table:
                        bad[index].add("unresolved_source_link")
                    else:
                        union(index, table[row[key]])
        pairs = list(near_pairs(shingle_sets))
        for left, right in pairs:
            union(left, right)
        excluded = {find(index) for index in bad}
        reasons = Counter(reason for values in bad.values() for reason in values)
        groups = defaultdict(list)
        for index in range(len(rows)):
            groups[find(index)].append(index)
        components = {root: digest(sorted(rows[index]["case_id"] + ":" + str(rows[index]["idx"]) for index in indexes)) for root, indexes in groups.items()}
        by_content = defaultdict(list)
        for index, (_, _, content) in enumerate(normalized):
            if find(index) not in excluded:
                by_content[content].append(index)
        records = []
        for content, indexes in sorted(by_content.items()):
            first = min(indexes, key=lambda index: rows[index]["idx"])
            row = rows[first]
            records.append({"schema": "fdec-unverified-source-projection/v1", "record_id": digest(["fdec-unverified-projection/v1", content, sorted(rows[index]["idx"] for index in indexes)]),
                            "source": None, "source_rows": sorted(indexes), "upstream_indexes": sorted(rows[index]["idx"] for index in indexes),
                            "case_ids": sorted({rows[index]["case_id"] for index in indexes}), "component_id": components[find(first)], "source_family": FAMILY,
                            "language": row["lang"], "subject": normalized[first][0], "body": normalized[first][1], "content_sha256": content,
                            "dimensions": missing_dimensions(),
                            "labels_origin": "not_provided_by_source", "training_ready": False})
        retained = sum(len(indexes) for indexes in by_content.values())
        return {"schema": "fdec-sinabis-review-projection/v1", "records": records,
                "summary": {"input_rows": len(rows), "input_cases": len(cases), "retained_source_rows": retained, "unique_records": len(records),
                            "quarantined_rows": len(rows) - retained, "quarantined_cases": len({row["case_id"] for index, row in enumerate(rows) if find(index) in excluded}),
                            "exact_duplicate_rows": len(rows) - len(exact), "retained_exact_duplicate_rows": retained - len(records), "near_duplicate_pairs": len(pairs),
                            "reason_rows": dict(sorted(reasons.items())), "languages": dict(sorted(Counter(record["language"] for record in records).items())),
                            "supervised_records": 0, "independent_source_cohorts": 1, "records_sha256": digest(records), "feature_algorithm": "unicode-alnum-5gram-jaccard80/v1", "unicode_version": unicodedata.unidata_version}}
    except SinabisError:
        raise
    except Exception:
        raise SinabisError("invalid_sinabis_projection") from None


def check_roles(projection, assignments):
    """Reject cross-role threads, duplicate components and source-family peers."""
    try:
        records = projection["records"]
        if projection.get("schema") != "fdec-sinabis-review-projection/v1" or not records or projection["summary"]["records_sha256"] != digest(records):
            raise SinabisError("invalid_sinabis_projection_proof")
        for row in records:
            unverified = row["source"] is None and row["schema"] == "fdec-unverified-source-projection/v1"
            verified_shape = row["source"] == IDENTITY and row["schema"] == "fdec-unlabelled-source-email/v1"
            if not (unverified or verified_shape) or row["source_family"] != FAMILY or row["training_ready"] is not False or row["dimensions"] != missing_dimensions() or row["labels_origin"] != "not_provided_by_source":
                raise SinabisError("invalid_sinabis_projection_proof")
        if not isinstance(assignments, dict) or set(assignments) != {row["record_id"] for row in records} or any(role not in {"train", "validation", "test"} for role in assignments.values()):
            raise SinabisError("invalid_sinabis_role_assignment")
        seen = {}
        for kind in ("thread", "component", "family"):
            for row in records:
                keys = row["case_ids"] if kind == "thread" else [row["component_id"] if kind == "component" else row["source_family"]]
                for key in keys:
                    pair = (kind, key)
                    role = assignments[row["record_id"]]
                    if pair in seen and seen[pair] != role:
                        raise SinabisError("sinabis_" + kind + "_leakage")
                    seen[pair] = role
        return {"scope": "preparation_role_consistency_only", "requires_current_split_and_consent_gate": True, "training_ready": False}
    except SinabisError:
        raise
    except Exception:
        raise SinabisError("invalid_sinabis_role_proof") from None


def implementation_hash():
    paths = ("training/augmentation/sinabis_source.py", "training/augmentation/training_boundary.py", "training/augmentation/inspect_sinabis_metadata.py", "training/scripts/normalize_email.py")
    return hashlib.sha256(b"".join((ROOT / path).read_bytes().replace(b"\r\n", b"\n") for path in paths)).hexdigest()


def prepare(path, *, purpose="commercial_training", opt_in=False, policy_root=ROOT, include_records=False):
    if opt_in is not True:
        raise SinabisError("sinabis_explicit_opt_in_required")
    admitted = assert_source(IDENTITY, purpose=purpose, policy_root=policy_root)
    data = source_snapshot(path)
    projected = project_rows(decode(data), allowed_languages=("en", "de", "fr", "it"))
    # Pure software projections never assert a real corpus identity. Bind that
    # identity only here, after exact source-rights and immutable-byte checks.
    for record in projected["records"]:
        record["schema"] = "fdec-unlabelled-source-email/v1"
        record["source"] = deepcopy(IDENTITY)
        record["record_id"] = digest([IDENTITY, record["record_id"]])
    projected["summary"]["records_sha256"] = digest(projected["records"])
    result = {"schema": "fdec-sinabis-preparation/v1", "source_admission": admitted, "implementation_sha256": implementation_hash(),
              "summary": projected["summary"], "training_ready": False,
              "remaining_gates": ["independent_permitted_annotation", "quality_evaluation", "current_source_consent_and_split_integration", "training_task_admission"]}
    if include_records:
        result["projection"] = projected
    return result


def main(argv=None):
    import argparse
    class PrivateParser(argparse.ArgumentParser):
        def error(self, message):
            raise SinabisError("invalid_sinabis_arguments")
    parser = PrivateParser(description="Read-only Sinabis preparation report; no training or email output")
    parser.add_argument("--source", required=True)
    parser.add_argument("--opt-in", action="store_true")
    try:
        args = parser.parse_args(argv)
        report = prepare(args.source, opt_in=args.opt_in)
    except SinabisError as error:
        safe_codes = {"sinabis_comparison_limit", "sinabis_feature_limit", "sinabis_total_feature_limit", "sinabis_row_limit", "sinabis_source_checksum_mismatch", "invalid_sinabis_projection", "invalid_sinabis_parquet", "invalid_sinabis_arguments"}
        print(str(error) if str(error) in safe_codes else "sinabis_preparation_failed", file=sys.stderr)
        return 1
    except Exception:
        print("sinabis_preparation_failed", file=sys.stderr)
        return 1
    # ASCII JSON escapes retain exact attribution through Windows pipe encodings.
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
