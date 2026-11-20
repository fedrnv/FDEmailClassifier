"""Offline installation of the exact locally reviewed model-check wheel closure."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
wheels=ROOT/"training/data/export-model-wheels-20261120"
observed=json.loads((HERE/"model-wheel-observations-v2.json").read_text())
for row in observed["wheels"]:
    if hashlib.sha256((wheels/row["filename"]).read_bytes()).hexdigest()!=row["sha256"]:raise ValueError("model_tooling_wheel_changed")
result=subprocess.run([str(ROOT/".venv/export/Scripts/python.exe"),"-m","pip","install","--no-index","--no-deps","--require-hashes","--find-links",str(wheels),"-r",str(ROOT/"models/export-model-requirements-win-py314.txt")],capture_output=True)
if result.returncode:raise ValueError("offline_model_tooling_install_failed")
print(json.dumps(dict(installed_packages=len(observed["wheels"]),model_tensors_downloaded=False,model_training_performed=False)))
