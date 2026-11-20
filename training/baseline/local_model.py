"""Explicit local stock snapshot only. No download, remote code or fine tuning."""
import hashlib
import importlib.metadata
import json
import logging
import os
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "training/scripts"))
from ingest_dataset import reject_links, strict_json
from prompt import MAX_INPUT_TOKENS, MAX_NEW_TOKENS
from baseline_metrics import EvaluationError

PROFILE = Path(__file__).with_name("qwen-stock-v1.json")


@contextmanager
def quiet_runtime():
    """Do not relay third-party diagnostics that could quote private input."""
    previous = logging.root.manager.disable
    with open(os.devnull, "w", encoding="utf-8") as sink, redirect_stdout(sink), redirect_stderr(sink):
        logging.disable(logging.CRITICAL)
        try:
            yield
        finally:
            logging.disable(previous)


def verify_snapshot(directory):
    try:
        profile = strict_json(PROFILE.read_text(encoding="utf-8"))
        directory = reject_links(directory).resolve()
        allowed = {row["path"] for row in profile["files"]}
        if not directory.is_dir() or {path.name for path in directory.iterdir()} != allowed:
            raise ValueError()
        for item in profile["files"]:
            path = reject_links(directory / item["path"])
            if not path.is_file() or path.stat().st_size != item["size"]:
                raise ValueError()
            digest = hashlib.sha256() if item["algorithm"] == "sha256" else hashlib.sha1(f'blob {item["size"]}\0'.encode())
            with path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
            if digest.hexdigest() != item["digest"]:
                raise ValueError()
        return profile
    except Exception:
        raise EvaluationError("stock_model_snapshot_not_verified") from None


class LocalQwen:
    def __init__(self, directory):
        with quiet_runtime():
            self._load(directory)

    def _load(self, directory):
        profile = verify_snapshot(directory)
        try:
            for package, version in profile["runtime"].items():
                if importlib.metadata.version(package) != version:
                    raise ValueError()
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            torch.set_num_threads(1)
            torch.manual_seed(0)
            torch.use_deterministic_algorithms(True)
            self.torch = torch
            self.tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False)
            self.model = AutoModelForCausalLM.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False, use_safetensors=True, dtype=torch.float32).to("cpu").eval()
            if self.model.config.model_type != "qwen3":
                raise ValueError()
            # Verify again after loading, before any private input reaches it.
            verify_snapshot(directory)
            self.identity = {"model_id": profile["model_id"], "revision": profile["revision"], "profile_sha256": hashlib.sha256(PROFILE.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                             "runtime": profile["runtime"], "environment_sha256": hashlib.sha256(json.dumps(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions()), separators=(",", ":")).encode()).hexdigest(),
                             "device": "cpu", "dtype": "float32", "seed": 0, "threads": 1, "do_sample": False, "enable_thinking": False,
                             "max_input_tokens": MAX_INPUT_TOKENS, "max_new_tokens": MAX_NEW_TOKENS}
        except Exception:
            raise EvaluationError("stock_runtime_unavailable_or_incompatible") from None

    def infer(self, messages):
        with quiet_runtime():
            return self._infer(messages)

    def _infer(self, messages):
        try:
            rendered = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
            tokens = self.tokenizer([rendered], return_tensors="pt", truncation=False)
            length = tokens["input_ids"].shape[1]
            if length > MAX_INPUT_TOKENS:
                raise EvaluationError("input_token_budget_exceeded")
            with self.torch.inference_mode():
                generated = self.model.generate(**tokens, do_sample=False, max_new_tokens=MAX_NEW_TOKENS)
            suffix = generated[0][length:]
            # A truncated object never becomes an apparently complete answer.
            if not len(suffix) or int(suffix[-1]) not in ([self.model.generation_config.eos_token_id] if isinstance(self.model.generation_config.eos_token_id, int) else self.model.generation_config.eos_token_id or []):
                raise EvaluationError("incomplete_model_generation")
            return self.tokenizer.decode(suffix, skip_special_tokens=True)
        except EvaluationError:
            raise
        except Exception:
            raise EvaluationError("stock_inference_failed") from None
