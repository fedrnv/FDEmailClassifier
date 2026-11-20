"""Lazy offline PyTorch/PEFT engine; actual CUDA integration must be measured."""
import hashlib
import importlib.metadata
import io
import os
import platform
from pathlib import Path
import random
import re
import subprocess
import sys

from trainer_config import ROOT, TrainerError
sys.path.append(str(ROOT / "training/baseline"))
sys.path.append(str(ROOT / "training/splits"))
from local_model import verify_snapshot, quiet_runtime
import split_data as splits

TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def deterministic_runtime(config):
    # Must be set before creating a CUDA context. Never silently override an
    # incompatible already configured process.
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG", ":4096:8") != ":4096:8":
        raise TrainerError("incompatible_cublas_determinism")
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    profile = splits.read_json(ROOT / "training/config/peft-runtime-v1.json", 16384)
    required = profile["packages"].copy()
    if config["backend"] != "qlora":
        required.pop("bitsandbytes")
    if any(importlib.metadata.version(name) != version for name, version in required.items()):
        raise TrainerError("incompatible_training_runtime")
    import torch
    import numpy as np
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
        raise TrainerError("single_bfloat16_cuda_device_required")
    torch.set_num_threads(1)
    random.seed(config["seed"])
    np.random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    torch.cuda.manual_seed_all(config["seed"])
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    return torch


class TorchEngine:
    def __init__(self, model_dir, config):
        try:
            with quiet_runtime():
                self.config = config
                self.profile = verify_snapshot(model_dir)
                self.torch = deterministic_runtime(config)
                from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
                from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
                kwargs = dict(local_files_only=True, trust_remote_code=False, use_safetensors=True,
                              dtype=self.torch.bfloat16, attn_implementation="eager", device_map={"": "cuda:0"})
                if config["backend"] == "qlora":
                    kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=self.torch.bfloat16)
                self.model = AutoModelForCausalLM.from_pretrained(str(model_dir), **kwargs)
                self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False)
                if self.model.config.model_type != "qwen3" or self.model.config.attention_dropout != 0:
                    raise ValueError()
                self.model.config.use_cache = False
                if config["backend"] == "qlora":
                    self.model = prepare_model_for_kbit_training(self.model, use_gradient_checkpointing=False)
                self.model = get_peft_model(self.model, LoraConfig(task_type="CAUSAL_LM", r=config["rank"], lora_alpha=config["alpha"], lora_dropout=0.0, bias="none", target_modules=TARGET_MODULES))
                self.setup_optimizer()
                verify_snapshot(model_dir)
                properties = self.torch.cuda.get_device_properties(0)
                driver = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], capture_output=True, text=True, timeout=10, check=True).stdout.strip()
                if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", driver):
                    raise ValueError()
                self.identity = dict(model_id=self.profile["model_id"], revision=self.profile["revision"], backend=config["backend"], cuda=self.torch.version.cuda,
                                     device=properties.name, capability=[properties.major, properties.minor], cudnn=self.torch.backends.cudnn.version(),
                                     driver=driver, python=platform.python_version(), platform=platform.platform(),
                                     environment_sha256=splits.digest(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions())),
                                     runtime_profile_sha256=hashlib.sha256((ROOT / "training/config/peft-runtime-v1.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
                                     targets=TARGET_MODULES, dtype="bfloat16-base/float32-adapter", optimizer="AdamW/foreach=false/fused=false", batch_size=1)
        except Exception:
            raise TrainerError("training_runtime_initialization_failed") from None

    def setup_optimizer(self):
        self.parameters = {name: parameter for name, parameter in self.model.named_parameters() if parameter.requires_grad}
        if not self.parameters or any("lora_" not in name for name in self.parameters):
            raise TrainerError("unexpected_trainable_parameters")
        # PEFT adapters are explicitly float32; frozen base precision is separate.
        for parameter in self.parameters.values():
            parameter.data = parameter.data.float()
        self.optimizer = self.torch.optim.AdamW(list(self.parameters.values()), lr=self.config["learning_rate"], weight_decay=self.config["weight_decay"], foreach=False, fused=False)
        self.optimizer.zero_grad(set_to_none=True)
        self.model.train()

    def tokenize(self, system, subject, body, classification):
        with quiet_runtime():
            try:
                messages = [{"role": "system", "content": system}, {"role": "user", "content": splits.canonical_json(dict(subject=subject, body=body))}]
                prefix = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, enable_thinking=False)
                target = self.tokenizer.encode(splits.canonical_json(classification), add_special_tokens=False)
                eos = self.tokenizer.eos_token_id
                if not isinstance(prefix, list) or not prefix or not target or type(eos) is not int or len(prefix) + len(target) + 1 > self.config["max_sequence_tokens"]:
                    raise ValueError()
                return prefix + target + [eos], [-100] * len(prefix) + target + [eos]
            except Exception:
                raise TrainerError("training_sequence_invalid_or_over_budget") from None

    def update(self, batches, current_check):
        with quiet_runtime():
            try:
                if len(batches) != self.config["gradient_accumulation"]:
                    raise ValueError()
                for input_ids, labels in batches:
                    current_check()
                    data = self.torch.tensor([input_ids], dtype=self.torch.long, device="cuda:0")
                    targets = self.torch.tensor([labels], dtype=self.torch.long, device="cuda:0")
                    loss = self.model(input_ids=data, attention_mask=self.torch.ones_like(data), labels=targets, use_cache=False).loss
                    if not self.torch.isfinite(loss).item():
                        raise ValueError()
                    (loss / len(batches)).backward()
                norm = self.torch.nn.utils.clip_grad_norm_(list(self.parameters.values()), self.config["max_grad_norm"], error_if_nonfinite=True)
                if not self.torch.isfinite(norm).item():
                    raise ValueError()
                current_check()
                self.optimizer.step()
                self.optimizer.zero_grad(set_to_none=True)
                self.torch.cuda.synchronize()
            except Exception:
                raise TrainerError("training_step_rejected") from None

    def state(self):
        return dict(schema="fdec-torch-peft-state/v1", adapter={name: value.detach().cpu().clone() for name, value in self.parameters.items()},
                    parameter_order=list(self.parameters), optimizer=self.optimizer.state_dict(), rng_cpu=self.torch.get_rng_state(), rng_cuda=self.torch.cuda.get_rng_state_all())

    def restore(self, state):
        try:
            if not isinstance(state, dict) or set(state) != {"schema", "adapter", "parameter_order", "optimizer", "rng_cpu", "rng_cuda"} or state["schema"] != "fdec-torch-peft-state/v1" or state["parameter_order"] != list(self.parameters) or set(state["adapter"]) != set(self.parameters):
                raise ValueError()
            for name, parameter in self.parameters.items():
                value = state["adapter"][name]
                if value.shape != parameter.shape or value.dtype != parameter.dtype or not self.torch.isfinite(value).all().item():
                    raise ValueError()
            with self.torch.no_grad():
                for name, parameter in self.parameters.items():
                    parameter.copy_(state["adapter"][name].to(parameter.device))
            self.optimizer.load_state_dict(state["optimizer"])
            self.optimizer.zero_grad(set_to_none=True)
            self.torch.set_rng_state(state["rng_cpu"])
            self.torch.cuda.set_rng_state_all(state["rng_cuda"])
        except Exception:
            raise TrainerError("incompatible_training_state") from None

    def write(self, state, path):
        self.torch.save(state, path)

    def read(self, content):
        # The checkpoint layer first checks the HMAC and frozen byte digest.
        # No pickle globals are added and no unrestricted load path is exposed.
        return self.torch.load(io.BytesIO(content), map_location="cpu", weights_only=True)
