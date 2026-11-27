"""Local source audit. Emit aggregates only and never persist decoded text."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[5]
for area in ("training/augmentation", "training/scripts"):
    sys.path.insert(0, str(ROOT / area))

from ingest_dataset import reject_links, strict_json
from normalize_email import text
from sinabis_source import features
from training_boundary import admit_training_run

SIZE = 21_844_808
SHA256 = "349c6afd429f2d55eaaece9794ee0a9d625771e4369c8fb45c5e8392f6af31c7"
CONTACT = re.compile(r"[^\s@]+@[^\s@]+\.[A-Za-z]{2,}|https?://", re.I)
SAMPLE = 32


def verify(raw):
    if len(raw) != SIZE or hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError("gemma_artifact_identity_mismatch")


def read_rows(path):
    with reject_links(path).open("rb") as stream:
        raw = stream.read(SIZE + 1)
    verify(raw)
    counts = Counter()
    rows = {}
    for line in raw.splitlines():
        row = strict_json(line.decode("utf-8"))
        if set(row) != {"id", "instruction", "output"} or type(row["id"]) is not int:
            raise ValueError("unexpected_row_schema")
        output = strict_json(row["output"])
        if row["id"] in rows:
            raise ValueError("duplicate_row_id")
        if set(output) != {"subject", "body"}:
            counts["noncanonical_output_fields"] += 1
            continue
        subject, body = normalize(output["subject"], output["body"])
        if not subject or not body:
            counts["empty_subject_or_body"] += 1
            continue
        if CONTACT.search(subject) or CONTACT.search(body):
            counts["contact_or_link_pattern"] += 1
            continue
        rows[row["id"]] = (subject, body)
    return rows, counts


def normalize(subject, body):
    return text(subject, 4096), text(body, 200_000)


def compare(rows, source_run):
    prior = admit_training_run(source_run, include_records=True)
    candidate_texts = set(rows.values())
    ids = sorted(rows, key=lambda value: hashlib.sha256(str(value).encode()).digest())[:SAMPLE]
    sample = [features(*rows[rid]) for rid in ids]
    exact, near = 0, 0
    for row in prior["records"]:
        candidate = normalize(row["subject"], row["body"])
        exact += candidate in candidate_texts
        grams = features(*candidate)
        for target in sample:
            low, high = sorted((len(grams), len(target)))
            if 5 * low >= 4 * high and 5 * len(grams & target) >= 4 * len(grams | target):
                near += 1
    return {"prior_rows": prior["rows"], "prior_records_sha256": prior["records_sha256"],
            "exact_overlapping_prior_rows": exact, "sampled_candidate_rows": len(sample),
            "near_match_pairs": near}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?")
    parser.add_argument("--prior-run", action="append", default=[])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        try:
            verify(b"x" * SIZE)
        except ValueError as error:
            if str(error) == "gemma_artifact_identity_mismatch":
                print("PASS exact-size changed bytes rejected before parsing")
                return 0
        return 2
    try:
        if not args.artifact or len(args.prior_run) != 2:
            raise ValueError("two_prior_runs_required")
        rows, rejected = read_rows(args.artifact)
        report = {"artifact_sha256": SHA256, "candidate_rows": len(rows), "screened_out": dict(rejected),
                  "unique_candidate_text_pairs": len(set(rows.values())),
                  "comparisons": [compare(rows, run) for run in args.prior_run],
                  "training_admitted": False}
        print(json.dumps(report, sort_keys=True))
    except Exception:
        print("gemma_cohort_inspection_failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
