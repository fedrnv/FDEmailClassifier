"""Unsigned local scale check of currently admitted source projections."""

from pathlib import Path
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "training/splits"))
import split_data as splits
from disk_inventory import open_inventory, pack, packed_components, private_file
from training_boundary import admit_training_run


def source_rows(paths):
    for private_run in paths:
        result = admit_training_run(private_run, include_records=True)
        receipt = splits.read_json(Path(private_run) / "receipt.json", 65_536)
        for row in result["records"]:
            yield splits.prepare_record(row, receipt, consent_id=splits.digest(["unsigned-scale-fixture", row["content_id"]]))


def main():
    source_descriptor, output = sys.argv[1:]
    with private_file(source_descriptor) as stream:
        paths = json.load(stream)
    if not isinstance(paths, list) or len(paths) != 3 or any(not isinstance(path, str) for path in paths):
        raise SystemExit("invalid_scale_source_descriptor")
    started = time.monotonic()
    manifest = pack(source_rows(paths), output_dir=output, opt_in=True)
    packed_time = time.monotonic()
    inventory = open_inventory(output)
    groups, comparisons = packed_components(inventory)
    sizes = sorted(map(len, groups))
    if manifest["rows"] != 33_131 or manifest["fingerprints"] != 20_119_151 or sizes != [3_905, 9_387, 19_839]:
        raise SystemExit("scale_workload_mismatch")
    print(json.dumps(dict(rows=manifest["rows"], fingerprints=manifest["fingerprints"],
                          group_sizes=sizes, comparisons=comparisons,
                          packed_storage_bytes=sum(item.stat().st_size for item in Path(output).iterdir()),
                          inventory_sha256=splits.digest(manifest), packing_seconds=round(packed_time-started, 3),
                          grouping_seconds=round(time.monotonic()-packed_time, 3),
                          scope="unsigned-local-scale-check"), sort_keys=True))


if __name__ == "__main__":
    main()
