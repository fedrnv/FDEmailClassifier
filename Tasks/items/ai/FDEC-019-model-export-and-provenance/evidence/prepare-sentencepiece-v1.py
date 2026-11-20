"""Audit and install one converter dependency; no model/data acquisition."""
from email.parser import BytesParser
import hashlib,json
from pathlib import Path
import subprocess,sys,urllib.request,zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def fetch(url):
    with urllib.request.urlopen(url,timeout=60) as response:return response.read()
metadata_url="https://pypi.org/pypi/sentencepiece/json"
latest=json.loads(fetch(metadata_url));version=latest["info"]["version"]
if not version.startswith("0.2."):raise ValueError("converter_sentencepiece_version_outside_upstream_requirement")
metadata_url=f"https://pypi.org/pypi/sentencepiece/{version}/json"
public=json.loads(fetch(metadata_url))
row=next(item for item in public["urls"] if item["filename"].endswith("cp314-cp314-win_amd64.whl"))
raw=fetch(row["url"]);sha=hashlib.sha256(raw).hexdigest()
if sha!=row["digests"]["sha256"] or len(raw)!=row["size"]:raise ValueError("dependency_integrity_failed")
destination=ROOT/"training/data/export-model-wheels-20261120"/row["filename"]
with destination.open("xb") as out:out.write(raw)
with zipfile.ZipFile(destination) as archive:
    files=[name for name in archive.namelist() if ".dist-info/" in name and "license" in name.lower() and not name.endswith("/")]
    licenses=[dict(path=name,sha256=hashlib.sha256(archive.read(name)).hexdigest(),prefix=archive.read(name).decode(errors="replace")[:350]) for name in files]
    if not any("Apache License" in item["prefix"] for item in licenses):raise ValueError("dependency_license_unresolved")
observation=dict(schema="fdec-export-tooling-supplement/v1",name="sentencepiece",version=version,filename=row["filename"],url=row["url"],metadata_url=metadata_url,size=len(raw),sha256=sha,licenses=licenses,license="Apache-2.0",scope="local converter dependency only; notices retained; no model training or redistribution approval")
with (HERE/"sentencepiece-observation-v1.json").open("x",encoding="utf-8") as out:out.write(json.dumps(observation,indent=2)+"\n")
lock=ROOT/"training/data/export-sentencepiece-lock-v1.txt"
with lock.open("x",encoding="utf-8") as out:out.write(f"sentencepiece=={version} --hash=sha256:{sha}\n")
result=subprocess.run([sys.executable,"-m","pip","install","--no-index","--no-deps","--require-hashes","--find-links",str(destination.parent),"-r",str(lock)],capture_output=True)
if result.returncode:raise ValueError("offline_dependency_install_failed")
print(json.dumps(observation))
