"""Download wheels only, verify PyPI hashes and record embedded license identities."""
from datetime import datetime, timezone
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
destination=ROOT/"training/data/export-wheels-20261120"
evidence=HERE/"wheel-observations-v1.json"
if destination.exists() or evidence.exists(): raise ValueError("append_only_wheel_observation")
destination.mkdir(parents=True)
result=subprocess.run([sys.executable,"-m","pip","download","--only-binary=:all:","--dest",str(destination),"gguf==0.19.0","numpy==2.5.5","safetensors==0.8.0","PyYAML==6.0.3","tqdm==4.70.1","pyarrow==26.0.1"],capture_output=True,text=True)
if result.returncode: raise ValueError("wheel_download_failed")
observed=[]
for path in sorted(destination.glob("*.whl")):
    with zipfile.ZipFile(path) as archive:
        metadata=BytesParser().parsebytes(archive.read(next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))))
        name,version=metadata["Name"],metadata["Version"]
        address=f"https://pypi.org/pypi/{name}/{version}/json"
        with urllib.request.urlopen(address,timeout=30) as response: public=json.load(response)
        expected=next(item for item in public["urls"] if item["filename"]==path.name)
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=expected["digests"]["sha256"]: raise ValueError("wheel_hash_mismatch")
        licenses=[]
        for entry in archive.namelist():
            if ".dist-info/" in entry and any(word in entry.casefold() for word in ("license","copying","notice")) and not entry.endswith("/"):
                raw=archive.read(entry)
                licenses.append(dict(path=entry,sha256=hashlib.sha256(raw).hexdigest(),prefix=raw.decode("utf-8",errors="replace")[:400]))
        if not licenses: raise ValueError("embedded_license_missing")
        observed.append(dict(name=name,version=version,filename=path.name,sha256=actual,size=path.stat().st_size,metadata_url=address,license=metadata.get("License-Expression") or metadata.get("License"),requires_dist=metadata.get_all("Requires-Dist",[]),licenses=licenses))
value=dict(schema="fdec-export-wheel-observations/v1",observed_at=datetime.now(timezone.utc).isoformat(),wheels=observed,installed=False,redistribution_approved=False)
with evidence.open("x",encoding="utf-8") as out:out.write(json.dumps(value,indent=2)+"\n")
print(json.dumps(dict(wheels=[dict(name=row["name"],version=row["version"],license=row["license"],license_files=[x["path"] for x in row["licenses"]]) for row in observed],installed=False)))
