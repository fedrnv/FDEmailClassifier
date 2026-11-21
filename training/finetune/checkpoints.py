"""Authenticated private checkpoints, immutable directories and receipt-last commit."""
import hashlib
import hmac
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/splits"))
import split_data as splits
from ingest_dataset import private_output, reject_links, remove_owned
from trainer_config import TrainerError

DOMAIN = b"fdec-private-peft-checkpoint/v1\0"
MLX_DOMAIN = b"fdec-private-mlx-checkpoint/v1\0"
MAX_STATE_BYTES = 512_000_000


def state_format(context):
    if context.get('schema') in ('fdec-mlx-run-context/v1','fdec-mlx-smoke-context/v1'):
        return 'state.safetensors','fdec-mlx-checkpoint/v1'
    return 'state.pt','fdec-peft-checkpoint/v1'


def file_hash(path):
    digest, size = hashlib.sha256(), 0
    path = reject_links(path)
    if not path.is_file() or path.stat().st_size > MAX_STATE_BYTES:
        raise TrainerError("invalid_checkpoint_size")
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_STATE_BYTES:
                raise TrainerError("invalid_checkpoint_size")
            digest.update(chunk)
    return digest.hexdigest(), size


def signature(payload, key):
    if not isinstance(key, bytes) or len(key) != 32:
        raise TrainerError("checkpoint_authority_missing")
    domain=MLX_DOMAIN if payload.get('schema')=='fdec-mlx-checkpoint/v1' else DOMAIN
    return hmac.new(key, domain + splits.canonical_json(payload).encode(), hashlib.sha256).hexdigest()


def save(directory, *, state, context, step, key, writer, current_check, policy_root=ROOT):
    """writer serializes numerical state only. Production uses torch.save.

    Library codec injection supports technical unit tests; the production CLI
    offers no alternate codec, key, policy root or trust override.
    """
    output = private_output(directory, policy_root)
    if type(step) is not int or not 0 <= step <= context["config"]["max_steps"]:
        raise TrainerError("invalid_checkpoint_step")
    token, owned = secrets.token_hex(32), False
    state_name,schema=state_format(context)
    try:
        current_check()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir(mode=0o700)
        owned = True
        with (output / ".owner").open("x", encoding="ascii") as handle:
            handle.write(token)
        if schema=='fdec-mlx-checkpoint/v1':
            import private_paths
            private_paths.verify(output,owner_token=token)
        writer(state, output / state_name)
        state_sha256, state_bytes = file_hash(output / state_name)
        metadata = {"schema": schema, "context": context, "step": step, "state_sha256": state_sha256, "state_bytes": state_bytes}
        with (output / "metadata.json").open("x", encoding="utf-8") as handle:
            handle.write(splits.canonical_json(metadata) + "\n")
        current_check()
        receipt = dict(schema="fdec-signed-peft-checkpoint/v1", payload=metadata, hmac_sha256=signature(metadata, key))
        with (output / "receipt.json").open("x", encoding="utf-8") as handle:
            handle.write(splits.canonical_json(receipt) + "\n")
        return receipt
    except Exception:
        if owned:
            remove_owned(output, token)
        raise TrainerError("checkpoint_not_committed") from None


def load(directory, *, context, key, reader, current_check):
    """Authenticate every byte and context before invoking the numerical decoder."""
    try:
        state_name,schema=state_format(context)
        current_check()
        directory = reject_links(directory)
        if {path.name for path in directory.iterdir()} != {".owner", state_name, "metadata.json", "receipt.json"}:
            raise ValueError()
        for path in directory.iterdir():
            reject_links(path)
        receipt = splits.read_json(directory / "receipt.json", 1_000_000)
        metadata = splits.read_json(directory / "metadata.json", 1_000_000)
        if not isinstance(receipt, dict) or set(receipt) != {"schema", "payload", "hmac_sha256"} or receipt["schema"] != "fdec-signed-peft-checkpoint/v1" or receipt["payload"] != metadata or not splits.is_hash(receipt["hmac_sha256"]) or not hmac.compare_digest(receipt["hmac_sha256"], signature(metadata, key)):
            raise ValueError()
        if not isinstance(metadata, dict) or set(metadata) != {"schema", "context", "step", "state_sha256", "state_bytes"} or metadata["schema"] != schema or metadata["context"] != context or type(metadata["step"]) is not int or not 0 <= metadata["step"] <= context["config"]["max_steps"]:
            raise ValueError()
        if file_hash(directory / state_name) != (metadata["state_sha256"], metadata["state_bytes"]):
            raise ValueError()
        # Freeze authenticated bytes for the decoder, preventing file swapping
        # after the integrity check. The already bounded file is private state.
        content = splits.read_bytes(directory / state_name, MAX_STATE_BYTES)
        if (hashlib.sha256(content).hexdigest(), len(content)) != (metadata["state_sha256"], metadata["state_bytes"]):
            raise ValueError()
        current_check()
        state = reader(content)
        current_check()
        return metadata["step"], state
    except Exception:
        raise TrainerError("checkpoint_resume_rejected") from None
