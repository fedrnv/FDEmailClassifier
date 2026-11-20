"""Technical random-tensor export acceptance diagnostic runner, never emails."""
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/"training/export"))
import tiny_model_check

diagnostics=ROOT/"training/outputs/fdec019-tiny-probe-v3-logs"
diagnostics.mkdir(exist_ok=False)
original=subprocess.run
counter=0
def capture(command,*args,**kwargs):
    global counter
    result=original(command,*args,**kwargs)
    if any(str(part).endswith(("convert_lora_to_gguf.py","convert_hf_to_gguf.py","llama-completion.exe")) for part in command):
        counter+=1
        for stream in ("stdout","stderr"):
            value=getattr(result,stream)
            if value is not None:
                (diagnostics/f"{counter}-{stream}.txt").write_bytes(value.encode() if isinstance(value,str) else value)
        print(json.dumps(dict(stage=counter,exit_code=result.returncode)),flush=True)
    return result
subprocess.run=capture
try:
    report=tiny_model_check.run(ROOT/"training/outputs/fdec019-tiny-probe-v3",ROOT/"training/data/export-llama-cpp-29b52d3",reuse_observed_build=True)
    print(json.dumps(report),flush=True)
except Exception:
    traceback.print_exc()
    raise
finally:subprocess.run=original
