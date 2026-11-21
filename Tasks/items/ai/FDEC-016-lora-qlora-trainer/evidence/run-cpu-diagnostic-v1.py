"""Numerical-only CPU diagnostic; never loads emails or pretrained tensors."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/"training/finetune"))
from gpu_check import run_cpu
print(json.dumps(run_cpu(opt_in=True),sort_keys=True))
