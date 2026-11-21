"""Actual CUDA contract check on random numerical tokens, never email fixtures.

This check is distinct from actual stock/email training. No natural-language
training texts, category labels, pretrained tensors or fixture packs are used.
Its tiny randomly initialized Qwen3 architecture and tensors are disposable.
"""
from pathlib import Path
import secrets
import tempfile

from trainer_config import ROOT, TrainerError, read as read_config
from torch_engine import TorchEngine, TARGET_MODULES, deterministic_runtime, quiet_runtime
import checkpoints
from normalize_email import IngestionError


def run(*, opt_in=False, backend="both"):
    if opt_in is not True:
        raise TrainerError("explicit_opt_in_required")
    if backend not in ("lora", "qlora", "both"):
        raise TrainerError("invalid_gpu_check_backend")
    choices = ("lora", "qlora") if backend == "both" else (backend,)
    checks = {name: check_backend(name) for name in choices}
    return dict(schema="fdec-numeric-gpu-check/v1", result="PASS", checks=checks, actual_email_training=False, stock_model_used=False, fixture_emails_used=False)


def run_cpu(*, opt_in=False):
    if opt_in is not True: raise TrainerError("explicit_opt_in_required")
    return dict(schema="fdec-numeric-cpu-check/v1", result="PASS", checks={"lora":check_backend("lora",technical_cpu=True)},
                supported_gpu_acceptance=False,actual_email_training=False,stock_model_used=False,fixture_emails_used=False)


def check_backend(backend, *, technical_cpu=False):
    with quiet_runtime():
        config = read_config(ROOT / "training/config/peft-trainer-v1.json").copy()
        config.update(backend=backend, max_steps=4, gradient_accumulation=1, rank=2, alpha=4, max_sequence_tokens=128, checkpoint_interval=2)
        torch = deterministic_runtime(config,technical_cpu=technical_cpu)
        from transformers import Qwen3Config, Qwen3ForCausalLM, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        def fresh():
            deterministic_runtime(config,technical_cpu=technical_cpu)
            engine = TorchEngine.__new__(TorchEngine)
            engine.config, engine.torch = config, torch
            if backend == "lora":
                model = tiny_model().to(device="cpu" if technical_cpu else "cuda:0", dtype=torch.float32 if technical_cpu else torch.bfloat16)
            else:
                model = AutoModelForCausalLM.from_pretrained(str(base_path), local_files_only=True, trust_remote_code=False, use_safetensors=True, attn_implementation="eager", dtype=torch.bfloat16, device_map={"": "cuda:0"}, quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16))
                model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)
            engine.model = get_peft_model(model, LoraConfig(task_type="CAUSAL_LM", r=2, lora_alpha=4, lora_dropout=0.0, bias="none", target_modules=TARGET_MODULES))
            engine.model.config.use_cache = False
            engine.setup_optimizer()
            return engine
        def tiny_model():
            return Qwen3ForCausalLM(Qwen3Config(vocab_size=128, hidden_size=32, intermediate_size=64, num_hidden_layers=1, num_attention_heads=4, num_key_value_heads=2, head_dim=8, max_position_embeddings=128, attention_dropout=0.0, pad_token_id=0, bos_token_id=1, eos_token_id=2, attn_implementation="eager"))
        with tempfile.TemporaryDirectory(prefix="fdec-numeric-gpu-check-") as name:
            path = Path(name).resolve()
            if not path.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not path.name.startswith("fdec-numeric-gpu-check-") or path.is_symlink() or path.is_junction():
                raise TrainerError("unsafe_gpu_fixture_directory")
            base_path = path / "random-base"
            if backend == "qlora":
                tiny_model().save_pretrained(str(base_path), safe_serialization=True)
            generator = torch.Generator(device="cpu").manual_seed(104729)
            numerical = torch.randint(3, 128, (32,), generator=generator).tolist()
            batch = [(numerical, numerical)]
            whole = fresh()
            initial = {name:value.detach().cpu().clone() for name,value in whole.parameters.items()}
            frozen = {name:value.detach().cpu().clone() for name,value in whole.model.named_parameters() if not value.requires_grad}
            for _ in range(4):
                whole.update(batch, lambda: None)
            expected = whole.state()
            if not any(not torch.equal(initial[name],value) for name,value in expected["adapter"].items()):
                raise TrainerError("numeric_fixture_adapter_not_updated")
            if any(not torch.equal(value.detach().cpu(),frozen[name]) for name,value in whole.model.named_parameters() if not value.requires_grad):
                raise TrainerError("numeric_fixture_frozen_base_changed")
            interrupted = fresh()
            for _ in range(2):
                interrupted.update(batch, lambda: None)
            context, key = dict(kind="technical-random-numeric-cpu-check" if technical_cpu else "technical-random-numeric-gpu-check", config=config), secrets.token_bytes(32)
            checkpoints.save(path / "checkpoint", state=interrupted.state(), context=context, step=2, key=key, writer=interrupted.write, current_check=lambda: None)
            resumed = fresh()
            step, state = checkpoints.load(path / "checkpoint", context=context, key=key, reader=resumed.read, current_check=lambda: None)
            if step != 2:
                raise TrainerError("gpu_resume_cursor_mismatch")
            resumed.restore(state)
            for _ in range(2):
                resumed.update(batch, lambda: None)
            def same(left, right):
                if isinstance(left, torch.Tensor):
                    return isinstance(right, torch.Tensor) and left.dtype == right.dtype and torch.equal(left.cpu(), right.cpu())
                if isinstance(left, dict):
                    return isinstance(right, dict) and left.keys() == right.keys() and all(same(left[key], right[key]) for key in left)
                if isinstance(left, (tuple, list)):
                    return type(left) is type(right) and len(left) == len(right) and all(same(a, b) for a, b in zip(left, right))
                return left == right
            if not same(expected, resumed.state()):
                raise TrainerError("gpu_resume_is_not_exact")
            checkpoint=path/"checkpoint"
            original={name:(checkpoint/name).read_bytes() for name in ("state.pt","metadata.json","receipt.json")}
            try:checkpoints.save(checkpoint,state=resumed.state(),context=context,step=4,key=key,writer=resumed.write,current_check=lambda:None)
            except (TrainerError,IngestionError):pass
            else:raise TrainerError("existing_numeric_checkpoint_overwritten")
            if any((checkpoint/name).read_bytes()!=content for name,content in original.items()):raise TrainerError("existing_numeric_checkpoint_changed")
            # Authenticated native torch serialization is corrupted only after
            # successful replay and preservation checks. Decoder must not run.
            (checkpoint/"state.pt").write_bytes(original["state.pt"]+b"corrupt-numerical-fixture")
            decoded=[]
            def forbidden_reader(content):
                decoded.append(True)
                return resumed.read(content)
            try:checkpoints.load(checkpoint,context=context,key=key,reader=forbidden_reader,current_check=lambda:None)
            except TrainerError:pass
            else:raise TrainerError("tampered_numeric_checkpoint_loaded")
            if decoded:raise TrainerError("tampered_numeric_checkpoint_decoded")
        return dict(backend=backend, device="cpu" if technical_cpu else "cuda:0", steps=4, checkpoint_resume_exact=True,adapter_updated=True,frozen_base_unchanged=True,optimizer_and_rng_exact=True,existing_checkpoint_preserved=True,tamper_rejected_before_decoder=True)
