"""Observe public rights metadata only. Never fetch or print corpus examples."""

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[2]
DATASETS = {
    "sinabis-group/sinabis-10k-synthetic-emails": "4b8e73e28074c94b9c70934501bee1ed8c98e395",
    "sinabis-group/sinabis-10m-synthetic-emails": "62385fbfe6aeb838305183215b55456ff5345cd5",
    "sinabis-group/sinabis-1m-synthetic-emails": "147b6c501c2910fb06626b9bbb9f109e1c2a6340",
}
MODELS = {
    "Qwen/Qwen3.6-35B-A3B": "345d467b117d1fd5eda9b879a5988de9ae5f47a7",
    "Qwen/Qwen3.5-9B": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
    "deepseek-ai/DeepSeek-V4-Flash": "60d8d70770c6776ff598c94bb586a859a38244f1",
    "google/gemma-4-26B-A4B": "24548b62aa021d562695c04aaf7758a1ea47990b",
}


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "FDEmailClassifier-rights-audit/1"}), timeout=30) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError("metadata_limit")
    return data


def observe():
    documents = []

    def document(url):
        data = fetch(url)
        documents.append(dict(url=url, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        return data

    datasets = []
    for name, revision in DATASETS.items():
        metadata = json.loads(document(f"https://huggingface.co/api/datasets/{name}/revision/{revision}?blobs=true"))
        if metadata["sha"] != revision:
            raise ValueError("revision_changed")
        document(f"https://huggingface.co/datasets/{name}/raw/{revision}/README.md")
        files = [{key: row[key] for key in ("rfilename", "size", "blobId", "lfs") if key in row}
                 for row in metadata["siblings"] if row["rfilename"] in ("README.md", "data/train-00000-of-00001.parquet", "docs/generation/company.json", "docs/generation/email_prompts.json")]
        datasets.append(dict(dataset_id=name, revision=revision, declared_license=metadata["cardData"]["license"], files=files))
    for path in ("company.json", "email_prompts.json"):
        document(f"https://huggingface.co/datasets/sinabis-group/sinabis-1m-synthetic-emails/raw/{DATASETS['sinabis-group/sinabis-1m-synthetic-emails']}/docs/generation/{path}")
    models = []
    for name, revision in MODELS.items():
        metadata = json.loads(document(f"https://huggingface.co/api/models/{name}/revision/{revision}?blobs=true"))
        if metadata["sha"] != revision:
            raise ValueError("revision_changed")
        document(f"https://huggingface.co/{name}/raw/{revision}/README.md")
        if any(row["rfilename"] == "LICENSE" for row in metadata["siblings"]):
            document(f"https://huggingface.co/{name}/raw/{revision}/LICENSE")
        models.append(dict(model_id=name, revision=revision, declared_license=metadata["cardData"]["license"]))
    for url in (
        "https://creativecommons.org/licenses/by/4.0/legalcode.en",
        "https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html",
        "https://cdn.deepseek.com/policies/en-US/deepseek-terms-of-use.html",
        "https://gemma.ai/resources/apache-2/",
        "https://gemma.ai/resources/terms/",
    ):
        document(url)
    return dict(schema="fdec-sinabis-source-observations/v1", observed_date="2026-11-20", datasets=datasets, models=models, documents=documents)


if __name__ == "__main__":
    result = observe()
    output = ROOT / "training/augmentation/sinabis-source-observations-v1.json"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print("PASS: pinned public metadata observed; no corpus fetched")
