"""Private, immutable model candidates. No upload or external publication."""
import hashlib
import hmac
import importlib.metadata
import json
from pathlib import Path
import re
import secrets
import sys

ROOT = Path(__file__).resolve().parents[2]
for area in ("training/scripts", "training/splits", "training/augmentation", "training/finetune", "training/baseline"):
    sys.path.append(str(ROOT / area))
from ingest_dataset import private_output, reject_links, remove_owned, strict_json
import split_data as splits

VARIANTS = ("peft-lora-f32", "gguf-base-f16", "gguf-lora-f16", "gguf-merged-f16")


class ExportError(ValueError):
    """Static diagnostics only."""


def digest_file(path, limit=8_000_000_000):
    path = reject_links(path)
    value, size = hashlib.sha256(), 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                raise ExportError("export_artifact_size_limit")
            value.update(chunk)
    return dict(sha256=value.hexdigest(), size=size)


def runtime():
    profile = splits.read_json(ROOT / "models/export-runtime-v1.json", 32768)
    if any(importlib.metadata.version(name) != version for name, version in profile["packages"].items()):
        raise ExportError("export_runtime_mismatch")
    return profile


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        out.write(splits.canonical_json(value) + "\n")


def candidate(directory, *, build, context, current_check, policy_root=ROOT, key=None):
    if key is not None and (not isinstance(key, bytes) or len(key) != 32):
        raise ExportError("export_authority_key_invalid")
    output = private_output(directory, policy_root)
    token, owned = secrets.token_hex(32), False
    try:
        current_check()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir(mode=0o700)
        owned = True
        with (output / ".owner").open("x", encoding="ascii") as out:
            out.write(token)
        build(output)
        files = []
        for path in sorted(output.rglob("*")):
            reject_links(path)
            if not path.is_file() or path.name == ".owner":
                continue
            relative = path.relative_to(output).as_posix()
            if any(word in relative for word in ("..", ":", "\\")) or path.suffix in (".pt", ".bin", ".pkl"):
                raise ExportError("unexpected_export_file")
            files.append(dict(path=relative, **digest_file(path)))
        manifest = dict(schema="fdec-model-candidate/v1", context=context, files=files, public_weight_redistribution_approved=False)
        manifest["hmac_sha256"] = None if key is None else hmac.new(key, b"fdec-model-candidate/v1\0" + splits.canonical_json(manifest).encode(), hashlib.sha256).hexdigest()
        current_check()
        write_json(output / "manifest.json", manifest)
        current_check()
        write_json(output / "receipt.json", dict(schema="fdec-model-candidate-receipt/v1", manifest_sha256=digest_file(output / "manifest.json")["sha256"]))
        return manifest
    except Exception:
        if owned:
            remove_owned(output, token)
        raise ExportError("model_candidate_not_committed") from None


def verify_candidate(directory, *, key=None):
    try:
        directory = reject_links(directory)
        receipt = splits.read_json(directory / "receipt.json", 4096)
        manifest = splits.read_json(directory / "manifest.json", 1_000_000)
        if set(receipt) != {"schema", "manifest_sha256"} or receipt["schema"] != "fdec-model-candidate-receipt/v1" or receipt["manifest_sha256"] != digest_file(directory / "manifest.json")["sha256"] or set(manifest) != {"schema", "context", "files", "public_weight_redistribution_approved", "hmac_sha256"} or manifest["schema"] != "fdec-model-candidate/v1" or manifest["public_weight_redistribution_approved"] is not False:
            raise ValueError()
        if key is not None:
            if not isinstance(key, bytes) or len(key) != 32: raise ValueError()
            payload = {name: value for name, value in manifest.items() if name != "hmac_sha256"}
            if not splits.is_hash(manifest["hmac_sha256"]) or not hmac.compare_digest(manifest["hmac_sha256"], hmac.new(key, b"fdec-model-candidate/v1\0" + splits.canonical_json(payload).encode(), hashlib.sha256).hexdigest()):
                raise ValueError()
        elif manifest["context"].get("kind") != "technical-container-fixture":
            raise ValueError()
        names = set()
        for binding in manifest["files"]:
            relative = binding["path"]
            if set(binding) != {"path", "sha256", "size"} or not isinstance(relative, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", relative) or relative.startswith("/") or ".." in relative or relative in names or relative in ("manifest.json", "receipt.json", ".owner"):
                raise ValueError()
            names.add(relative)
            if digest_file(directory / relative) != {name: binding[name] for name in ("sha256", "size")}:
                raise ValueError()
        actual = set()
        for path in directory.rglob("*"):
            reject_links(path)
            if path.is_file(): actual.add(path.relative_to(directory).as_posix())
        if actual != names | {"manifest.json", "receipt.json", ".owner"}:
            raise ValueError()
        return manifest
    except Exception:
        raise ExportError("model_candidate_integrity_rejected") from None
