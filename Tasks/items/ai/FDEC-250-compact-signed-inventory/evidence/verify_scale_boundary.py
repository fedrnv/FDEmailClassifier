"""Verify storage and grouping at the 30-million fingerprint boundary."""

from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "training/splits"))

import disk_inventory as disk
import split_data as splits
from test_splits import SplitTests

ROWS_PER_GROUP = 2500
FINGERPRINTS_PER_ROW = 4000


def rows(template):
    for group in range(3):
        source = dict(template["source"], dataset_id=f"fixture/synthetic-group-{group}")
        fingerprints = sorted(splits.digest(["fingerprint", group, index])
                              for index in range(FINGERPRINTS_PER_ROW))
        for index in range(ROWS_PER_GROUP):
            row = deepcopy(template)
            row["source"] = source
            row["content_sha256"] = splits.digest(["content", group, index])
            row["thread_id"], row["family_ids"], row["shingles"] = None, [], fingerprints
            row["record_id"] = splits.digest([source, row["content_sha256"], row["provenance"]["source_rows"]])
            yield row


def main():
    scratch, = sys.argv[1:]
    fixture = SplitTests()
    try:
        fixture.setUp()
        with TemporaryDirectory(prefix="fdec-fingerprint-boundary-", dir=scratch) as temporary:
            output = Path(temporary) / "inventory"
            manifest = disk.pack(rows(fixture.inventory["records"][0]), output_dir=output, opt_in=True)
            inventory = disk.open_inventory(output)
            groups, comparisons = disk.packed_components(inventory)
            sizes = sorted(map(len, groups))
            if manifest["fingerprints"] != 30_000_000 or sizes != [ROWS_PER_GROUP] * 3:
                raise ValueError("fingerprint_boundary_check_mismatch")
            print(json.dumps(dict(fingerprints=manifest["fingerprints"], rows=manifest["rows"],
                                  group_sizes=sizes, comparisons=comparisons), sort_keys=True))
    finally:
        fixture.doCleanups()


if __name__ == "__main__":
    main()
