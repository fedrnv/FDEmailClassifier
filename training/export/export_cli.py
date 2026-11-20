"""Private export/verification only. No uploader or publication command exists."""
import json
from pathlib import Path
import sys

from common import ROOT, candidate, verify_candidate, write_json, ExportError
import split_data as splits
from formats import numerical_round_trip
from exporter import run, sbom
from lineage import inputs, provenance
import training_inputs
from baseline import Parser
import release_gate


def main(argv=None):
    parser = Parser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    software = commands.add_parser("software-check")
    software.add_argument("--output-dir", required=True)
    model_check = commands.add_parser("software-model-check")
    model_check.add_argument("--output-dir", required=True)
    model_check.add_argument("--llama-cpp-dir", required=True)
    model_check.add_argument("--reuse-observed-build", action="store_true")
    verify = commands.add_parser("verify")
    verify.add_argument("--candidate-dir", required=True)
    export = commands.add_parser("export")
    export.add_argument("--opt-in", action="store_true")
    export.add_argument("--checkpoint", required=True)
    export.add_argument("--model-dir", required=True)
    export.add_argument("--llama-cpp-dir", required=True)
    export.add_argument("--output-dir", required=True)
    release = commands.add_parser("release-gate")
    release.add_argument("--candidate-dir", required=True)
    for command in (export, release):
        for name in ("inventory", "consent", "split-dir", "annotations", "prompt"):
            command.add_argument("--" + name, required=True)
        command.add_argument("--source-run", action="append", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "software-check":
            report = {}
            def build(directory):
                report.update(numerical_round_trip(directory))
                write_json(directory / "verification.json", report)
                write_json(directory / "sbom.cdx.json", sbom(directory))
            candidate(args.output_dir, build=build, context=dict(kind="technical-container-fixture", actual_trained_model_used=False, model_runtime_load_verified=False), current_check=lambda: None)
            print(json.dumps(dict(scope="technical-container-fixture-only", actual_trained_model_used=False, model_inference_roundtrip_verified=False, format_roundtrips=report)))
        elif args.command == "software-model-check":
            from tiny_model_check import run as check_model
            from local_model import quiet_runtime
            with quiet_runtime():
                report = check_model(args.output_dir, args.llama_cpp_dir, reuse_observed_build=args.reuse_observed_build)
            print(json.dumps(dict(scope="technical-random-model-only",actual_trained_model_used=False,actual_model_training=False,model_inference_roundtrip_verified=report["model_inference_roundtrip_verified"])))
        elif args.command == "verify":
            # No unsigned real model candidate can pass; fixture verification
            # does not grant any real training/model redistribution permission.
            key = None
            if splits.read_json(Path(args.candidate_dir) / "manifest.json", 1_000_000)["context"].get("kind") != "technical-container-fixture":
                key = splits.authority_key()
            verify_candidate(args.candidate_dir, key=key)
            print(json.dumps(dict(integrity_verified=True, public_weight_redistribution_approved=False)))
        elif args.command == "export":
            run(args)
            print(json.dumps(dict(private_candidate_created=True, public_weight_redistribution_approved=False, numerical_runtime_probe_verified=True)))
        else:
            key = splits.authority_key()
            def current_check(expected):
                if provenance(training_inputs.admit(**inputs(args, key))) != expected:
                    raise ExportError("release_training_authority_changed")
            print(json.dumps(release_gate.check(args.candidate_dir, key=key, current_check=current_check)))
        return 0
    except Exception:
        print("model_export_rejected", file=sys.stderr)
        return 2


if __name__ == "__main__": raise SystemExit(main())
