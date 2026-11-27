"""Explicit local training, private immutable checkpoints and safe resumption."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys

from trainer_config import ROOT, TrainerError, read as read_config, record_index
from training_inputs import admit, recheck, REVIEW_ANCHOR
import split_data as splits
from ingest_dataset import private_output, reject_links, remove_owned
import checkpoints
from torch_engine import TorchEngine


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "trainer_arguments_invalid\n")


def implementation_hash():
    paths = sorted(Path(__file__).parent.glob("*.py")) + [ROOT / relative for relative in ("training/config/peft-runtime-v1.json", "training/baseline/local_model.py", "training/baseline/qwen-stock-v1.json", "training/eval/baseline_metrics.py", "training/augmentation/training_boundary.py", "training/splits/split_data.py", "training/splits/disk_inventory.py", "training/splits/source_replay.py", "training/scripts/ingest_dataset.py", "training/scripts/normalize_email.py", "training/labels/map_annotations.py", "training/datasets/get-inclusion.ps1", "training/datasets/assert-allowlist.ps1")]
    paths+=sorted((ROOT/'training/config').glob('mlx-*'))
    return hashlib.sha256(b"".join(path.relative_to(ROOT).as_posix().encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n") for path in paths)).hexdigest()


def run_context(config,engine,snapshot,engine_kind):
    return dict(schema='fdec-mlx-run-context/v1' if engine_kind=='mlx' else 'fdec-peft-run-context/v1',config=config,model=engine.identity,implementation_sha256=implementation_hash(),
                inventory_sha256=splits.inventory_digest(snapshot.inventory),consent_sha256=splits.digest(snapshot.consent),split_receipt_sha256=splits.digest(snapshot.split['receipt']),annotations_sha256=snapshot.annotations_sha256,prompt_sha256=snapshot.prompt_sha256,review_sha256=snapshot.review_sha256)


def run(args):
    if not args.opt_in:
        raise TrainerError("explicit_opt_in_required")
    config = read_config(args.config)
    stop = config["max_steps"] if args.stop_after is None else args.stop_after
    if type(stop) is not int or not 1 <= stop <= config["max_steps"]:
        raise TrainerError("invalid_stop_step")
    output = private_output(args.output_dir, ROOT)
    key = splits.authority_key()
    inputs = dict(inventory_path=args.inventory, consent_path=args.consent, split_dir=args.split_dir, annotations_path=args.annotations,
                  prompt_path=args.prompt, source_runs=args.source_run, key=key)
    snapshot = admit(**inputs)
    engine_kind=getattr(args,'engine','pytorch')
    if engine_kind=='pytorch':engine=TorchEngine(reject_links(args.model_dir),config)
    elif engine_kind=='mlx':
        if not getattr(args,'handoff_dir',None):raise TrainerError('mlx_handoff_required')
        from mlx_handoff import Handoff
        permitted=Handoff(args.handoff_dir)
        expected=dict(inventory=splits.inventory_digest(snapshot.inventory),consent=splits.digest(snapshot.consent),split=splits.digest(snapshot.split['receipt']),annotations=snapshot.annotations_sha256,prompt=snapshot.prompt_sha256,review=snapshot.review_sha256)
        if permitted.manifest['input_manifest_hashes']!=expected:raise TrainerError('mlx_handoff_training_inputs_changed')
        from mlx_engine import MLXEngine
        engine=MLXEngine(reject_links(args.model_dir),config,args.handoff_dir)
    else:raise TrainerError('training_engine_unsupported')
    def current_check():
        recheck(snapshot,key=key)
        if engine_kind=='mlx':engine.handoff.authorize('actual-training',source=False)
    current_check()
    context=run_context(config,engine,snapshot,engine_kind)
    step = 0
    if args.resume:
        step, state = checkpoints.load(args.resume, context=context, key=key, reader=engine.read, current_check=current_check)
        engine.restore(state)
        if engine_kind=='mlx':engine.validate_cursor(step)
    if step >= stop:
        raise TrainerError("resume_has_no_remaining_requested_steps")
    # Prepare every sequence before mutating state. No silent truncation or
    # dropped record is permitted in a fixed dataset run.
    batches = [engine.tokenize(snapshot.system, *snapshot.texts[row["record_id"]], row["classification"]) for row in snapshot.rows]
    token, owned, committed = secrets.token_hex(32), False, False
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir(mode=0o700)
        owned = True
        with (output / ".owner").open("x", encoding="ascii") as handle:
            handle.write(token)
        if engine_kind=='mlx':
            import private_paths
            private_paths.verify(output,owner_token=token)
        while step < stop:
            current_check()
            microstep = step * config["gradient_accumulation"]
            selected = [batches[record_index(config["seed"], microstep + offset, len(batches))] for offset in range(config["gradient_accumulation"])]
            engine.update(selected, current_check)
            step += 1
            if step % config["checkpoint_interval"] == 0 or step == stop:
                if admit(**inputs) != snapshot:
                    raise TrainerError("training_inputs_changed")
                current_check()
                checkpoints.save(output / f"step-{step:09d}", state=engine.state(), context=context, step=step, key=key, writer=engine.write, current_check=current_check)
                committed = True
        current_check()
        summary = dict(schema="fdec-private-training-result/v1", context_sha256=splits.digest(context), steps=step, complete=step == config["max_steps"], actual_email_training=True,
                       checkpoint=f"step-{step:09d}", public_artifact_release_approved=False)
        pending = output / ".result.part"
        with pending.open("x", encoding="utf-8") as handle:
            handle.write(splits.canonical_json(summary) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        current_check()
        if (output / "result.json").exists():
            raise TrainerError("training_result_already_exists")
        os.replace(pending, output / "result.json")
        return {"status": "completed" if summary["complete"] else "checkpointed", "steps": step}
    except Exception:
        # Keep valid, committed checkpoints for recovery after a later failure.
        # A run with no committed checkpoint is safe to remove by ownership.
        if owned and not committed:
            remove_owned(output, token)
        elif owned and (output / ".owner").read_text(encoding="ascii") == token:
            pending = reject_links(output / ".result.part")
            if pending.is_file():
                pending.unlink()
        raise TrainerError("training_run_incomplete") from None


def main(argv=None):
    parser = Parser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    commands.add_parser("preflight")
    cpu_check = commands.add_parser("cpu-check")
    cpu_check.add_argument("--opt-in", action="store_true")
    check = commands.add_parser("gpu-check")
    check.add_argument("--opt-in", action="store_true")
    check.add_argument("--backend", choices=("lora", "qlora", "both"), default="both")
    mlx_check=commands.add_parser('mlx-check')
    mlx_check.add_argument('--opt-in',action='store_true')
    mlx_check.add_argument('--handoff-dir',required=True)
    mlx_check.add_argument('--output-dir',required=True)
    for command_name in ('mlx-evaluate','mlx-collect'):
        command=commands.add_parser(command_name)
        command.add_argument('--opt-in',action='store_true')
        for name in ('handoff-dir','checkpoint','config','inventory','consent','split-dir','training-annotations','training-prompt','annotations','model-dir','output-dir'):command.add_argument('--'+name,required=True)
        command.add_argument('--source-run',action='append',required=True)
        if command_name=='mlx-collect':command.add_argument('--evaluation-dir',required=True)
    training = commands.add_parser("train")
    training.add_argument("--opt-in", action="store_true")
    training.add_argument('--engine',choices=('pytorch','mlx'),default='pytorch')
    training.add_argument('--handoff-dir')
    for name in ("config", "inventory", "consent", "split-dir", "annotations", "prompt", "model-dir", "output-dir"):
        training.add_argument("--" + name, required=True)
    training.add_argument("--source-run", action="append", required=True)
    training.add_argument("--resume")
    training.add_argument("--stop-after", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            result = dict(schema="fdec-trainer-availability/v1", actual_training=False, current_training_review_present=(ROOT / REVIEW_ANCHOR).is_file(),
                          requires=["reviewed-non-openai-training-data-labels-prompt", "current-rights-and-consent", "verified-train-partition", "verified-stock-snapshot", "compatible-single-bfloat16-CUDA-device"], availability_is_admission=False)
        elif args.command=='mlx-evaluate':
            from mlx_evaluate import run as mlx_evaluate
            result=mlx_evaluate(args)
        elif args.command=='mlx-collect':
            from mlx_return_training import collect
            result=collect(args)
        elif args.command=='mlx-check':
            from mlx_smoke import run as mlx_smoke
            result=mlx_smoke(opt_in=args.opt_in,handoff_dir=args.handoff_dir,output_dir=args.output_dir)
        elif args.command == "cpu-check":
            from gpu_check import run_cpu
            result = run_cpu(opt_in=args.opt_in)
        elif args.command == "gpu-check":
            from gpu_check import run as gpu_check
            result = gpu_check(opt_in=args.opt_in, backend=args.backend)
        else:
            result = run(args)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as error:
        if args.command.startswith('mlx-') or getattr(args,'engine','pytorch')=='mlx':
            from mlx_handoff import diagnostic
            message=diagnostic(error)
        else:message='trainer_execution_rejected'
        print(message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
