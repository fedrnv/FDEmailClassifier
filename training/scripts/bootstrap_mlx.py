"""Owner-confirmed Mac tooling install from the exact audited offline lock."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request
import venv

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'training/finetune'))
from trainer_config import TrainerError
import mlx_handoff as handoff
from mlx_engine import hardware


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--opt-in',action='store_true',required=True)
    parser.add_argument('--handoff-dir',required=True)
    args=parser.parse_args()
    authorization=handoff.Handoff(args.handoff_dir)
    authorization.authorize(authorization.manifest['purpose'])
    hardware()
    if sys.version_info[:2]!=(3,14):raise TrainerError('audited_mlx_python314_required')
    evidence=ROOT/'Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/evidence'
    observed=evidence/'mac-wheel-observations-v1.json'
    profile=handoff.mac_profile()
    if hashlib.sha256(observed.read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=profile['wheel_observation_sha256']:raise TrainerError('mac_runtime_audit_changed')
    wheels=ROOT/'training/data/mlx-mac-wheels-v1';wheels.mkdir(parents=True,exist_ok=True)
    from ingest_dataset import reject_links
    reject_links(wheels)
    for row in handoff.read(observed)['wheels']:
        path=reject_links(wheels/row['filename'])
        if not path.is_file():
            if not row['url'].startswith('https://files.pythonhosted.org/'):raise TrainerError('mac_runtime_artifact_host_rejected')
            with urllib.request.urlopen(row['url'],timeout=60) as response:raw=response.read(row['size']+1)
            if len(raw)!=row['size'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise TrainerError('mac_runtime_artifact_changed')
            with path.open('xb') as out:out.write(raw)
        if handoff.file_identity(path)!={k:row[k] for k in ('sha256','size')}:raise TrainerError('mac_runtime_artifact_changed')
    environment=reject_links(ROOT/'.venv/mlx')
    marker=environment/'.fdec-runtime-profile'
    if environment.exists() and (not marker.is_file() or marker.read_text()!=authorization.manifest['runtime_profile_sha256']):raise TrainerError('existing_mlx_environment_not_owned')
    if not environment.exists():
        venv.EnvBuilder(with_pip=True,symlinks=False).create(environment)
        with marker.open('x') as out:out.write(authorization.manifest['runtime_profile_sha256'])
    authorization.authorize(authorization.manifest['purpose'])
    result=subprocess.run([str(environment/'bin/python'),'-I','-m','pip','--isolated','install','--prefix',str(environment),'--no-index','--no-deps','--require-hashes','--find-links',str(wheels),'-r',str(ROOT/'training/config/mlx-requirements-py314-macos15-arm64.txt')],capture_output=True,timeout=600)
    if result.returncode:raise TrainerError('offline_mlx_environment_install_failed')
    authorization.authorize(authorization.manifest['purpose'])
    print(json.dumps(dict(tooling_installed=True,model_weights_downloaded=False,actual_email_training=False,owner_transition_bound=True)))


if __name__=='__main__':
    try:main()
    except Exception:
        print('mlx_tooling_bootstrap_rejected',file=sys.stderr)
        raise SystemExit(2)
