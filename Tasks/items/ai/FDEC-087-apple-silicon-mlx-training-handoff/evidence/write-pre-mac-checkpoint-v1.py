"""Append a public-safe checkpoint; never export private keys or approve owners."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'training/finetune'))
import mlx_handoff as handoff
import portable_source

evidence=Path(__file__).resolve().parent
store=Path(os.environ['LOCALAPPDATA'])/'FDEmailClassifier/private-FDEC-087-v1'
state=handoff.Handoff(store/'handoff')
portable_source.verify(state.manifest['source'])
ready=handoff.read(evidence/'readiness-v2.json')
def binding(relative):
    raw=(ROOT/relative).read_bytes().replace(b'\r\n',b'\n')
    return dict(path=relative,canonical_lf_sha256=hashlib.sha256(raw).hexdigest())
assert not (store/'owner-transition.json').exists(), 'No real owner activation may exist yet'
result=dict(
    schema='fdec-pre-mac-checkpoint/v1',task_id='FDEC-087',epic_id='FDEC-EPIC-D003',
    source=state.manifest['source'],source_environment=dict(platform=sys.platform,architecture=platform.machine(),python=platform.python_version()),
    policy_sha256=ready['policy_sha256'],readiness=dict(path='evidence/readiness-v2.json',source_state_algorithm=ready['source_state_algorithm'],source_state_sha256=ready['source_state_sha256']),
    task_state_at_prepare=state.manifest['task_state_at_prepare'],accepted_next_state='Blocked awaiting explicit owner Mac transition; not Done',
    working_tree=dict(source_clean=True,unrelated_preserved=['.idea/'],own_task_bookkeeping_pending=True,other_source_changes=False),
    handoff_sha256=state.sha256,source_bundle=state.manifest['source_bundle'],purpose=state.manifest['purpose'],
    bindings=[binding(path) for path in ('Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/evidence/readiness-v2.json','training/config/mlx-runtime-v1.json','training/config/mlx-trainer-v1.json','training/config/mlx-requirements-py314-macos15-arm64.txt','Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/evidence/local-mac-tooling-review-v1.md','Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/evidence/software-verification-v1.json','Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/evidence/software-test-output-v1.txt')],
    input_manifest_hashes=state.manifest['input_manifest_hashes'],source_license_state=state.manifest['source_license_state'],resources=state.manifest['resources'],
    private_artifact_alias='LOCALAPPDATA/FDEmailClassifier/private-FDEC-087-v1/handoff; private, outside Git',
    pending_commands=[
        'Only after explicit owner reply: record genuine confirmation and create protected external bound owner-transition.json; no approval CLI exists.',
        'Owner-authorized private kit transfer and new isolated Mac clone at the pinned source; preserve latest FDEC-087 task metadata separately.',
        'python3.14 training/finetune/handoff_cli.py inspect --handoff-dir "$PRIVATE_STORE/handoff"',
        'pwsh -NoProfile -File Tasks/items/ai/FDEC-087-apple-silicon-mlx-training-handoff/evidence/write-readiness-v2.ps1 -Name mac-readiness-unique.json',
        'python3.14 training/scripts/bootstrap_mlx.py --opt-in --handoff-dir "$PRIVATE_STORE/handoff"',
        '.venv/mlx/bin/python training/finetune/train.py mlx-check --opt-in --handoff-dir "$PRIVATE_STORE/handoff" --output-dir "$PRIVATE_STORE/mac-numeric-return"'],
    restart_predicate='Genuine owner confirmation bound to source/kit/scope; authorized private transfer; exact source and latest immutable task state; fresh FDTasks readiness/resume event; audited compatible Apple runtime/resources. Actual training additionally needs separately admitted non-OpenAI data, labels, prompt, held-out gold and current consent.',
    owner_transition_confirmed=False,owner_activation_created=False,actual_apple_execution=False,actual_email_training=False,actual_return_complete=False,public_weight_permission=False,
    continuation='Resume FDEC-087 Stage B numeric smoke after confirmation. Preserve FDEC-015 independent baseline/FDEC-016 CUDA blockers; do not run D003 gate/review or activate a second development Epic prematurely.')
handoff.write(evidence/'pre-mac-checkpoint-v1.json',result)
print(json.dumps(dict(checkpoint_created=True,source_sha=result['source']['source_sha'],handoff_sha256=state.sha256,private_keys_exported=False,owner_activation_created=False)))
