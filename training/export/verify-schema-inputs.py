"""Check the exact official schema snapshot before offline validation."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
observed=json.loads((ROOT/"Tasks/items/ai/FDEC-019-model-export-and-provenance/evidence/sbom-schema-observations-v2.json").read_text())
for entry in observed["files"]:
    path=ROOT/"training/data/export-sbom-schema-v2"/entry["filename"]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=entry["sha256"]:raise ValueError("sbom_schema_changed")
print("PASS: pinned official SBOM schemas")
