"""Inspect only pinned public-source metadata; no email text/labels in output."""

from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import sys

IDENTITY = {
    "dataset_id": "sinabis-group/sinabis-10k-synthetic-emails",
    "revision": "4b8e73e28074c94b9c70934501bee1ed8c98e395",
    "artifact": "data/train-00000-of-00001.parquet",
    "sha256": "4c016783ff5f69211f869448d8d87f24044e055deed0304d48793401383f4175",
}
SIZE = 7_133_232


def inspect(path):
    import pyarrow
    import pyarrow.parquet as pq

    if pyarrow.__version__ != "26.0.1":
        raise ValueError("unapproved_parquet_decoder")
    # Decode exactly the immutable bytes whose size/hash were checked.
    with Path(path).open("rb") as source:
        raw = source.read(SIZE + 1)
    if len(raw) != SIZE or hashlib.sha256(raw).hexdigest() != IDENTITY["sha256"]:
        raise ValueError("pinned_source_integrity_mismatch")
    columns = ["idx", "case_id", "case_size", "position", "model", "lang", "case_kind", "message_id", "in_reply_to", "duplicate_of"]
    rows = pq.read_table(io.BytesIO(raw), columns=columns).to_pylist()
    cases = defaultdict(list)
    for row in rows:
        cases[row["case_id"]].append(row)
    message_ids = Counter(row["message_id"] for row in rows if row["message_id"])
    return {
        "schema": "fdec-sinabis-metadata-inspection/v1",
        "source": IDENTITY,
        "bytes": len(raw),
        "rows": len(rows),
        "cases": len(cases),
        "complete_cases": sum(len(group) == group[0]["case_size"] and sorted(row["position"] for row in group) == list(range(1, len(group) + 1)) for group in cases.values()),
        "model_rows": [{"model": model, "rows": count} for model, count in sorted(Counter(row["model"] for row in rows).items())],
        "languages": dict(sorted(Counter(row["lang"] for row in rows).items())),
        "case_kinds": dict(sorted(Counter(row["case_kind"] for row in rows).items())),
        "unresolved_model_cases": sum(any(row["model"] == "qwen3.6" for row in group) for group in cases.values()),
        "duplicate_message_ids": sum(count - 1 for count in message_ids.values()),
        "unresolved_replies": sum(bool(row["in_reply_to"]) and row["in_reply_to"] not in message_ids for row in rows),
        "declared_duplicate_pointers": sum(bool(row["duplicate_of"]) for row in rows),
        "content_duplicate_check": "not_performed_by_metadata_inspection",
        "source_training_admission": "not_registered",
        "training_performed": False,
    }


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("expected_one_private_source_path")
        result = inspect(sys.argv[1])
    except Exception:
        # Do not expose paths or source/parser fragments through diagnostics.
        print("sinabis_metadata_inspection_failed", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
