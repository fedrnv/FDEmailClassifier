"""Public package/source metadata only. No model tensor or email download."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "FDEmailClassifier-export-review"}), timeout=30) as response:
        data = response.read(10_000_001)
    if len(data) > 10_000_000: raise ValueError("metadata_limit")
    return data

path = Path(__file__).with_name("runtime-observations-v1.json")
if path.exists(): raise ValueError("append_only_evidence")
packages=[]
for name in ("gguf", "numpy", "safetensors", "PyYAML", "tqdm", "pyarrow"):
    url=f"https://pypi.org/pypi/{name}/json"
    raw=fetch(url); info=json.loads(raw)["info"]
    packages.append(dict(name=name,version=info["version"],requires_dist=info.get("requires_dist"),license=info.get("license_expression") or info.get("license"),metadata_url=url,metadata_sha256=hashlib.sha256(raw).hexdigest()))
commit=json.loads(fetch("https://api.github.com/repos/ggml-org/llama.cpp/commits/master"))["sha"]
documents=[]
for name in ("LICENSE", "convert_lora_to_gguf.py", "convert_hf_to_gguf.py"):
    url=f"https://raw.githubusercontent.com/ggml-org/llama.cpp/{commit}/{name}"
    data=fetch(url)
    documents.append(dict(path=name,url=url,sha256=hashlib.sha256(data).hexdigest(),size=len(data)))
value=dict(schema="fdec-export-runtime-observations/v1",observed_at=datetime.now(timezone.utc).isoformat(),packages=packages,llama_cpp_revision=commit,documents=documents,model_tensors_downloaded=False,installed=False,redistribution_approved=False)
with path.open("x",encoding="utf-8") as out:out.write(json.dumps(value,indent=2)+"\n")
print(json.dumps(value))
