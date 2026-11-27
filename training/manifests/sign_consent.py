"""Sign an explicitly drafted consent ledger, never infer or auto-create grants."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "splits"))
import split_data as s
from ingest_dataset import PrivateArgumentParser
from datetime import datetime, timezone


def main(argv=None):
    parser = PrivateArgumentParser(description="Authorized data-owner consent signing")
    for name in ("inventory", "payload", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args(argv)
    try:
        key = s.authority_key()
        inventory, payload = s.read_inventory(args.inventory), s.read_json(args.payload)
        s.validate_inventory(inventory)
        signed = s.envelope(payload, key)
        s.consent(inventory, signed, key, datetime.now(timezone.utc))
        output = s.private_output(args.output, s.ROOT)
        if output.resolve() == (s.ROOT / "training/data/consent/current.json").resolve():
            raise s.SplitError("consent_anchor_requires_activation")
        s._write(output, (s.canonical_json(signed) + "\n").encode("utf-8"))
        if args.activate:
            s.activate_consent(inventory, signed, key=key)
        print(s.canonical_json({"schema": signed["schema"], "snapshot_sha256": s.digest(signed)}))
        return 0
    except s.SplitError as error:
        print("consent_error:" + str(error), file=sys.stderr)
        return 2
    except Exception:
        print("consent_error:failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
