"""Metadata-only installed-runtime/GPU availability observation, no training."""
import importlib.metadata
import json
from pathlib import Path
import platform,sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/"training/finetune"))
from trainer_config import read,TrainerError
from torch_engine import deterministic_runtime
import torch

value=dict(schema="fdec-local-training-runtime/v2",python=platform.python_version(),packages={name:importlib.metadata.version(name) for name in ("torch","transformers","peft","numpy","safetensors")},cuda_available=torch.cuda.is_available(),cuda_device_count=torch.cuda.device_count(),torch_cuda_build=torch.version.cuda,actual_email_training=False,supported_gpu_acceptance=False)
try:deterministic_runtime(read(ROOT/"training/config/peft-trainer-v1.json"))
except TrainerError as error:
    reason=str(error)
    if reason not in ("single_bfloat16_cuda_device_required","incompatible_training_runtime","incompatible_cublas_determinism"):raise
    value["actual_training_runtime_rejection"]=reason
else:value["actual_training_runtime_rejection"]=None
print(json.dumps(value,sort_keys=True))
