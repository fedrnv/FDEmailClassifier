"""Authenticate a real FDEC trainer checkpoint against current independently reviewed data."""
from pathlib import Path
from common import ROOT, ExportError
import split_data as splits
import training_inputs
import trainer_config
import train
import checkpoints
from local_model import verify_snapshot
from torch_engine import TARGET_MODULES


def inputs(args, key):
    return dict(inventory_path=args.inventory, consent_path=args.consent, split_dir=args.split_dir, annotations_path=args.annotations, prompt_path=args.prompt, source_runs=args.source_run, key=key)


def provenance(snapshot):
    return dict(inventory_sha256=splits.inventory_digest(snapshot.inventory), consent_sha256=splits.digest(snapshot.consent), split_receipt_sha256=splits.digest(snapshot.split["receipt"]),
                annotations_sha256=snapshot.annotations_sha256, prompt_sha256=snapshot.prompt_sha256, review_sha256=snapshot.review_sha256)


def checkpoint_context(args, key):
    try:
        snapshot = training_inputs.admit(**inputs(args, key))
        receipt = splits.read_json(Path(args.checkpoint) / "receipt.json", 1_000_000)
        context = receipt["payload"]["context"]
        fields = {"schema", "config", "model", "implementation_sha256", "inventory_sha256", "consent_sha256", "split_receipt_sha256", "annotations_sha256", "prompt_sha256", "review_sha256"}
        if set(context) != fields or context["schema"] != "fdec-peft-run-context/v1" or context["implementation_sha256"] != train.implementation_hash() or any(context[name] != value for name, value in provenance(snapshot).items()):
            raise ValueError()
        trainer_config.validate(context["config"])
        profile = verify_snapshot(args.model_dir)
        if context["model"]["model_id"] != profile["model_id"] or context["model"]["revision"] != profile["revision"] or context["model"]["targets"] != TARGET_MODULES or context["model"]["backend"] != context["config"]["backend"]:
            raise ValueError()
        # Verify the checkpoint envelope/bytes before allowing any Torch decoder.
        checkpoints.load(args.checkpoint, context=context, key=key, reader=lambda data: None, current_check=lambda: training_inputs.recheck(snapshot, key=key))
        return snapshot, context, profile
    except Exception:
        raise ExportError("trained_checkpoint_lineage_rejected") from None
