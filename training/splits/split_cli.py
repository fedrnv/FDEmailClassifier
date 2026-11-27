"""Private split build/verify CLI; signing is a separate data-owner operation."""

import sys
import split_data as s
from disk_inventory import MAX_METADATA_LINE, pack, private_file
from ingest_dataset import PrivateArgumentParser


def projected_rows(path):
    with private_file(path) as stream:
        while raw := stream.readline(MAX_METADATA_LINE + 1):
            if len(raw) > MAX_METADATA_LINE or not raw.endswith(b"\n"):
                raise s.SplitError("invalid_disk_inventory_record_line")
            yield s.strict_json(raw.decode("utf-8"))


def main(argv=None):
    parser = PrivateArgumentParser(description="Consent-bound grouped training splits")
    parser.add_argument("action", choices=("pack", "build", "verify"))
    for name in ("inventory", "output-dir"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--consent")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--opt-in", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "pack":
            if args.consent is not None:
                raise s.SplitError("packing_does_not_accept_consent")
            report = pack(projected_rows(args.inventory), output_dir=args.output_dir, opt_in=args.opt_in)
            print(s.canonical_json({"schema": report["schema"], "rows": report["rows"],
                                    "fingerprints": report["fingerprints"], "inventory_sha256": s.digest(report)}))
            return 0
        if args.consent is None:
            raise s.SplitError("consent_input_required")
        key = s.authority_key()
        if args.action == "build" and not args.opt_in:
            raise s.SplitError("explicit_opt_in_required")
        inventory, consent = s.read_inventory(args.inventory), s.read_json(args.consent)
        if args.action == "build":
            result = s.build(inventory, consent, output_dir=args.output_dir, key=key, seed=args.seed, opt_in=True)
        else:
            result = s.verify(args.output_dir, inventory, consent, key=key)
        print(s.canonical_json(result))
        return 0
    except s.SplitError as error:
        print("split_error:" + str(error), file=sys.stderr)
        return 2
    except Exception:
        print("split_error:failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
