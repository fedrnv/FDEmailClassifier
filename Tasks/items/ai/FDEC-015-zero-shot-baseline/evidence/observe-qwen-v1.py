"""Read public metadata only; never download model tensors or email data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent


def fetch(url, limit=4_000_000):
    request = urllib.request.Request(url, headers={"User-Agent": "FDEmailClassifier-metadata-review"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("public_metadata_size_limit")
    return data


def main():
    destination = HERE / "qwen-observations-v1.json"
    if destination.exists():
        raise ValueError("observations_are_append_only")
    url = "https://huggingface.co/api/models/Qwen/Qwen3-0.6B?blobs=true"
    raw = fetch(url)
    metadata = json.loads(raw)
    revision = metadata["sha"]
    documents, parsed = [], {}
    for name in ("README.md", "LICENSE", "config.json", "generation_config.json", "tokenizer_config.json"):
        address = f"https://huggingface.co/Qwen/Qwen3-0.6B/raw/{revision}/{name}"
        content = fetch(address)
        documents.append(dict(path=name, url=address, sha256=hashlib.sha256(content).hexdigest(), size=len(content)))
        if name.endswith(".json"):
            parsed[name] = json.loads(content)
    packages = []
    for name in ("transformers", "torch"):
        address = f"https://pypi.org/pypi/{name}/json"
        content = fetch(address)
        info = json.loads(content)["info"]
        packages.append(dict(name=name, version=info["version"], requires_python=info["requires_python"], license=info.get("license_expression") or info.get("license"), metadata_url=address, metadata_sha256=hashlib.sha256(content).hexdigest()))
    config = parsed["config.json"]
    result = dict(schema="fdec-model-observations/v1", observed_at=datetime.now(timezone.utc).isoformat(), model_id=metadata["id"], revision=revision,
                  metadata_url=url, metadata_sha256=hashlib.sha256(raw).hexdigest(), declared_license=metadata.get("cardData", {}).get("license"),
                  files=[dict(path=item["rfilename"], size=item.get("size"), git_blob=item.get("blobId"), lfs=item.get("lfs")) for item in metadata["siblings"]],
                  documents=documents, configuration={key: config.get(key) for key in ("architectures", "model_type", "hidden_size", "num_hidden_layers", "num_attention_heads", "num_key_value_heads", "vocab_size", "max_position_embeddings", "tie_word_embeddings")},
                  non_thinking_template_declared="enable_thinking" in parsed["tokenizer_config.json"].get("chat_template", ""), packages=packages,
                  model_tensors_downloaded=False, runtime_installed=False, corpus_admitted=False, public_artifact_release_approved=False)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(model_id=result["model_id"], revision=revision, license=result["declared_license"], files=len(result["files"]), packages=packages, tensors_downloaded=False), indent=2))


if __name__ == "__main__":
    main()
