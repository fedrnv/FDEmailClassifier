"""Private split build/verify CLI; signing is a separate data-owner operation."""

import sys
import split_data as s
from ingest_dataset import PrivateArgumentParser


def main(argv=None):
    parser = PrivateArgumentParser(description="Consent-bound grouped training splits")
    parser.add_argument("action", choices=("build", "verify"))
    for name in ("inventory", "consent", "output-dir"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--opt-in", action="store_true")
    args = parser.parse_args(argv)
    try:
        key = s.authority_key()
        if args.action == "build" and not args.opt_in:
            raise s.SplitError("explicit_opt_in_required")
        inventory, consent = s.read_json(args.inventory), s.read_json(args.consent)
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
