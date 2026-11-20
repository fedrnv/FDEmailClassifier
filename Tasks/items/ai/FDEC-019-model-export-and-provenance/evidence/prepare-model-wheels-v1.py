"""Prepare pinned local model-code tooling, without model tensors or datasets."""
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
destination=ROOT/"training/data/export-model-wheels-20261120"
evidence=HERE/"model-wheel-observations-v1.json"
if destination.exists() or evidence.exists():raise ValueError("append_only_model_tooling")
destination.mkdir(parents=True)
pins=json.loads((ROOT/"models/export-runtime-v1.json").read_text())["packages"]
pins.update(torch="2.15.0",transformers="5.23.0",peft="0.22.0")
result=subprocess.run([sys.executable,"-m","pip","download","--only-binary=:all:","--dest",str(destination),*[name+"=="+version for name,version in pins.items()]],capture_output=True,text=True)
if result.returncode:raise ValueError("model_tooling_wheel_download_failed")
rows=[]
for path in sorted(destination.glob("*.whl")):
    with zipfile.ZipFile(path) as archive:
        metadata=BytesParser().parsebytes(archive.read(next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))))
        name,version=metadata["Name"],metadata["Version"]
        address=f"https://pypi.org/pypi/{name}/{version}/json"
        with urllib.request.urlopen(address,timeout=30) as response:public=json.load(response)
        expected=next(item for item in public["urls"] if item["filename"]==path.name)
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if sha!=expected["digests"]["sha256"]:raise ValueError("model_tooling_checksum_mismatch")
        licenses=[]
        for entry in archive.namelist():
            if ".dist-info/" in entry and any(word in entry.casefold() for word in ("license","copying","notice")) and not entry.endswith("/"):
                raw=archive.read(entry);licenses.append(dict(path=entry,sha256=hashlib.sha256(raw).hexdigest(),prefix=raw.decode("utf-8",errors="replace")[:350]))
        if not licenses:raise ValueError("model_tooling_license_missing")
        rows.append(dict(name=name,version=version,filename=path.name,size=path.stat().st_size,sha256=sha,license=metadata.get("License-Expression") or metadata.get("License"),metadata_url=address,licenses=licenses))
with evidence.open("x",encoding="utf-8") as out:out.write(json.dumps(dict(schema="fdec-export-model-wheel-observations/v1",wheels=rows,installed=False,model_tensors_downloaded=False,redistribution_approved=False),indent=2)+"\n")
print(json.dumps(dict(wheels=[dict(name=row['name'],version=row['version'],license=row['license']) for row in rows],model_tensors_downloaded=False)))
