"""Compare the recomputed source projection with the signed inventory."""

from contextlib import contextmanager

from disk_inventory import DiskInventory, WIDTH


@contextmanager
def record_matcher(inventory):
    if not isinstance(inventory, DiskInventory):
        yield lambda prepared, target: prepared == target
        return

    positions = {row["record_id"]: offset for row, offset in zip(inventory.records, inventory.offsets, strict=True)}
    with inventory.fingerprint_snapshot() as payload:
        def match(prepared, target):
            metadata = {field: value for field, value in prepared.items() if field != "shingles"}
            if metadata != target:
                return False
            start, count = positions[target["record_id"]]
            shingles = prepared["shingles"]
            return len(shingles) == count and bytes.fromhex("".join(shingles)) == payload[start:start + count * WIDTH]

        yield match
