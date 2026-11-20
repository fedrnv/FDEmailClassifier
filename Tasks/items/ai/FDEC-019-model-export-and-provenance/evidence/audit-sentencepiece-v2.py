"""Resolve missing wheel license from exact publisher version tag, then install."""
import hashlib,json
from pathlib import Path
import subprocess,sys,urllib.request

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"FDEmailClassifier-tooling-audit"}),timeout=60) as response:return response.read()
version="0.2.3";metadata_url=f"https://pypi.org/pypi/sentencepiece/{version}/json"
public=json.loads(fetch(metadata_url))
path=next((ROOT/"training/data/export-model-wheels-20261120").glob("sentencepiece-0.2.3-cp314-cp314-win_amd64.whl"))
row=next(item for item in public["urls"] if item["filename"]==path.name)
sha=hashlib.sha256(path.read_bytes()).hexdigest()
if sha!=row["digests"]["sha256"] or path.stat().st_size!=row["size"]:raise ValueError("dependency_integrity_failed")
ref=json.loads(fetch(f"https://api.github.com/repos/google/sentencepiece/git/ref/tags/v{version}"))["object"]
if ref["type"]=="tag":ref=json.loads(fetch("https://api.github.com/repos/google/sentencepiece/git/tags/"+ref["sha"]))["object"]
if ref["type"]!="commit":raise ValueError("version_tag_not_commit")
url=f"https://raw.githubusercontent.com/google/sentencepiece/{ref['sha']}/LICENSE"
license=fetch(url)
if b"Apache License" not in license or b"Version 2.0" not in license:raise ValueError("dependency_license_unresolved")
notice=path.parent/"sentencepiece-0.2.3-LICENSE"
with notice.open("xb") as out:out.write(license)
observation=dict(schema="fdec-export-tooling-supplement/v1",name="sentencepiece",version=version,filename=row["filename"],url=row["url"],metadata_url=metadata_url,size=path.stat().st_size,sha256=sha,license="Apache-2.0",license_supplement=dict(url=url,source_revision=ref["sha"],sha256=hashlib.sha256(license).hexdigest(),size=len(license)),scope="local converter dependency only; official version notice retained outside wheel; no model training or redistribution approval")
with (HERE/"sentencepiece-observation-v2.json").open("x",encoding="utf-8") as out:out.write(json.dumps(observation,indent=2)+"\n")
lock=ROOT/"training/data/export-sentencepiece-lock-v2.txt"
with lock.open("x",encoding="utf-8") as out:out.write(f"sentencepiece=={version} --hash=sha256:{sha}\n")
result=subprocess.run([sys.executable,"-m","pip","install","--no-index","--no-deps","--require-hashes","--find-links",str(path.parent),"-r",str(lock)],capture_output=True)
if result.returncode:raise ValueError("offline_dependency_install_failed")
print(json.dumps(observation))
