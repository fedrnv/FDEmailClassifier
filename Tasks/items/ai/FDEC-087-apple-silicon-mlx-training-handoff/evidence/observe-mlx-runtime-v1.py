"""Pin public MLX tooling/source identities for local inspection, never models."""
import hashlib,json
from pathlib import Path
import urllib.request

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"FDEmailClassifier-runtime-observation"}),timeout=60) as response:return response.read()
records=[]
for name,version in (("mlx","0.32.4"),("mlx-metal","0.32.4"),("mlx-lm","0.32.2")):
    url=f"https://pypi.org/pypi/{name}/{version}/json";raw=fetch(url);value=json.loads(raw)
    selected=[dict(filename=row["filename"],url=row["url"],sha256=row["digests"]["sha256"],size=row["size"]) for row in value["urls"] if row["filename"].endswith(("cp314-cp314-macosx_15_0_arm64.whl","py3-none-macosx_15_0_arm64.whl","py3-none-any.whl"))]
    records.append(dict(name=name,version=version,metadata_url=url,metadata_sha256=hashlib.sha256(raw).hexdigest(),license=value["info"].get("license_expression") or value["info"].get("license"),requires=value["info"].get("requires_dist"),wheels=selected))
documents=[]
for project,version,paths in (("mlx","0.32.4",["LICENSE","python/mlx/optimizers/optimizers.py","python/mlx/utils.py","python/src/random.cpp"]),("mlx-lm","0.32.2",["LICENSE","mlx_lm/tuner/utils.py","mlx_lm/tuner/lora.py","mlx_lm/models/qwen3.py","mlx_lm/utils.py"])):
    ref=json.loads(fetch(f"https://api.github.com/repos/ml-explore/{project}/git/ref/tags/v{version}"))["object"]
    if ref["type"]=="tag":ref=json.loads(fetch(f"https://api.github.com/repos/ml-explore/{project}/git/tags/{ref['sha']}"))["object"]
    if ref["type"]!="commit":raise ValueError("tooling_tag_not_commit")
    for name in paths:
        url=f"https://raw.githubusercontent.com/ml-explore/{project}/{ref['sha']}/{name}";raw=fetch(url)
        destination=ROOT/"training/data/mlx-api-observation-v1"/project/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open("xb") as out:out.write(raw)
        documents.append(dict(project=project,version=version,source_revision=ref["sha"],path=name,url=url,sha256=hashlib.sha256(raw).hexdigest(),size=len(raw)))
result=dict(schema="fdec-mlx-runtime-observation/v1",packages=records,documents=documents,installed=False,actual_apple_execution=False,model_tensors_downloaded=False,redistribution_approved=False)
with (HERE/"mlx-runtime-observations-v1.json").open("x",encoding="utf-8") as out:out.write(json.dumps(result,indent=2)+"\n")
print(json.dumps(dict(packages=[dict(name=r['name'],version=r['version'],selected_wheels=len(r['wheels'])) for r in records],documents=len(documents),actual_apple_execution=False)))
