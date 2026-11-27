"""Private empirical score calibration; separate immutable numerical acceptance."""
import hashlib
import hmac
import json
from pathlib import Path
import sys

from calibrate import ROOT, fit, evaluate, CalibrationError
from admit_scores import admit
import split_data as splits
sys.path.append(str(ROOT / "training/baseline"))
from baseline import publish, Parser

FIXTURE = Path(__file__).with_name("fixtures") / "heldout-v1.json"
FIXTURE_SHA256 = "523535d05151555b6342209b490a09d540e57b6dda056588ba193623de52f180"


def implementation_hash():
    paths = sorted(Path(__file__).parent.glob("*.py")) + [ROOT / "crates/core/src/schema/calibration.rs",
                                                               ROOT / "training/splits/disk_inventory.py", ROOT / "training/splits/source_replay.py"]
    return hashlib.sha256(b"".join(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n") for path in paths)).hexdigest()


def software_report():
    raw = FIXTURE.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise CalibrationError("frozen_calibration_fixture_changed")
    bundle = splits.strict_json(raw.decode())
    artifact = fit(bundle, min_class_support=2, min_tail_support=2)
    return dict(schema="fdec-calibration-run/v1", scope="software-numerical-fixture-only", actual_model_executed=False, actual_model_calibrated=False, probabilities_estimated=False,
                fixture_sha256=hashlib.sha256(raw).hexdigest(), implementation_sha256=implementation_hash(), artifact=artifact, holdout=evaluate(artifact, bundle), public_artifact_release_approved=False)


def main(argv=None):
    parser = Parser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    software = commands.add_parser("software-check")
    software.add_argument("--output-dir", required=True)
    actual = commands.add_parser("fit")
    actual.add_argument("--opt-in", action="store_true")
    for name in ("inventory", "consent", "split-dir", "observations", "output-dir"):
        actual.add_argument("--" + name, required=True)
    actual.add_argument("--source-run", action="append", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "software-check":
            report = software_report()
            publish(args.output_dir, report, lambda: None)
        else:
            if not args.opt_in:
                raise CalibrationError("explicit_opt_in_required")
            key = splits.authority_key()
            inputs = dict(inventory_path=args.inventory, consent_path=args.consent, split_dir=args.split_dir, observations_path=args.observations, source_runs=args.source_run, key=key)
            bundle, provenance = admit(**inputs)
            artifact = fit(bundle)  # Production support is 20 per class/tail.
            supported = sum(policy["status"] == "supported" for values in artifact["policies"].values() for policy in values.values())
            report = dict(schema="fdec-calibration-run/v1", scope="independently-reviewed-measured-margins", actual_model_executed=False, actual_model_calibrated=bool(supported), supported_policy_count=supported,
                          probabilities_estimated=False, artifact=artifact, holdout=evaluate(artifact, bundle), provenance=provenance,
                          implementation_sha256=implementation_hash(), public_artifact_release_approved=False)
            report["hmac_sha256"] = hmac.new(key, b"fdec-calibration-artifact/v1\0" + splits.canonical_json(report).encode(), hashlib.sha256).hexdigest()
            def current_check():
                if admit(**inputs) != (bundle, provenance):
                    raise CalibrationError("calibration_inputs_or_authority_changed")
            publish(args.output_dir, report, current_check)
        print(json.dumps(dict(scope=report["scope"], actual_model_executed=False, probabilities_estimated=False)))
        return 0
    except Exception:
        print("calibration_rejected", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
