"""Acquire the exact public MIT source checkout; no model or dataset download."""
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
revision=json.loads((ROOT/"models/export-runtime-v1.json").read_text())["llama_cpp_revision"]
path=ROOT/"training/data/export-llama-cpp-29b52d3"
if path.exists():raise ValueError("source_checkout_already_exists")
path.mkdir(parents=True)
commands=[["git","init","--quiet"],["git","config","core.autocrlf","false"],["git","remote","add","origin","https://github.com/ggml-org/llama.cpp.git"],["git","fetch","--depth","1","origin",revision],["git","checkout","--detach","--quiet","FETCH_HEAD"]]
for command in commands:
    result=subprocess.run(command,cwd=path,capture_output=True,timeout=300)
    if result.returncode:raise ValueError("pinned_source_acquisition_failed")
print(json.dumps(dict(source_revision=revision,model_tensors_downloaded=False)))
