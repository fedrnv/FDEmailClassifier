"""Explicit local augmentation CLI; no remote API or real email input."""

import sys
import augment
from ingest_dataset import PrivateArgumentParser


def main(argv=None):
    parser = PrivateArgumentParser(description="Rights-admitted synthetic template generation")
    for name in ("plan", "output-dir", "pack-id", "purpose"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--opt-in", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not args.opt_in:
            raise augment.AugmentationError("explicit_opt_in_required")
        # Rights admission precedes reading user-selected plan metadata.
        augment.load_pack(args.pack_id, args.purpose)
        result = augment.generate(augment.read_json(args.plan), output_dir=args.output_dir, pack_id=args.pack_id, purpose=args.purpose, opt_in=True)
        print(augment.canonical({"schema": result["schema"], "rows": result["rows"], "training_allowed": result["training_allowed"], "samples_sha256": result["files"]["samples.jsonl"]["sha256"]}))
        return 0
    except augment.AugmentationError as error:
        print("augmentation_error:" + str(error), file=sys.stderr)
        return 2
    except Exception:
        print("augmentation_error:failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
