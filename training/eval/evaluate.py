"""Full metric reporting for admitted real inference; no arbitrary fixture-model CLI."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from classification_metrics import measure
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "training/baseline"))
from baseline import Parser, publish
from admission import admit, recheck
from local_model import LocalQwen
from prompt import messages, parse, PROMPT_SHA256
from baseline_metrics import EvaluationError
import split_data as splits
from ingest_dataset import private_output, reject_links


def implementation_hash():
    paths = sorted(Path(__file__).parent.glob("*.py")) + [ROOT / relative for relative in ("training/baseline/admission.py", "training/baseline/baseline.py", "training/baseline/local_model.py", "training/baseline/prompt.py", "training/baseline/qwen-stock-v1.json", "training/labels/map_annotations.py", "training/augmentation/training_boundary.py", "training/splits/split_data.py", "training/splits/disk_inventory.py", "training/splits/source_replay.py")]
    return hashlib.sha256(b"".join(path.relative_to(ROOT).as_posix().encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n") for path in paths)).hexdigest()


def run(args):
    if not args.opt_in:
        raise EvaluationError("explicit_opt_in_required")
    output = private_output(args.output_dir, ROOT)
    key = splits.authority_key()
    arguments = dict(inventory_path=args.inventory, consent_path=args.consent, split_dir=args.split_dir, annotations_path=args.annotations, source_runs=args.source_run, key=key)
    snapshot = admit(**arguments)
    model = LocalQwen(reject_links(args.model_dir))
    predictions = []
    for row in snapshot.gold:
        recheck(snapshot, key=key)
        try:
            response = model.infer(messages(*snapshot.texts[row["record_id"]]))
        except EvaluationError as error:
            if str(error) != "incomplete_model_generation":
                raise
            predictions.append(None)
            continue
        try:
            predictions.append(parse(response))
        except EvaluationError:
            predictions.append(None)
    if admit(**arguments) != snapshot:
        raise EvaluationError("evaluation_inputs_changed")
    recheck(snapshot, key=key)
    report = dict(schema="fdec-multilabel-report/v1", scope="admitted-stock-model-held-out-evaluation", actual_model_executed=True,
                  created_at=datetime.now(timezone.utc).isoformat(), model=model.identity, prompt_sha256=PROMPT_SHA256,
                  inventory_sha256=splits.inventory_digest(snapshot.inventory), consent_sha256=splits.digest(snapshot.consent), split_receipt_sha256=splits.digest(snapshot.split["receipt"]),
                  annotations_sha256=snapshot.annotations_sha256, review_sha256=snapshot.review_sha256, implementation_sha256=implementation_hash(),
                  metrics=measure(snapshot.gold, predictions), public_artifact_release_approved=False)
    publish(output, report, lambda: recheck(snapshot, key=key))
    return {"status": "measured", "rows": len(snapshot.gold), "languages": len(report["metrics"]["by_language"])}


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--opt-in", action="store_true")
    for name in ("inventory", "consent", "split-dir", "annotations", "model-dir", "output-dir"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--source-run", action="append", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(args), sort_keys=True))
        return 0
    except Exception:
        print("evaluation_rejected", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
