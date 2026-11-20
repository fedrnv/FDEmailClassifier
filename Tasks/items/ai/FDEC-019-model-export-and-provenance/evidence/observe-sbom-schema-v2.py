"""Official repository fallback after cyclonedx.org returned HTTP 403."""
from pathlib import Path
import hashlib
import json
import urllib.request

def fetch(url):
    request=urllib.request.Request(url,headers={"User-Agent":"FDEmailClassifier-schema-review"})
    with urllib.request.urlopen(request,timeout=30) as response:data=response.read(2_000_001)
    if len(data)>2_000_000:raise ValueError("schema_size_limit")
    return data

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
destination=ROOT/"training/data/export-sbom-schema-v2"
evidence=HERE/"sbom-schema-observations-v2.json"
if destination.exists() or evidence.exists():raise ValueError("append_only_schema_observation")
repo=json.loads(fetch("https://api.github.com/repos/CycloneDX/specification"))
sha=json.loads(fetch("https://api.github.com/repos/CycloneDX/specification/commits/"+repo["default_branch"]))["sha"]
destination.mkdir(parents=True)
files=[]
for name in ("bom-1.6.schema.json","spdx.schema.json","jsf-0.82.schema.json"):
    url=f"https://raw.githubusercontent.com/CycloneDX/specification/{sha}/schema/{name}"
    data=fetch(url);json.loads(data)
    with (destination/name).open("xb") as out:out.write(data)
    files.append(dict(filename=name,url=url,sha256=hashlib.sha256(data).hexdigest(),size=len(data)))
with evidence.open("x",encoding="utf-8") as out:out.write(json.dumps(dict(schema="fdec-export-sbom-schema-observations/v1",repository_revision=sha,files=files,website_attempt="HTTP 403; v1 script retained"),indent=2)+"\n")
print(json.dumps(dict(schemas=len(files),revision=sha,model_tensors_downloaded=False)))
