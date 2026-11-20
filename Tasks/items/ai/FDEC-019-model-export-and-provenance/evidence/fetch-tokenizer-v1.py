"""Fetch only exact Apache-licensed tokenizer metadata; no pretrained tensors."""
import hashlib
import json
from pathlib import Path
import urllib.request

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
profile=json.loads((ROOT/"training/baseline/qwen-stock-v1.json").read_text())
destination=ROOT/"training/data/export-qwen-tokenizer-v1"
if destination.exists():raise ValueError("tokenizer_destination_already_exists")
destination.mkdir(parents=True)
files=[]
for row in profile["files"]:
    if row["path"] not in ("LICENSE","tokenizer.json","tokenizer_config.json","vocab.json","merges.txt"):continue
    url=f"https://huggingface.co/{profile['model_id']}/resolve/{profile['revision']}/{row['path']}"
    with urllib.request.urlopen(url,timeout=60) as response:data=response.read(row["size"]+1)
    actual=hashlib.sha256(data).hexdigest() if row["algorithm"]=="sha256" else hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
    if len(data)!=row["size"] or actual!=row["digest"]:raise ValueError("tokenizer_identity_mismatch")
    with (destination/row["path"]).open("xb") as out:out.write(data)
    files.append(dict(path=row["path"],sha256=hashlib.sha256(data).hexdigest(),size=len(data)))
value=dict(schema="fdec-export-tokenizer-observation/v1",model_id=profile["model_id"],revision=profile["revision"],files=files,pretrained_tensors_downloaded=False,scope="local-technical-runtime-check-only",redistribution_approved=False)
with (HERE/"tokenizer-observations-v1.json").open("x",encoding="utf-8") as out:out.write(json.dumps(value,indent=2)+"\n")
print(json.dumps(dict(files=len(files),pretrained_tensors_downloaded=False)))
