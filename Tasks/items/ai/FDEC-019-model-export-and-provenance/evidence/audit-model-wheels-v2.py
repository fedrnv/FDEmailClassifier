"""Verify downloaded wheels; resolve tokenizers' missing notice from exact upstream tag."""
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"FDEmailClassifier-tooling-audit"}),timeout=30) as response:return response.read()
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
destination=ROOT/"training/data/export-model-wheels-20261120"
evidence=HERE/"model-wheel-observations-v2.json"
if evidence.exists():raise ValueError("append_only_model_tooling")
ref=json.loads(fetch("https://api.github.com/repos/huggingface/tokenizers/git/ref/tags/v0.23.3"))["object"]
if ref["type"]=="tag":ref=json.loads(fetch("https://api.github.com/repos/huggingface/tokenizers/git/tags/"+ref["sha"]))["object"]
if ref["type"]!="commit":raise ValueError("tokenizers_tag_not_commit")
url=f"https://raw.githubusercontent.com/huggingface/tokenizers/{ref['sha']}/LICENSE"
raw=fetch(url)
if b"Apache License" not in raw or b"Version 2.0" not in raw:raise ValueError("tokenizers_version_license_unresolved")
supplement=dict(version="0.23.3",source_revision=ref["sha"],url=url,sha256=hashlib.sha256(raw).hexdigest(),license="Apache-2.0",scope="local-use-only; wheel omitted license; no runtime redistribution approval")
rows=[]
for path in sorted(destination.glob("*.whl")):
    with zipfile.ZipFile(path) as archive:
        metadata=BytesParser().parsebytes(archive.read(next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))))
        name,version=metadata["Name"],metadata["Version"]
        address=f"https://pypi.org/pypi/{name}/{version}/json";public=json.loads(fetch(address))
        expected=next(item for item in public["urls"] if item["filename"]==path.name)
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if sha!=expected["digests"]["sha256"]:raise ValueError("model_tooling_checksum_mismatch")
        licenses=[]
        for entry in archive.namelist():
            if ".dist-info/" in entry and any(word in entry.casefold() for word in ("license","copying","notice")) and not entry.endswith("/"):
                data=archive.read(entry);licenses.append(dict(path=entry,sha256=hashlib.sha256(data).hexdigest(),prefix=data.decode("utf-8",errors="replace")[:350]))
        if not licenses and (name,version)!=("tokenizers","0.23.3"):raise ValueError("model_tooling_license_missing")
        rows.append(dict(name=name,version=version,filename=path.name,size=path.stat().st_size,sha256=sha,license=metadata.get("License-Expression") or metadata.get("License"),metadata_url=address,licenses=licenses,versioned_license_supplement=supplement if not licenses else None))
with evidence.open("x",encoding="utf-8") as out:out.write(json.dumps(dict(schema="fdec-export-model-wheel-observations/v1",wheels=rows,installed=False,model_tensors_downloaded=False,redistribution_approved=False),indent=2)+"\n")
print(json.dumps(dict(wheels=[dict(name=row['name'],version=row['version'],license=row['license'],supplement=bool(row['versioned_license_supplement'])) for row in rows],model_tensors_downloaded=False)))
