"""Fetch the official versioned schema for offline SBOM validation; no code import."""
from pathlib import Path
import hashlib
import json
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
destination=ROOT/"training/data/export-sbom-schema-v1"
evidence=HERE/"sbom-schema-observations-v1.json"
if destination.exists() or evidence.exists():raise ValueError("append_only_schema_observation")
destination.mkdir(parents=True)
files=[]
for name in ("bom-1.6.schema.json","spdx.schema.json","jsf-0.82.schema.json"):
    url="https://cyclonedx.org/schema/"+name
    with urllib.request.urlopen(url,timeout=30) as response: data=response.read(2_000_001)
    if len(data)>2_000_000:raise ValueError("schema_size_limit")
    json.loads(data)
    with (destination/name).open("xb") as out:out.write(data)
    files.append(dict(filename=name,url=url,sha256=hashlib.sha256(data).hexdigest(),size=len(data)))
with evidence.open("x",encoding="utf-8") as out:out.write(json.dumps(dict(schema="fdec-export-sbom-schema-observations/v1",files=files),indent=2)+"\n")
print(json.dumps(dict(schemas=len(files),model_tensors_downloaded=False)))
