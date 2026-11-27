"""Private, consent-bound source/thread/duplicate grouping for training splits."""

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
sys.path.append(str(ROOT / "training/augmentation"))
from ingest_dataset import inclusion, private_output, reject_links, remove_owned, strict_json
from normalize_email import VERSION as NORMALIZATION_VERSION, canonical_json

VERSION = "fdec-grouped-splits/v1"
FEATURE_POLICY = {"algorithm": "unicode-alnum-5gram-jaccard80/v1", "unicode_version": unicodedata.unidata_version}
ROLES = ("train", "validation", "test")
GEMMA_ID = "Kamisori-daijin/email-datasets-20k"
SINABIS_SPLIT_IMPLEMENTATION_SHA256 = "5cdfe83de56e6a6939bc79044c3fed8a591c0d98ddc9a958dc326b9c4a992070"
SINABIS_ID = "sinabis-group/sinabis-10k-synthetic-emails"
GEMMA_SPLIT_IMPLEMENTATION_SHA256 = "5df67b7387491d31efe4ba15c4fcc2f47223c51c73ddc75d119d9fdbd0c541f6"
LEGACY_IMPLEMENTATION_SHA256 = "502c5f219c3529614eb6f805675c6028010031fec5029636b84ec5c512945686"
MAX_ROWS = 100_000
MAX_FEATURES = 4096
MAX_TOTAL_FEATURES = 2_000_000
MAX_COMPARISONS = 2_000_000


class SplitError(ValueError):
    """Static codes only. Never log private inventory/consent contents."""


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def implementation_hash():
    paths = ("training/splits/split_data.py", "training/splits/split_cli.py", "training/scripts/normalize_email.py", "training/scripts/ingest_dataset.py", "training/datasets/get-inclusion.ps1", "training/datasets/assert-allowlist.ps1", "scripts/validate_tasks/identity.ps1")
    paths += ("training/augmentation/sinabis_source.py", "training/augmentation/training_boundary.py",
              "training/augmentation/inspect_sinabis_metadata.py", "training/augmentation/gemma_source.py",
              "training/splits/disk_inventory.py")
    return hashlib.sha256(b"".join((ROOT / path).read_bytes().replace(b"\r\n", b"\n") for path in paths)).hexdigest()


def is_hash(value):
    return isinstance(value, str) and re.fullmatch("[a-f0-9]{64}", value) is not None


def integer(value, maximum):
    return type(value) is int and 0 <= value <= maximum


def read_bytes(path, limit=250_000_000):
    try:
        path = reject_links(path)
        with path.open("rb") as source:
            data = source.read(limit + 1)
        if len(data) > limit:
            raise SplitError("input_size_limit")
        return data
    except SplitError:
        raise
    except Exception:
        raise SplitError("invalid_json_input") from None


def read_json(path, limit=250_000_000):
    try:
        return strict_json(read_bytes(path, limit).decode("utf-8-sig", errors="strict"))
    except SplitError:
        raise
    except Exception:
        raise SplitError("invalid_json_input") from None


def read_inventory(path):
    path = reject_links(path)
    if path.is_dir():
        from disk_inventory import open_inventory

        return open_inventory(path)
    return read_json(path)


def inventory_rows(inventory):
    from disk_inventory import DiskInventory

    if isinstance(inventory, DiskInventory):
        return inventory.rows()
    return inventory["records"]


def inventory_digest(inventory):
    from disk_inventory import DiskInventory

    if isinstance(inventory, DiskInventory):
        return digest(inventory.manifest)
    return digest(inventory)


def features(subject, body):
    """Versioned character shingles; no raw text is returned or persisted."""
    if not isinstance(subject, str) or not isinstance(body, str) or len(subject) > 4096 or not 1 <= len(body) <= 200_000:
        raise SplitError("invalid_feature_text")
    try:
        text = unicodedata.normalize("NFKC", subject + "\n" + body).casefold()
        text.encode("utf-8", errors="strict")
    except UnicodeError:
        raise SplitError("invalid_feature_text") from None
    text = "".join(char for char in text if char.isalnum())
    if not text:
        raise SplitError("empty_feature_text")
    grams = {text[index:index + 5] for index in range(max(1, len(text) - 4))}
    if len(grams) > MAX_FEATURES:
        raise SplitError("feature_budget_exceeded")
    return sorted(hashlib.sha256(gram.encode("utf-8")).hexdigest() for gram in grams)


def prepare_record(normalized, receipt, *, consent_id, thread_id=None, family_ids=()):
    """Trusted preparer helper; caller first verifies the actual ingestion run."""
    try:
        source = {name: receipt["input"][name] for name in ("dataset_id", "revision", "artifact", "sha256")}
        if source["dataset_id"] == SINABIS_ID:
            from sinabis_source import FAMILY, RUN_SCHEMA

            if normalized["schema"] != "fdec-sinabis-reviewed-row/v1" or receipt["schema"] != RUN_SCHEMA:
                raise SplitError("unsupported_ingestion_provenance")
            expected_family = [digest(FAMILY)]
            if normalized["family_ids"] != expected_family:
                raise SplitError("changed_sinabis_lineage")
            if thread_id is not None and thread_id != normalized["thread_id"]:
                raise SplitError("changed_sinabis_lineage")
            if family_ids and sorted(family_ids) != expected_family:
                raise SplitError("changed_sinabis_lineage")
            thread_id, family_ids = normalized["thread_id"], expected_family
        else:
            expected_schema = "fdec-gemma-reviewed-run/v1" if source["dataset_id"] == GEMMA_ID else "fdec-ingestion-receipt/v1"
            if normalized["schema"] != "fdec-normalized-email/v1" or receipt["schema"] != expected_schema or receipt["normalization_version"] != NORMALIZATION_VERSION:
                raise SplitError("unsupported_ingestion_provenance")
        expected = hashlib.sha256((NORMALIZATION_VERSION + "\0" + canonical_json([normalized["subject"], normalized["body"]])).encode("utf-8")).hexdigest()
        if normalized["content_id"] != expected or normalized["source"] != source:
            raise SplitError("changed_normalized_record")
        source_rows = sorted(item["source_row"] for item in normalized["annotations"])
        provenance = {"ingestion_receipt_sha256": digest(receipt), "normalized_records_sha256": receipt["records_sha256"], "source_rows": source_rows}
        record = {"content_sha256": expected, "source": source, "provenance": provenance, "thread_id": thread_id, "family_ids": sorted(family_ids), "shingles": features(normalized["subject"], normalized["body"]), "consent_id": consent_id}
        record["record_id"] = digest([source, expected, source_rows])
        validate_record(record)
        return record
    except SplitError:
        raise
    except Exception:
        raise SplitError("invalid_ingestion_record") from None


def validate_record(record, *, metadata_only=False):
    required = {"record_id", "content_sha256", "source", "provenance", "thread_id", "family_ids", "shingles", "consent_id"}
    if metadata_only:
        required.remove("shingles")
    if not isinstance(record, dict) or set(record) != required or any(not is_hash(record[name]) for name in ("record_id", "content_sha256", "consent_id")):
        raise SplitError("invalid_inventory_record")
    source = record["source"]
    if not isinstance(source, dict) or set(source) != {"dataset_id", "revision", "artifact", "sha256"} or not isinstance(source["dataset_id"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["dataset_id"]) or not isinstance(source["revision"], str) or not re.fullmatch("[a-f0-9]{40}", source["revision"]) or not is_hash(source["sha256"]) or not isinstance(source["artifact"], str) or len(source["artifact"]) > 256:
        raise SplitError("invalid_record_source")
    provenance = record["provenance"]
    if not isinstance(provenance, dict) or set(provenance) != {"ingestion_receipt_sha256", "normalized_records_sha256", "source_rows"} or not is_hash(provenance["ingestion_receipt_sha256"]) or not is_hash(provenance["normalized_records_sha256"]):
        raise SplitError("invalid_record_provenance")
    source_rows = provenance["source_rows"]
    if not isinstance(source_rows, list) or not 1 <= len(source_rows) <= MAX_ROWS or any(not integer(row, MAX_ROWS - 1) for row in source_rows) or source_rows != sorted(set(source_rows)):
        raise SplitError("invalid_source_rows")
    if record["record_id"] != digest([source, record["content_sha256"], source_rows]):
        raise SplitError("changed_record_identity")
    if record["thread_id"] is not None and not is_hash(record["thread_id"]):
        raise SplitError("invalid_thread_identity")
    if source["dataset_id"] == SINABIS_ID:
        from sinabis_source import FAMILY

        if record["thread_id"] is None or record["family_ids"] != [digest(FAMILY)]:
            raise SplitError("changed_sinabis_lineage")
    lists = [("family_ids", 0, 16)]
    if not metadata_only:
        lists.append(("shingles", 1, MAX_FEATURES))
    for field, minimum, maximum in lists:
        values = record[field]
        if not isinstance(values, list) or not minimum <= len(values) <= maximum or any(not is_hash(value) for value in values) or values != sorted(set(values)):
            raise SplitError("invalid_record_fingerprints")


def validate_inventory(inventory):
    from disk_inventory import DiskInventory

    if isinstance(inventory, DiskInventory):
        inventory.verify_fingerprint_file()
        return
    if not isinstance(inventory, dict) or set(inventory) != {"schema", "normalization_version", "feature_policy", "records"} or inventory["schema"] != "fdec-split-inventory/v1" or inventory["normalization_version"] != NORMALIZATION_VERSION or inventory["feature_policy"] != FEATURE_POLICY or not isinstance(inventory["records"], list) or not 1 <= len(inventory["records"]) <= MAX_ROWS:
        raise SplitError("invalid_inventory")
    identifiers, total = set(), 0
    for record in inventory["records"]:
        validate_record(record)
        if record["record_id"] in identifiers:
            raise SplitError("duplicate_inventory_record")
        identifiers.add(record["record_id"])
        total += len(record["shingles"])
    if total > MAX_TOTAL_FEATURES:
        raise SplitError("inventory_feature_budget_exceeded")


def utc(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise SplitError("invalid_consent_time")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise SplitError("invalid_consent_time") from None


def authority_key():
    raw = os.environ.get("FDEC_CONSENT_KEY", "")
    if not re.fullmatch("[a-fA-F0-9]{64}", raw):
        raise SplitError("consent_authority_key_missing")
    return bytes.fromhex(raw)


def envelope(payload, key):
    if not isinstance(key, bytes) or len(key) != 32:
        raise SplitError("invalid_consent_authority")
    return {"schema": "fdec-signed-consent/v1", "payload": payload, "hmac_sha256": hmac.new(key, canonical_json(payload).encode("utf-8"), hashlib.sha256).hexdigest()}


def consent(inventory, signed, key, now):
    if not isinstance(signed, dict) or set(signed) != {"schema", "payload", "hmac_sha256"} or signed["schema"] != "fdec-signed-consent/v1" or not is_hash(signed["hmac_sha256"]):
        raise SplitError("invalid_consent_envelope")
    expected = envelope(signed["payload"], key)
    if not hmac.compare_digest(signed["hmac_sha256"], expected["hmac_sha256"]):
        raise SplitError("untrusted_consent_signature")
    payload = signed["payload"]
    if not isinstance(payload, dict) or set(payload) != {"schema", "revision", "previous_snapshot_sha256", "inventory_sha256", "issued_at", "valid_until", "grants"} or payload["schema"] != "fdec-consent-ledger/v1" or type(payload["revision"]) is not int or payload["revision"] <= 0 or payload["inventory_sha256"] != inventory_digest(inventory) or not isinstance(payload["grants"], list) or len(payload["grants"]) > MAX_ROWS:
        raise SplitError("invalid_consent_ledger")
    if payload["previous_snapshot_sha256"] is not None and not is_hash(payload["previous_snapshot_sha256"]):
        raise SplitError("invalid_previous_consent_snapshot")
    start, end = utc(payload["issued_at"]), utc(payload["valid_until"])
    if now.tzinfo is None or not start <= now < end:
        raise SplitError("consent_ledger_not_current")
    records = {row["record_id"]: row for row in inventory_rows(inventory)}
    grants, allowed = {}, set()
    for grant in payload["grants"]:
        if not isinstance(grant, dict) or set(grant) != {"record_id", "consent_id", "evidence_sha256", "status", "purposes", "expires_at"} or not is_hash(grant["record_id"]) or grant["record_id"] not in records or grant["record_id"] in grants or grant["consent_id"] != records[grant["record_id"]]["consent_id"] or not is_hash(grant["evidence_sha256"]) or grant["status"] not in ("granted", "revoked"):
            raise SplitError("invalid_consent_grant")
        purposes = grant["purposes"]
        if not isinstance(purposes, list) or any(item not in ("commercial_training", "evaluation") for item in purposes) or len(purposes) != len(set(purposes)):
            raise SplitError("invalid_consent_purposes")
        expires = utc(grant["expires_at"])
        if not start < expires <= end:
            raise SplitError("invalid_consent_expiry")
        grants[grant["record_id"]] = grant
        if grant["status"] == "granted" and set(purposes) == {"commercial_training", "evaluation"} and now < expires:
            allowed.add(grant["record_id"])
    return allowed, grants


def active_consent(policy_root, signed, key):
    """The protected current anchor is authoritative, never an archive argument."""
    current = read_json(Path(policy_root) / "training/data/consent/current.json")
    if not isinstance(current, dict) or set(current) != {"schema", "payload", "hmac_sha256"} or current["schema"] != "fdec-signed-consent/v1" or not is_hash(current["hmac_sha256"]) or not hmac.compare_digest(current["hmac_sha256"], envelope(current["payload"], key)["hmac_sha256"]):
        raise SplitError("untrusted_current_consent")
    if digest(current) != digest(signed):
        raise SplitError("consent_snapshot_no_longer_current")


def activate_consent(inventory, signed, *, key, policy_root=ROOT, now=None):
    """Data-owner operation: monotonic snapshots, immutable history, atomic anchor."""
    validate_inventory(inventory)
    now = datetime.now(timezone.utc) if now is None else now
    consent(inventory, signed, key, now)
    directory = reject_links(Path(policy_root) / "training/data/consent").resolve()
    boundary = Path(policy_root).resolve() / "training/data"
    if not directory.is_relative_to(boundary):
        raise SplitError("unsafe_consent_authority_path")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    anchor = directory / "current.json"
    reject_links(anchor)
    lock = directory / ".activate.lock"
    staging = directory / (".current-" + secrets.token_hex(16) + ".part")
    owned_lock = False
    try:
        with lock.open("x", encoding="ascii") as handle:
            handle.write("consent-activation\n")
        owned_lock = True
        current = read_json(anchor) if anchor.exists() else None
        if current is not None:
            active_consent(policy_root, current, key)
            if digest(current) == digest(signed):
                return digest(signed)
        expected_revision = 1 if current is None else current["payload"]["revision"] + 1
        expected_previous = None if current is None else digest(current)
        if signed["payload"]["revision"] != expected_revision or signed["payload"]["previous_snapshot_sha256"] != expected_previous:
            raise SplitError("nonmonotonic_consent_activation")
        archive = directory / f"revision-{expected_revision}-{digest(signed)}.json"
        data = (canonical_json(signed) + "\n").encode("utf-8")
        if archive.exists():
            if reject_links(archive).read_bytes() != data:
                raise SplitError("consent_history_changed")
        else:
            _write(archive, data)
        _write(staging, data)
        os.replace(staging, anchor)
        return digest(signed)
    except SplitError:
        raise
    except Exception:
        raise SplitError("consent_activation_failed") from None
    finally:
        if staging.exists():
            staging.unlink()
        if owned_lock:
            lock.unlink()


def lineage_components(records):
    parent = list(range(len(records)))
    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index
    def union(left, right):
        parent[find(right)] = find(left)
    seen = {}
    for index, row in enumerate(records):
        keys = [("source", row["source"]["dataset_id"]), ("content", row["content_sha256"])]
        if row["thread_id"] is not None:
            keys.append(("thread", row["thread_id"]))
        keys.extend(("family", value) for value in row["family_ids"])
        for key in keys:
            if key in seen:
                union(index, seen[key])
            else:
                seen[key] = index

    return find, union


def collect_components(records, find):
    groups = defaultdict(list)
    for index, row in enumerate(records):
        groups[find(index)].append(row)
    return sorted((sorted(group, key=lambda row: row["record_id"]) for group in groups.values()), key=lambda group: group[0]["record_id"])


def components(records):
    find, union = lineage_components(records)
    # Avoid quadratic self-comparisons within an already connected source.
    initial_roots = [find(index) for index in range(len(records))]
    if len(set(initial_roots)) == 1:
        return [sorted(records, key=lambda row: row["record_id"])]
    postings = defaultdict(lambda: defaultdict(list))
    features_by_record = [set(row["shingles"]) for row in records]
    compared = 0
    for index, values in enumerate(features_by_record):
        candidates = set()
        for value in sorted(values):
            for root, previous_indexes in postings[value].items():
                if find(root) != find(index):
                    candidates.update(previous_indexes)
            postings[value][initial_roots[index]].append(index)
        for other in sorted(candidates):
            if find(index) == find(other):
                continue
            compared += 1
            if compared > MAX_COMPARISONS:
                raise SplitError("near_duplicate_comparison_budget_exceeded")
            previous = features_by_record[other]
            if len(values & previous) * 100 >= len(values | previous) * 80:
                union(index, other)
    return collect_components(records, find)


def assign(groups, seed, ratios):
    if not integer(seed, 2**32 - 1) or not isinstance(ratios, dict) or set(ratios) != set(ROLES) or any(type(value) is not int or not 1 <= value <= 100 for value in ratios.values()) or sum(ratios.values()) != 100:
        raise SplitError("invalid_split_policy")
    if len(groups) < 3:
        raise SplitError("insufficient_independent_groups")
    ranked = sorted(groups, key=lambda group: (-len(group), digest([seed, [row["record_id"] for row in group]])))
    total = sum(len(group) for group in ranked)
    counts = dict.fromkeys(ROLES, 0)
    assignments = []
    for index, group in enumerate(ranked):
        group_id = digest([row["record_id"] for row in group])
        empty = [role for role in ROLES if counts[role] == 0]
        options = empty if len(ranked) - index == len(empty) else ROLES
        def cost(role):
            before = counts[role] * 100 - total * ratios[role]
            after = (counts[role] + len(group)) * 100 - total * ratios[role]
            return after**2 - before**2, digest([seed, group_id, role])
        role = min(options, key=cost)
        counts[role] += len(group)
        assignments.extend({"record_id": row["record_id"], "group_id": group_id, "split": role, "source_sha256": digest(row["source"]), "provenance_sha256": digest(row["provenance"])} for row in group)
    return sorted(assignments, key=lambda item: item["record_id"]), counts


def plan_manifest(inventory, signed, *, key, seed, ratios, policy_root=ROOT, now=None):
    """Verify current authority/rights and produce a text-free deterministic plan."""
    try:
        validate_inventory(inventory)
        now = datetime.now(timezone.utc) if now is None else now
        allowed, grants = consent(inventory, signed, key, now)
        active_consent(policy_root, signed, key)
        from disk_inventory import DiskInventory, packed_components

        records = sorted(inventory_rows(inventory), key=lambda row: row["record_id"])
        source_grants = []
        for encoded in sorted({canonical_json(row["source"]) for row in records}):
            source = json.loads(encoded)
            for purpose in ("commercial_training", "evaluation"):
                if source["dataset_id"] == SINABIS_ID:
                    from sinabis_source import assert_source

                    admitted = assert_source(source, purpose=purpose, policy_root=policy_root)
                    descriptor = admitted["descriptor"]
                    audit_sha256 = admitted["origin_policy_sha256"]
                elif source["dataset_id"] == GEMMA_ID:
                    from gemma_source import assert_source

                    descriptor = assert_source(source, purpose=purpose, policy_root=policy_root)["descriptor"]
                    audit_sha256 = descriptor["audit_sha256"]
                else:
                    descriptor = inclusion(source["dataset_id"], source["revision"], source["artifact"], purpose, "specialized-email-classifier", policy_root)
                    audit_sha256 = descriptor["audit_sha256"]
                if descriptor["sha256"] != source["sha256"]:
                    raise SplitError("source_artifact_changed")
                source_grants.append({"source_sha256": digest(source), "purpose": purpose, "descriptor_sha256": digest(descriptor), "audit_sha256": audit_sha256})
        selected, excluded = [], []
        groups = packed_components(inventory)[0] if isinstance(inventory, DiskInventory) else components(records)
        for group in groups:
            if all(row["record_id"] in allowed for row in group):
                selected.append(group)
            else:
                # Withdrawal quarantines every linked copy, including source peers.
                excluded.extend(row["record_id"] for row in group)
        if not selected:
            raise SplitError("no_consent_admitted_rows")
        assignments, counts = assign(selected, seed, ratios)
        for assignment in assignments:
            assignment["consent_grant_sha256"] = digest(grants[assignment["record_id"]])
        return {"schema": VERSION, "implementation_sha256": implementation_hash(), "feature_policy": dict(FEATURE_POLICY), "inventory_sha256": inventory_digest(inventory), "consent_snapshot_sha256": digest(signed), "consent_revision": signed["payload"]["revision"], "consent_valid_until": signed["payload"]["valid_until"], "source_grants": source_grants, "seed": seed, "ratios": dict(ratios), "counts": counts, "ratio_error_hundredths": {role: counts[role] * 100 - len(assignments) * ratios[role] for role in ROLES}, "assignments": assignments, "excluded_record_ids": sorted(excluded)}
    except SplitError:
        raise
    except Exception:
        raise SplitError("split_admission_failed") from None


def _write(path, data):
    with path.open("xb") as target:
        target.write(data)
        target.flush()
        os.fsync(target.fileno())


def build(inventory, signed, *, output_dir, key, seed=1, ratios=None, opt_in=False, policy_root=ROOT, now=None):
    if opt_in is not True:
        raise SplitError("explicit_opt_in_required")
    ratios = {"train": 80, "validation": 10, "test": 10} if ratios is None else ratios
    manifest = plan_manifest(inventory, signed, key=key, seed=seed, ratios=ratios, policy_root=policy_root, now=now)
    try:
        output = private_output(output_dir, policy_root)
    except Exception:
        raise SplitError("unsafe_manifest_output") from None
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
        content = (canonical_json(manifest) + "\n").encode("utf-8")
        _write(output / "manifest.json", content)
        receipt = {"schema": "fdec-split-receipt/v1", "manifest_sha256": hashlib.sha256(content).hexdigest(), "manifest_file": "manifest.json", "rows": len(manifest["assignments"]), "counts": manifest["counts"]}
        _write(output / ".receipt.part", (canonical_json(receipt) + "\n").encode("utf-8"))
        active_consent(policy_root, signed, key)
        os.replace(output / ".receipt.part", output / "receipt.json")
        return receipt
    except Exception:
        if owned:
            remove_owned(output, token)
        for parent in reversed(created):
            try:
                parent.rmdir()
            except OSError:
                pass
        raise SplitError("manifest_write_failed") from None


def verify(output_dir, inventory, signed, *, key, policy_root=ROOT, now=None, include_manifest=False):
    try:
        output = reject_links(output_dir)
        receipt = read_json(output / "receipt.json", 4096)
        content = read_bytes(output / "manifest.json")
        manifest = strict_json(content.decode("utf-8-sig", errors="strict"))
        if set(receipt) != {"schema", "manifest_sha256", "manifest_file", "rows", "counts"} or receipt["schema"] != "fdec-split-receipt/v1" or receipt["manifest_file"] != "manifest.json" or receipt["manifest_sha256"] != hashlib.sha256(content).hexdigest():
            raise SplitError("changed_split_receipt")
        expected = plan_manifest(inventory, signed, key=key, seed=manifest["seed"], ratios=manifest["ratios"], policy_root=policy_root, now=now)
        old_implementation = manifest.get("implementation_sha256")
        from disk_inventory import DiskInventory

        source_ids = {row["source"]["dataset_id"] for row in inventory_rows(inventory)}
        if not isinstance(inventory, DiskInventory) and (
            old_implementation == GEMMA_SPLIT_IMPLEMENTATION_SHA256
            or GEMMA_ID not in source_ids and (
                old_implementation == SINABIS_SPLIT_IMPLEMENTATION_SHA256
                or old_implementation == LEGACY_IMPLEMENTATION_SHA256 and SINABIS_ID not in source_ids
            )
        ):
            # Replay every other field against current rights, consent and grouping.
            expected["implementation_sha256"] = old_implementation
        if manifest != expected or receipt["rows"] != len(expected["assignments"]) or receipt["counts"] != expected["counts"]:
            raise SplitError("split_provenance_or_contamination_changed")
        active_consent(policy_root, signed, key)
        return {"receipt": receipt, "manifest": manifest} if include_manifest else receipt
    except SplitError:
        raise
    except Exception:
        raise SplitError("split_verification_failed") from None
