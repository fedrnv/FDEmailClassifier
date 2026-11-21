"""Private source/owner-bound handoff. No confirmation signer or network transfer."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import sys

from trainer_config import ROOT,TrainerError
from ingest_dataset import private_output,reject_links,remove_owned,strict_json
import portable_source
import private_paths

PROFILE='training/config/mlx-runtime-v1.json'
TASK_ID='FDEC-087'
NOTICE='Training is ready. Switch development to the MacBook Air M4.'
RETURN_NOTICE='Training and artifact handoff are complete. You can return to the original development workstation.'
DIAGNOSTICS=frozenset(('explicit_opt_in_required','explicit_owner_transition_missing','owner_transition_not_bound','owner_transition_changed','owner_transition_unavailable','owner_confirmation_must_be_outside_git','apple_silicon_host_required','macos15_or_newer_required','insufficient_apple_resources','apple_power_or_thermal_condition_unsuitable','mlx_runtime_version_mismatch','mlx_runtime_package_missing','mlx_backend_import_unavailable','audited_mlx_python314_required','apple_metal_backend_required','insufficient_approved_data','consent_authority_key_missing','mlx_handoff_required','mlx_handoff_training_inputs_changed','mlx_handoff_config_mismatch','mlx_v1_unquantized_lora_only','handoff_scope_mismatch','handoff_untracked_source','handoff_working_source_drift','handoff_staged_source_drift','handoff_source_committed_drift','private_handoff_acl_rejected','private_handoff_permissions_rejected','actual_return_requires_verified_private_export','mlx_to_peft_numeric_probe_mismatch'))


def diagnostic(error):
    code=str(error)
    return code if code in DIAGNOSTICS else 'mlx_execution_rejected'


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def file_identity(path,limit=512_000_000):
    path=reject_links(path);size=0;sha=hashlib.sha256()
    with path.open('rb') as source:
        while chunk:=source.read(1024*1024):
            size+=len(chunk)
            if size>limit:raise TrainerError('handoff_artifact_size_limit')
            sha.update(chunk)
    return dict(sha256=sha.hexdigest(),size=size)
def read(path,limit=1_000_000):
    path=reject_links(path)
    with path.open('rb') as source:raw=source.read(limit+1)
    if len(raw)>limit:raise TrainerError('handoff_json_size_limit')
    return strict_json(raw.decode('utf-8-sig'))
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as out:out.write(canonical(value)+'\n')
def mac_profile(root=ROOT):return read(Path(root)/PROFILE)
def signature(value,key,domain):return hmac.new(key,domain+canonical(value).encode(),hashlib.sha256).hexdigest()


def prepare(directory,*,purpose,config_path,inputs=None,root=ROOT):
    if purpose not in ('numeric-smoke','actual-training'):raise TrainerError('invalid_handoff_purpose')
    root=Path(root);source=portable_source.verify(root=root)
    from trainer_config import read as read_config
    config=read_config(config_path)
    if config['backend']!='lora':raise TrainerError('mlx_v1_unquantized_lora_only')
    profile=mac_profile(root)
    if purpose=='actual-training':
        if not inputs:raise TrainerError('insufficient_approved_data')
        from training_inputs import admit
        import split_data
        snapshot=admit(**inputs,key=split_data.authority_key())
        hashes=dict(inventory=digest(snapshot.inventory),consent=digest(snapshot.consent),split=digest(snapshot.split['receipt']),annotations=snapshot.annotations_sha256,prompt=snapshot.prompt_sha256,review=snapshot.review_sha256)
    else:hashes={}
    token=secrets.token_hex(32);key=secrets.token_bytes(32);owned=False
    output=private_output(directory,root)
    try:
        output.parent.mkdir(parents=True,exist_ok=True);output.mkdir(mode=0o700);owned=True
        with (output/'.owner').open('x',encoding='ascii') as out:out.write(token)
        private_paths.verify(output,owner_token=token)
        with (output/'.authority').open('xb') as out:out.write(key)
        if os.name!='nt':os.chmod(output/'.authority',0o600)
        portable_source.command(root,['bundle','create',str(output/'source.bundle'),'HEAD'])
        base=read(root/'training/baseline/qwen-stock-v1.json') if hashes else None
        model=dict(model_id=base['model_id'],revision=base['revision']) if base else dict(model_id='fdec-technical-random-qwen3',revision='numeric-only-no-publisher-tensors')
        manifest=dict(schema='fdec-mlx-handoff/v1',task_id=TASK_ID,purpose=purpose,source=source,source_bundle=file_identity(output/'source.bundle'),origin=dict(platform=sys.platform,architecture=platform.machine()),config=config,model=model,runtime_profile_sha256=digest(profile),input_manifest_hashes=hashes,source_license_state='admitted-current-private-inputs' if hashes else 'insufficient_approved_data; numeric-only scope',authority_sha256=hashlib.sha256(key).hexdigest(),model_weights_publicly_approved=False,stage='awaiting-explicit-owner-transition',task_state_at_prepare='InProgress',restart_predicate='exact clean source; explicit owner confirmation; audited Apple runtime; independently admitted data for actual training',artifact_destination='private verified return bundle; never public Git',resources=dict(preferred_hardware='Apple M4 / 32 GB',minimum_memory_gib=24,minimum_free_disk_gib=12,estimated_free_disk_gib=20,estimates_are_acceptance_limits_not_measured_throughput=True))
        write(output/'manifest.json',manifest)
        write(output/'receipt.json',dict(schema='fdec-mlx-handoff-receipt/v1',manifest_sha256=digest(manifest),hmac_sha256=signature(manifest,key,b'fdec-mlx-handoff/v1\0')))
        portable_source.verify(source,root=root)
        return dict(handoff_sha256=digest(manifest),source=source,purpose=purpose,owner_confirmation_required=True,actual_apple_execution=False,actual_email_training=False,notice=NOTICE if hashes else 'Technical numerical MLX smoke check is ready for the MacBook Air M4. Actual email training is blocked: insufficient_approved_data.')
    except Exception:
        if owned:remove_owned(output,token)
        raise TrainerError('handoff_not_committed') from None


class Handoff:
    def __init__(self,directory,*,root=ROOT):
        self.root=Path(root);self.directory=reject_links(directory);private_paths.verify(self.directory);self.manifest=read(self.directory/'manifest.json')
        if {p.name for p in self.directory.iterdir()}!={'.owner','.authority','source.bundle','manifest.json','receipt.json'}:raise TrainerError('handoff_inventory_changed')
        with reject_links(self.directory/'.authority').open('rb') as source:self.key=source.read(33)
        if len(self.key)!=32 or self.manifest.get('schema')!='fdec-mlx-handoff/v1' or self.manifest.get('task_id')!=TASK_ID or hashlib.sha256(self.key).hexdigest()!=self.manifest.get('authority_sha256') or self.manifest.get('model_weights_publicly_approved') is not False:raise TrainerError('handoff_identity_invalid')
        receipt=read(self.directory/'receipt.json')
        self.sha256=digest(self.manifest)
        if not isinstance(receipt,dict) or set(receipt)!={'schema','manifest_sha256','hmac_sha256'} or receipt['schema']!='fdec-mlx-handoff-receipt/v1' or receipt['manifest_sha256']!=self.sha256 or not isinstance(receipt['hmac_sha256'],str) or not hmac.compare_digest(receipt['hmac_sha256'],signature(self.manifest,self.key,b'fdec-mlx-handoff/v1\0')):raise TrainerError('handoff_receipt_rejected')
        if file_identity(self.directory/'source.bundle')!=self.manifest['source_bundle']:raise TrainerError('source_bundle_changed')
        self.approval_sha256=None

    def authorize(self,purpose,*,source=True):
        if purpose!=self.manifest['purpose']:raise TrainerError('handoff_scope_mismatch')
        if source:portable_source.verify(self.manifest['source'],root=self.root)
        if digest(mac_profile(self.root))!=self.manifest['runtime_profile_sha256']:raise TrainerError('handoff_runtime_profile_changed')
        raw=os.environ.get('FDEC_OWNER_CONFIRMATION_FILE','')
        if not raw:raise TrainerError('explicit_owner_transition_missing')
        path=reject_links(raw).resolve()
        if not path.is_file():raise TrainerError('explicit_owner_transition_missing')
        # This is an externally protected activation anchor, never a file that a
        # corpus/source checkout can provide. No CLI creates or signs approval.
        if portable_source.command(path.parent,['rev-parse','--show-toplevel'],check=False).returncode==0:raise TrainerError('owner_confirmation_must_be_outside_git')
        private_paths.verify(path.parent)
        try:approval=read(path,16000)
        except Exception:raise TrainerError('owner_transition_unavailable') from None
        required={'schema','source_sha','handoff_sha256','scope','confirmation','confirmed_at'}
        if set(approval)!=required or approval['schema']!='fdec-owner-transition/v1' or approval['source_sha']!=self.manifest['source']['source_sha'] or approval['handoff_sha256']!=self.sha256 or approval['scope']!=purpose or approval['confirmation']!='explicit-project-owner-device-transition':raise TrainerError('owner_transition_not_bound')
        from datetime import datetime,timezone
        try:
            confirmed=datetime.fromisoformat(approval['confirmed_at'].replace('Z','+00:00'))
            if confirmed.tzinfo is None or confirmed>datetime.now(timezone.utc):raise ValueError()
        except Exception:raise TrainerError('owner_transition_time_invalid') from None
        current=digest(approval)
        if self.approval_sha256 is not None and current!=self.approval_sha256:raise TrainerError('owner_transition_changed')
        self.approval_sha256=current
        return approval


RETURN_FILES=frozenset(('checkpoint/.owner','checkpoint/state.safetensors','checkpoint/metadata.json','checkpoint/receipt.json','adapter/adapter_model.safetensors','adapter/adapter_config.json','runtime-proof.json','evaluation/report.json','evaluation/probe.safetensors','evaluation/receipt.json'))


def create_return(directory,*,handoff,report,artifacts):
    """Only internal actual-engine producers call this; no arbitrary-sign CLI."""
    handoff.authorize(handoff.manifest['purpose'])
    if set(artifacts)-RETURN_FILES or not {'checkpoint/state.safetensors','checkpoint/metadata.json','checkpoint/receipt.json','checkpoint/.owner'}<=set(artifacts):raise TrainerError('return_artifact_scope_invalid')
    output=private_output(directory,handoff.root);token=secrets.token_hex(32);owned=False
    try:
        output.parent.mkdir(parents=True,exist_ok=True);output.mkdir(mode=0o700);owned=True;(output/'.owner').write_text(token,encoding='ascii');private_paths.verify(output,owner_token=token)
        inventory=[]
        for relative,path in sorted(artifacts.items()):
            path=reject_links(path);destination=output/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,destination)
            inventory.append(dict(path=relative,**file_identity(destination)))
        manifest=dict(schema='fdec-mlx-return/v1',handoff_sha256=handoff.sha256,source=handoff.manifest['source'],purpose=handoff.manifest['purpose'],owner_confirmation_sha256=handoff.approval_sha256,report=report,files=inventory,public_weight_permission=False)
        write(output/'manifest.json',manifest)
        write(output/'receipt.json',dict(schema='fdec-mlx-return-receipt/v1',manifest_sha256=digest(manifest),hmac_sha256=signature(manifest,handoff.key,b'fdec-mlx-return/v1\0')))
        handoff.authorize(handoff.manifest['purpose'])
        return dict(bundle_sha256=digest(manifest),transfer_performed=False,return_notice_allowed=False,actual_email_training=False if handoff.manifest['purpose']=='numeric-smoke' else True)
    except Exception:
        if owned:remove_owned(output,token)
        raise TrainerError('return_bundle_not_committed') from None


def verify_return(directory,*,handoff,actual_arguments=None):
    handoff.authorize(handoff.manifest['purpose'])
    origin=handoff.manifest['origin']
    if sys.platform!=origin['platform'] or platform.machine()!=origin['architecture']:raise TrainerError('return_requires_original_environment_class')
    directory=reject_links(directory);private_paths.verify(directory);manifest=read(directory/'manifest.json');receipt=read(directory/'receipt.json')
    if not isinstance(receipt,dict) or set(receipt)!={'schema','manifest_sha256','hmac_sha256'} or receipt['schema']!='fdec-mlx-return-receipt/v1' or receipt['manifest_sha256']!=digest(manifest) or not isinstance(receipt['hmac_sha256'],str) or not hmac.compare_digest(receipt['hmac_sha256'],signature(manifest,handoff.key,b'fdec-mlx-return/v1\0')):raise TrainerError('return_receipt_rejected')
    if manifest.get('schema')!='fdec-mlx-return/v1' or manifest.get('source')!=handoff.manifest['source'] or manifest.get('handoff_sha256')!=handoff.sha256 or manifest.get('owner_confirmation_sha256')!=handoff.approval_sha256 or manifest.get('purpose')!=handoff.manifest['purpose'] or manifest.get('public_weight_permission') is not False:raise TrainerError('return_context_changed')
    names=set()
    for row in manifest['files']:
        name=row['path']
        if set(row)!={'path','sha256','size'} or name not in RETURN_FILES or name in names or file_identity(directory/name)!={k:row[k] for k in ('sha256','size')}:raise TrainerError('return_artifact_changed')
        names.add(name)
    actual={p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    for path in directory.rglob('*'):reject_links(path)
    if actual!=names|{'.owner','manifest.json','receipt.json'}:raise TrainerError('return_inventory_changed')
    if not {'checkpoint/state.safetensors','checkpoint/metadata.json','checkpoint/receipt.json','checkpoint/.owner'}<=names:raise TrainerError('return_checkpoint_missing')
    report=manifest['report']
    if handoff.manifest['purpose']=='actual-training':
        required={'adapter/adapter_model.safetensors','adapter/adapter_config.json','evaluation/report.json','evaluation/probe.safetensors','evaluation/receipt.json'}
        if report.get('schema')!='fdec-mlx-trained-return/v1' or report.get('simulation') is not False or report.get('actual_apple_execution') is not True or report.get('checkpoint_complete') is not True or not required<=names:raise TrainerError('actual_training_return_incomplete')
        from mlx_return_training import verify_actual
        return verify_actual(directory,authorization=handoff,args=actual_arguments)
    if report.get('schema')!='fdec-mlx-numeric-smoke/v1' or report.get('result')!='PASS' or report.get('checkpoint_resume_exact') is not True:raise TrainerError('verified_return_producer_unsupported')
    # Decode the actual authenticated native state on the receiving workstation;
    # no MLX or PyTorch import is required for this portable numerical check.
    import checkpoints,mlx_codec
    context=read(directory/'checkpoint/metadata.json')['context']
    step,state=checkpoints.load(directory/'checkpoint',context=context,key=handoff.key,reader=lambda raw:mlx_codec.decode(raw,from_numpy=lambda value:value),current_check=lambda:handoff.authorize(handoff.manifest['purpose'],source=False))
    if step!=4 or context.get('schema')!='fdec-mlx-smoke-context/v1' or context.get('handoff_sha256')!=handoff.sha256 or state.get('schema')!='fdec-mlx-state/v1':raise TrainerError('returned_native_checkpoint_invalid')
    if not {'adapter/adapter_model.safetensors','adapter/adapter_config.json'}<=names:raise TrainerError('returned_peft_export_missing')
    import mlx_export_adapter
    import numpy as np
    from safetensors.numpy import load_file
    expected=mlx_export_adapter.tensors(state['adapter'],rank=context['config']['rank'])
    exported=load_file(str(directory/'adapter/adapter_model.safetensors'))
    if set(expected)!=set(exported) or any(not np.array_equal(value,exported[name]) for name,value in expected.items()):raise TrainerError('returned_peft_export_mismatch')
    if read(directory/'adapter/adapter_config.json')!=mlx_export_adapter.configuration(context['config'],handoff.manifest['model']['model_id'],handoff.manifest['model']['revision']):raise TrainerError('returned_peft_config_mismatch')
    # Numeric smoke is not actual email training/evaluation or GGUF clearance.
    # The final training notice is deliberately unavailable on this path.
    return dict(received_artifacts_verified=True,native_checkpoint_decoded=True,actual_apple_execution=report.get('actual_apple_execution') is True and report.get('simulation') is False,actual_email_training=False,training_return_complete=False,public_weight_permission=False,return_notice=None,remaining=['independent-approved-training-data','actual-MLX-training-evaluation','verified-export-compatibility'])
