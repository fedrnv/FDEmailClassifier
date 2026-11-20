"""Install hash-pinned locally inspected tooling into a new isolated test venv."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import venv

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
destination=ROOT/".venv/export"
if destination.exists(): raise ValueError("export_environment_already_exists")
observed=json.loads((HERE/"wheel-observations-v1.json").read_text())
wheels=ROOT/"training/data/export-wheels-20261120"
for row in observed["wheels"]:
    if hashlib.sha256((wheels/row["filename"]).read_bytes()).hexdigest()!=row["sha256"]: raise ValueError("wheel_changed")
venv.EnvBuilder(with_pip=True,symlinks=False).create(destination)
python=destination/"Scripts/python.exe"
result=subprocess.run([str(python),"-m","pip","install","--no-index","--no-deps","--require-hashes","--find-links",str(wheels),"-r",str(ROOT/"models/export-runtime-requirements-win-py314.txt")],capture_output=True,text=True)
if result.returncode: raise ValueError("offline_runtime_install_failed")
print(json.dumps(dict(installed=True,packages=len(observed["wheels"]),offline=True,model_tensors_downloaded=False)))
