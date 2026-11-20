"""Frozen classification-metadata arithmetic only. Never invokes a model."""
import hashlib
import json
from pathlib import Path

from classification_metrics import measure
from evaluate import implementation_hash, publish, Parser
from ingest_dataset import strict_json

FIXTURE = Path(__file__).with_name("fixtures") / "metric-oracle-v1.json"
FIXTURE_SHA256 = "263edd2a7eebca51781a929536133f4fe226eb3e5fba6be16744bbd1e6131c97"


def report():
    raw = FIXTURE.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise ValueError("frozen_metric_fixture_changed")
    data = strict_json(raw.decode("utf-8"))
    return dict(schema="fdec-multilabel-report/v1", scope="software-metric-oracle-only", actual_model_executed=False,
                model_quality_claim=False, fixture_sha256=FIXTURE_SHA256, implementation_sha256=implementation_hash(),
                metrics=measure(data["gold"], data["predictions"]), public_artifact_release_approved=False)


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        value = report()
        publish(args.output_dir, value, lambda: None)
        print(json.dumps(dict(scope=value["scope"], actual_model_executed=False, rows=value["metrics"]["overall"]["rows"])))
        return 0
    except Exception:
        print("metric_oracle_rejected")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
