"""Local explicit baseline command. No remote services, training or publication."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import sys

from admission import ROOT, REVIEW_ANCHOR, admit, recheck
import split_data as splits
from ingest_dataset import private_output, reject_links, remove_owned
from baseline_metrics import EvaluationError, score
from prompt import PROMPT_SHA256, messages, parse
from local_model import LocalQwen


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default error can echo a private input path or secret.
        self.exit(2, "baseline_arguments_invalid\n")


def run(args):
    if not args.opt_in:
        raise EvaluationError("explicit_opt_in_required")
    output = private_output(args.output_dir, ROOT)
    key = splits.authority_key()
    inputs = dict(inventory_path=args.inventory, consent_path=args.consent, split_dir=args.split_dir,
                  annotations_path=args.annotations, source_runs=args.source_run, key=key)
    snapshot = admit(**inputs)
    model = LocalQwen(reject_links(args.model_dir))
    predictions = []
    for row in snapshot.gold:
        recheck(snapshot, key=key)
        try:
            text = model.infer(messages(*snapshot.texts[row["record_id"]]))
        except EvaluationError as error:
            if str(error) != "incomplete_model_generation":
                raise
            predictions.append(None)
            continue
        try:
            predictions.append(parse(text))
        except EvaluationError:
            predictions.append(None)
    # Re-run actual split/rights/source/annotation checks before committing a
    # result. Replayed data, consent and annotations must be the same snapshot.
    current = admit(**inputs)
    if current != snapshot:
        raise EvaluationError("baseline_inputs_changed")
    recheck(snapshot, key=key)
    metrics = score(snapshot.gold, predictions)
    report = {"schema": "fdec-stock-baseline-report/v1", "actual_stock_model_executed": True,
              "created_at": datetime.now(timezone.utc).isoformat(), "model": model.identity,
              "prompt_sha256": PROMPT_SHA256, "inventory_sha256": splits.digest(snapshot.inventory),
              "consent_sha256": splits.digest(snapshot.consent), "split_receipt_sha256": splits.digest(snapshot.split["receipt"]),
              "annotations_sha256": snapshot.annotations_sha256, "review_sha256": snapshot.review_sha256,
              "implementation_sha256": implementation_hash(), "metrics": metrics,
              "scope": "reviewed-test-partition-only; no training or model-release approval"}
    publish(output, report, lambda: recheck(snapshot, key=key))
    return {"status": "measured", "rows": len(snapshot.gold), "invalid_outputs": metrics["overall"]["invalid_outputs"]}


def implementation_hash():
    paths = sorted(Path(__file__).parent.glob("*.py")) + [Path(__file__).with_name("qwen-stock-v1.json"), ROOT / "training/eval/baseline_metrics.py"]
    return hashlib.sha256(b"".join(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n") for path in paths)).hexdigest()


def publish(output, report, current_check):
    """Receipt is the commit marker; rollback removes only this owned directory."""
    output = private_output(output, ROOT)
    token = secrets.token_hex(32)
    owned = False
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir(mode=0o700)
        owned = True
        with (output / ".owner").open("x", encoding="ascii") as handle:
            handle.write(token)
        current_check()
        content = (splits.canonical_json(report) + "\n").encode()
        with (output / "metrics.json").open("xb") as handle:
            handle.write(content)
        current_check()
        receipt = dict(schema="fdec-baseline-receipt/v1", report_file="metrics.json", report_sha256=hashlib.sha256(content).hexdigest())
        with (output / "receipt.json").open("x", encoding="utf-8") as handle:
            handle.write(splits.canonical_json(receipt) + "\n")
    except Exception:
        if owned:
            remove_owned(output, token)
        raise EvaluationError("baseline_report_not_committed") from None


def preflight():
    """Availability only, deliberately not an admission or a model measurement."""
    return {"schema": "fdec-baseline-availability/v1", "status": "not_measured", "actual_stock_model_executed": False,
            "current_consent_present": (ROOT / "training/data/consent/current.json").is_file(),
            "current_label_review_present": (ROOT / REVIEW_ANCHOR).is_file(),
            "requires": ["audited-independent-source-runs", "current-signed-consent", "verified-grouped-test-partition", "independently-reviewed-non-openai-multilingual-gold", "verified-local-stock-model", "compatible-local-runtime"],
            "availability_is_admission": False}


def main(argv=None):
    parser = Parser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    commands.add_parser("preflight")
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--opt-in", action="store_true")
    for name in ("inventory", "consent", "split-dir", "annotations", "model-dir", "output-dir"):
        evaluate.add_argument("--" + name, required=True)
    evaluate.add_argument("--source-run", action="append", required=True)
    args = parser.parse_args(argv)
    try:
        result = preflight() if args.command == "preflight" else run(args)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception:
        # Do not include parser excerpts, model output, private paths or keys.
        print("baseline_evaluation_rejected", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
