"""Reproduce hash-pinned local tooling/schema inputs; never download model data."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import urllib.request
import venv

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/"Tasks/items/ai/FDEC-019-model-export-and-provenance/evidence"


def materialize(url,path,sha256,size):
    if path.is_symlink() or path.is_junction():raise ValueError("linked_tooling_path")
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha256:raise ValueError("existing_tooling_changed")
        return
    if not url.startswith(("https://files.pythonhosted.org/","https://raw.githubusercontent.com/CycloneDX/specification/")):raise ValueError("unapproved_tooling_host")
    with urllib.request.urlopen(url,timeout=60) as response:data=response.read(size+1)
    if len(data)!=size or hashlib.sha256(data).hexdigest()!=sha256:raise ValueError("tooling_checksum_mismatch")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("xb") as out:out.write(data)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opt-in",action="store_true",required=True)
    parser.parse_args()
    if sys.platform!="win32" or sys.version_info[:2]!=(3,14) or platform.machine().lower() not in ("amd64","x86_64"):raise ValueError("audited_lock_is_windows_py314_amd64_only")
    for row in json.loads((EVIDENCE/"sbom-schema-observations-v2.json").read_text())["files"]:
        materialize(row["url"],ROOT/"training/data/export-sbom-schema-v2"/row["filename"],row["sha256"],row["size"])
    wheels=ROOT/"training/data/export-wheels-20261120"
    for row in json.loads((EVIDENCE/"wheel-observations-v1.json").read_text())["wheels"]:
        with urllib.request.urlopen(row["metadata_url"],timeout=30) as response:metadata=json.load(response)
        artifact=next(item for item in metadata["urls"] if item["filename"]==row["filename"])
        if artifact["digests"]["sha256"]!=row["sha256"]:raise ValueError("publisher_tooling_identity_changed")
        materialize(artifact["url"],wheels/row["filename"],row["sha256"],row["size"])
    destination=ROOT/".venv/export"
    if not destination.exists():
        venv.EnvBuilder(with_pip=True,symlinks=False).create(destination)
        result=subprocess.run([str(destination/"Scripts/python.exe"),"-m","pip","install","--no-index","--no-deps","--require-hashes","--find-links",str(wheels),"-r",str(ROOT/"models/export-runtime-requirements-win-py314.txt")],capture_output=True)
        if result.returncode:raise ValueError("offline_export_tooling_install_failed")
    print("Export tooling/schema inputs ready; no models or datasets downloaded")


if __name__=="__main__":
    try:main()
    except Exception:
        print("export_tooling_bootstrap_rejected",file=sys.stderr)
        raise SystemExit(2)
