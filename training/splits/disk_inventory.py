"""Private compact split inventory. Fingerprints retain their full SHA-256 width."""

from collections import Counter, defaultdict
from array import array
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import mmap
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import tempfile

import split_data as splits

SCHEMA = "fdec-split-inventory/v2"
WIDTH = 32
MAX_FINGERPRINTS = 30_000_000
MAX_EXACT_COMPARISONS = 30_000_000
MAX_METADATA_LINE = 1_500_000
MAX_METADATA_BYTES = 200_000_000
FILES = {".owner", "manifest.json", "records.jsonl", "shingles.bin"}


@dataclass(frozen=True)
class DiskInventory:
    path: Path
    manifest: dict
    records: tuple
    offsets: tuple

    def rows(self):
        """Return metadata records; fingerprints remain in the verified payload."""
        return self.records

    @contextmanager
    def fingerprint_snapshot(self):
        """Group only over an authenticated, process-owned snapshot."""
        with tempfile.TemporaryFile() as snapshot:
            self.verify_fingerprint_file(snapshot)
            with mmap.mmap(snapshot.fileno(), 0, access=mmap.ACCESS_READ) as view:
                yield view

    def verify_fingerprint_file(self, snapshot=None):
        identity = hashlib.sha256()
        with private_file(self.path / "shingles.bin") as stream:
            for _, count in self.offsets:
                block = stream.read(count * WIDTH)
                if len(block) != count * WIDTH:
                    raise splits.SplitError("truncated_disk_fingerprints")
                values = fingerprints(block)
                if any(a >= b for a, b in zip(values, values[1:])):
                    raise splits.SplitError("invalid_disk_fingerprint_order")
                identity.update(block)
                if snapshot is not None:
                    snapshot.write(block)
            if stream.read(1) or identity.hexdigest() != self.manifest["shingles_sha256"]:
                raise splits.SplitError("changed_disk_fingerprints")
        if snapshot is not None:
            snapshot.flush()


def fingerprints(block):
    return [block[offset:offset + WIDTH] for offset in range(0, len(block), WIDTH)]


def require_private(path, *, directory=False):
    if os.name != "posix":
        raise splits.SplitError("disk_inventory_requires_posix_private_storage")
    path = splits.reject_links(path)
    info = path.stat()
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if not kind(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise splits.SplitError("disk_inventory_path_not_private")
    if sys.platform == "darwin":
        status = subprocess.run(["/bin/ls", "-lde", str(path)], capture_output=True, text=True, timeout=10)
        fields = status.stdout.split()
        if status.returncode or not fields or "+" in fields[0]:
            raise splits.SplitError("disk_inventory_acl_not_private")
    if not directory and info.st_nlink != 1:
        raise splits.SplitError("disk_inventory_path_not_private")
    return path


@contextmanager
def private_file(path):
    path = require_private(path)
    # Check the descriptor as well, without following a replaced final link.
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077 or info.st_nlink != 1:
            raise splits.SplitError("disk_inventory_path_not_private")
        yield stream


def open_inventory(directory):
    try:
        directory = require_private(directory, directory=True)
        if {path.name for path in directory.iterdir()} != FILES:
            raise splits.SplitError("invalid_disk_inventory_files")
        require_private(directory / ".owner")
        with private_file(directory / "manifest.json") as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            raise splits.SplitError("invalid_disk_inventory_manifest")
        manifest = splits.strict_json(raw.decode("utf-8"))
        expected = {"schema", "normalization_version", "feature_policy", "rows", "fingerprints", "records_sha256", "shingles_sha256"}
        if not isinstance(manifest, dict) or set(manifest) != expected or manifest["schema"] != SCHEMA or manifest["normalization_version"] != splits.NORMALIZATION_VERSION or manifest["feature_policy"] != splits.FEATURE_POLICY:
            raise splits.SplitError("invalid_disk_inventory_manifest")
        if not splits.integer(manifest["rows"], splits.MAX_ROWS) or not splits.integer(manifest["fingerprints"], MAX_FINGERPRINTS) or not 1 <= manifest["rows"] <= manifest["fingerprints"]:
            raise splits.SplitError("disk_inventory_budget_exceeded")
        if not all(splits.is_hash(manifest[name]) for name in ("records_sha256", "shingles_sha256")):
            raise splits.SplitError("invalid_disk_inventory_manifest")
        if require_private(directory / "shingles.bin").stat().st_size != manifest["fingerprints"] * WIDTH:
            raise splits.SplitError("invalid_disk_fingerprint_size")
        records, offsets, seen, total = [], [], set(), 0
        metadata_bytes = 0
        identity = hashlib.sha256()
        with private_file(directory / "records.jsonl") as stream:
            for _ in range(manifest["rows"]):
                raw = stream.readline(MAX_METADATA_LINE + 1)
                if len(raw) > MAX_METADATA_LINE or not raw.endswith(b"\n"):
                    raise splits.SplitError("invalid_disk_inventory_record_line")
                metadata_bytes += len(raw)
                if metadata_bytes > MAX_METADATA_BYTES:
                    raise splits.SplitError("disk_inventory_metadata_budget_exceeded")
                identity.update(raw)
                record = splits.strict_json(raw.decode("utf-8"))
                if not isinstance(record, dict) or "shingles" in record:
                    raise splits.SplitError("invalid_disk_inventory_record")
                count = record.pop("fingerprint_count", None)
                if not splits.integer(count, splits.MAX_FEATURES) or not count:
                    raise splits.SplitError("invalid_disk_inventory_fingerprint_count")
                splits.validate_record(record, metadata_only=True)
                if record["record_id"] in seen:
                    raise splits.SplitError("duplicate_inventory_record")
                seen.add(record["record_id"])
                records.append(record)
                offsets.append((total * WIDTH, count))
                total += count
                if total > manifest["fingerprints"]:
                    raise splits.SplitError("changed_disk_inventory_records")
            if stream.read(1) or identity.hexdigest() != manifest["records_sha256"] or total != manifest["fingerprints"]:
                raise splits.SplitError("changed_disk_inventory_records")
        return DiskInventory(directory, manifest, tuple(records), tuple(offsets))
    except splits.SplitError:
        raise
    except Exception:
        raise splits.SplitError("invalid_disk_inventory") from None


def pack(records, *, output_dir, policy_root=splits.ROOT, opt_in=False):
    """Pack already-projected provenance records without creating authority."""
    if opt_in is not True:
        raise splits.SplitError("explicit_opt_in_required")
    if os.name != "posix":
        raise splits.SplitError("disk_inventory_requires_posix_private_storage")
    output = splits.private_output(output_dir, policy_root)
    output.mkdir(mode=0o700)
    token = secrets.token_hex(16)
    try:
        if sys.platform == "darwin":
            status = subprocess.run(["/bin/chmod", "-N", str(output)], capture_output=True, timeout=10)
            if status.returncode:
                raise splits.SplitError("disk_inventory_acl_not_private")
        splits._write(output / ".owner", token.encode("ascii"))
        (output / ".owner").chmod(0o600)
        row_identity, shingle_identity = hashlib.sha256(), hashlib.sha256()
        seen, total, metadata_bytes = set(), 0, 0
        with (output / "records.jsonl").open("xb") as metadata, (output / "shingles.bin").open("xb") as payload:
            for stream in (metadata, payload):
                os.fchmod(stream.fileno(), 0o600)
            for record in records:
                splits.validate_record(record)
                identifier = record["record_id"]
                if identifier in seen:
                    raise splits.SplitError("duplicate_inventory_record")
                seen.add(identifier)
                count = len(record["shingles"])
                total += count
                if len(seen) > splits.MAX_ROWS or total > MAX_FINGERPRINTS:
                    raise splits.SplitError("disk_inventory_budget_exceeded")
                row = {name: value for name, value in record.items() if name != "shingles"}
                row["fingerprint_count"] = count
                line = (splits.canonical_json(row) + "\n").encode("utf-8")
                metadata_bytes += len(line)
                if len(line) > MAX_METADATA_LINE or metadata_bytes > MAX_METADATA_BYTES:
                    raise splits.SplitError("disk_inventory_metadata_budget_exceeded")
                block = bytes.fromhex("".join(record["shingles"]))
                metadata.write(line)
                payload.write(block)
                row_identity.update(line)
                shingle_identity.update(block)
            if not seen:
                raise splits.SplitError("empty_disk_inventory")
            for stream in (metadata, payload):
                stream.flush()
                os.fsync(stream.fileno())
        manifest = dict(schema=SCHEMA, normalization_version=splits.NORMALIZATION_VERSION,
                        feature_policy=splits.FEATURE_POLICY, rows=len(seen), fingerprints=total,
                        records_sha256=row_identity.hexdigest(), shingles_sha256=shingle_identity.hexdigest())
        # Publish the manifest last. The already private directory protects any
        # staging names left by an interrupted process.
        stage = output / ".manifest.part"
        splits._write(stage, (splits.canonical_json(manifest) + "\n").encode("utf-8"))
        stage.chmod(0o600)
        stage.rename(output / "manifest.json")
        return manifest
    except Exception:
        if (output / ".owner").is_file():
            splits.remove_owned(output, token)
        else:
            output.rmdir()
        raise


def packed_components(inventory):
    records = inventory.rows()
    find, union = splits.lineage_components(records)
    initial = [find(index) for index in range(len(records))]
    roots = len(set(initial))
    comparisons = 0
    with inventory.fingerprint_snapshot() as payload:
        if roots == 1:
            return splits.collect_components(records, find), comparisons

        def values(index):
            offset, count = inventory.offsets[index]
            return fingerprints(payload[offset:offset + count * WIDTH])

        frequency = Counter()
        for index in range(len(records)):
            frequency.update(values(index))
        previous_values = lru_cache(maxsize=256)(lambda index: set(values(index)))
        postings = defaultdict(dict)
        ordered = sorted(range(len(records)), key=lambda index: inventory.offsets[index][1])
        for index in ordered:
            current = values(index)
            size = len(current)
            minimum = (4 * size + 4) // 5
            # If Jaccard >= 4/5, the smallest common token occurs in both
            # prefixes in this shared order. Sorting is stable on hash ties.
            prefix = sorted(current, key=frequency.__getitem__)[:size - minimum + 1]
            selected = set(current)
            seen = set()
            for token in prefix:
                bucket = postings[token]
                for root, indexes in bucket.items():
                    if find(root) == find(index):
                        continue
                    for other in reversed(indexes):
                        other_size = inventory.offsets[other][1]
                        if other_size < minimum:
                            break
                        if other in seen:
                            continue
                        seen.add(other)
                        comparisons += 1
                        if comparisons > MAX_EXACT_COMPARISONS:
                            raise splits.SplitError("near_duplicate_comparison_budget_exceeded")
                        if 9 * len(selected.intersection(previous_values(other))) >= 4 * (size + other_size):
                            union(index, other)
                            roots -= 1
                            break
                    if roots == 1:
                        return splits.collect_components(records, find), comparisons
                bucket.setdefault(initial[index], array("I")).append(index)
    return splits.collect_components(records, find), comparisons
