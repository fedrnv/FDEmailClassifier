"""Replay one exact, independently audited Gemma email source."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sys

import training_boundary as boundary
from ingest_dataset import private_output, reject_links, remove_owned, strict_json
from normalize_email import VERSION, canonical_json, text

IDENTITY = {
    "dataset_id": "Kamisori-daijin/email-datasets-20k",
    "revision": "7c615780b64770697e8e517c9d3e70db470cadf1",
    "artifact": "email-datasets-20k-v2.jsonl",
    "sha256": "349c6afd429f2d55eaaece9794ee0a9d625771e4369c8fb45c5e8392f6af31c7",
}
SIZE = 21_844_808
RUN_SCHEMA = "fdec-gemma-reviewed-run/v1"
EVIDENCE = Path("Tasks/items/ai/FDEC-248-verify-pinned-gemma-source/evidence")
AUDIT = "9671cf0248ed356e84781cc07f7b18074d4ef2bf9aeeb06005a9e19ab4d88ae0"
AGGREGATE = "c94e31d7a8e211ef646fd24be00ccd6e890602871410bd57c1349d253d850dad"
CONTACT = re.compile(r"[^\s@]+@[^\s@]+\.[A-Za-z]{2,}|https?://", re.I)


def assert_source(identity, *, purpose, policy_root=boundary.ROOT):
    if identity != IDENTITY or purpose not in boundary.PURPOSES:
        raise boundary.TrainingBoundaryError("unapproved_gemma_source")
    for name, sha256 in (("verification-v1.md", AUDIT), ("aggregate-v1.json", AGGREGATE)):
        path = reject_links(Path(policy_root) / EVIDENCE / name).resolve()
        if not path.is_relative_to(Path(policy_root).resolve()) or boundary.text_hash(path) != sha256:
            raise boundary.TrainingBoundaryError("gemma_audit_evidence_changed")
    return {
        "descriptor": dict(IDENTITY, size=SIZE, license="Apache-2.0", purpose=purpose,
                           target="specialized-email-classifier", audit_sha256=AUDIT,
                           attribution=f"https://huggingface.co/datasets/{IDENTITY['dataset_id']}/tree/{IDENTITY['revision']}"),
        "scope": "screened-publisher-declared-gemma-text-only",
        "requires_split_and_consent": True,
    }


def snapshot(path):
    with reject_links(path).open("rb") as stream:
        raw = stream.read(SIZE + 1)
    if len(raw) != SIZE or hashlib.sha256(raw).hexdigest() != IDENTITY["sha256"]:
        raise boundary.TrainingBoundaryError("gemma_source_identity_changed")
    return raw


def project(raw):
    rows, identifiers = {}, set()
    for source_row, line in enumerate(raw.splitlines()):
        item = strict_json(line.decode("utf-8"))
        if (set(item) != {"id", "instruction", "output"} or type(item["id"]) is not int
                or not isinstance(item["instruction"], str) or item["id"] in identifiers):
            raise boundary.TrainingBoundaryError("invalid_gemma_source_row")
        identifiers.add(item["id"])
        fields = strict_json(item["output"])
        if not isinstance(fields, dict) or set(fields) != {"subject", "body"}:
            continue
        subject, body = text(fields["subject"], 4096), text(fields["body"], 200_000)
        if not subject or not body or CONTACT.search(subject) or CONTACT.search(body):
            continue
        content_id = hashlib.sha256((VERSION + "\0" + canonical_json([subject, body])).encode()).hexdigest()
        record = rows.setdefault(content_id, {
            "schema": "fdec-normalized-email/v1", "source": dict(IDENTITY),
            "content_id": content_id, "subject": subject, "body": body, "annotations": [],
        })
        record["annotations"].append({"source_row": source_row})
    if not rows:
        raise boundary.TrainingBoundaryError("no_gemma_source_rows")
    return [rows[key] for key in sorted(rows)]


def replay(raw, *, purpose, policy_root=boundary.ROOT):
    admitted = assert_source(IDENTITY, purpose=purpose, policy_root=policy_root)
    if len(raw) != SIZE or hashlib.sha256(raw).hexdigest() != IDENTITY["sha256"]:
        raise boundary.TrainingBoundaryError("gemma_source_identity_changed")
    records = project(raw)
    implementation = hashlib.sha256()
    for path in (Path(__file__), boundary.ROOT / "training/scripts/normalize_email.py"):
        implementation.update(path.read_bytes().replace(b"\r\n", b"\n"))
    receipt = {
        "schema": RUN_SCHEMA, "input": admitted["descriptor"],
        "normalization_version": VERSION, "implementation_sha256": implementation.hexdigest(),
        "records_sha256": hashlib.sha256(canonical_json(records).encode()).hexdigest(),
    }
    return receipt, records


def create_run(source, output_dir, *, purpose, policy_root=boundary.ROOT):
    raw = snapshot(source)
    receipt, records = replay(raw, purpose=purpose, policy_root=policy_root)
    output = private_output(output_dir, policy_root)
    marker = secrets.token_hex(32)
    output.mkdir(mode=0o700)
    try:
        (output / ".owner").write_text(marker, encoding="ascii")
        for name, content in (("source.jsonl", raw), (".receipt.tmp", (canonical_json(receipt) + "\n").encode())):
            with (output / name).open("xb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        (output / ".receipt.tmp").rename(output / "receipt.json")
    except Exception:
        remove_owned(output, marker)
        raise
    return {"rows": len(records), "records_sha256": receipt["records_sha256"], "schema": RUN_SCHEMA}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opt-in", action="store_true", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--purpose", choices=boundary.PURPOSES, default="commercial_training")
    args = parser.parse_args()
    try:
        print(json.dumps(create_run(args.source, args.output_dir, purpose=args.purpose), sort_keys=True))
    except Exception:
        print("gemma_cohort_preparation_rejected", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
