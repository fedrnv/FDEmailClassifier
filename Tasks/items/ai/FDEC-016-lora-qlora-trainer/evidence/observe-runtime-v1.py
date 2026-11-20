"""Observe public package metadata only; no installation or model execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

destination = Path(__file__).with_name("runtime-observations-v1.json")
if destination.exists():
    raise ValueError("append_only_evidence")
packages = []
for name in ("torch", "transformers", "peft", "safetensors", "bitsandbytes", "numpy"):
    address = f"https://pypi.org/pypi/{name}/json"
    with urllib.request.urlopen(urllib.request.Request(address, headers={"User-Agent": "FDEmailClassifier-runtime-review"}), timeout=30) as response:
        raw = response.read(8_000_001)
    if len(raw) > 8_000_000:
        raise ValueError("metadata_limit")
    info = json.loads(raw)["info"]
    packages.append(dict(name=name, version=info["version"], requires_python=info["requires_python"], license=info.get("license_expression") or info.get("license"), metadata_url=address, metadata_sha256=hashlib.sha256(raw).hexdigest()))
result = dict(schema="fdec-trainer-runtime-observations/v1", observed_at=datetime.now(timezone.utc).isoformat(), packages=packages, installation_performed=False, actual_runtime_verified=False, wheel_or_transitive_license_audit_complete=False)
with destination.open("x", encoding="utf-8") as output:
    output.write(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
