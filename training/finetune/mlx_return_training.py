"""Private actual-training collection and primary-side verified GGUF return."""
import hmac
from pathlib import Path
import shutil
import sys
import tempfile

from trainer_config import ROOT,TrainerError,read as read_config
import checkpoints,mlx_codec,mlx_export_adapter
import mlx_handoff as handoff
import private_paths


def evaluation(directory,authorization):
    directory=Path(directory);receipt=handoff.read(directory/'receipt.json')
    required={'schema','files','hmac_sha256'}
    if set(receipt)!=required or receipt['schema']!='fdec-mlx-evaluation-receipt/v1' or set(receipt['files'])!={'report.json','probe.safetensors'}:raise TrainerError('mlx_evaluation_receipt_invalid')
    body={k:v for k,v in receipt.items() if k!='hmac_sha256'}
    if not hmac.compare_digest(receipt['hmac_sha256'],handoff.signature(body,authorization.key,b'fdec-mlx-evaluation/v1\0')):raise TrainerError('mlx_evaluation_receipt_untrusted')
    for name,identity in receipt['files'].items():
        if handoff.file_identity(directory/name)!=identity:raise TrainerError('mlx_evaluation_artifact_changed')
    report=handoff.read(directory/'report.json')
    if report.get('schema')!='fdec-mlx-evaluation/v1' or report.get('handoff_sha256')!=authorization.sha256 or report.get('actual_apple_execution') is not True or report.get('actual_model_executed') is not True or report.get('public_artifact_release_approved') is not False:raise TrainerError('actual_mlx_evaluation_required')
    return report


def current_inputs(args,authorization):
    import training_inputs,split_data
    from admission import admit as admit_test
    from mlx_evaluate import input_arguments
    key=split_data.authority_key()
    training=training_inputs.admit(**input_arguments(args,training=True),key=key)
    gold=admit_test(**input_arguments(args,training=False),key=key)
    expected=dict(inventory=split_data.inventory_digest(training.inventory),consent=split_data.digest(training.consent),split=split_data.digest(training.split['receipt']),annotations=training.annotations_sha256,prompt=training.prompt_sha256,review=training.review_sha256)
    if expected!=authorization.manifest['input_manifest_hashes']:raise TrainerError('mlx_return_training_inputs_changed')
    return training,gold,key


def source_provenance(inventory):
    """Keep the resolved source notices with the private export."""
    from collections import Counter

    import split_data
    import training_boundary

    counts = Counter(split_data.canonical_json(row["source"]) for row in split_data.inventory_rows(inventory))
    sources = []
    for encoded, count in sorted(counts.items()):
        identity = split_data.strict_json(encoded)
        admission = training_boundary.assert_training_source(identity, purpose="commercial_training")
        rights = admission["descriptor"]
        if admission.get("schema") == "fdec-independent-source-admission/v2" and admission.get("requires_origin_projection") is True:
            attribution = admission.get("attribution")
            audit_sha256 = admission.get("origin_policy_sha256")
        else:
            attribution = rights.get("attribution")
            audit_sha256 = rights.get("audit_sha256")
        if not attribution or not split_data.is_hash(audit_sha256):
            raise TrainerError("mlx_return_source_provenance_incomplete")
        sources.append(dict(identity=identity, inventory_records=count, training_license=rights["license"],
                            attribution=attribution, source_audit_sha256=audit_sha256,
                            public_weight_rights="separate-review-required"))
    return sources


def check_evaluation(report,gold,metadata,context):
    import split_data
    expected=dict(inventory_sha256=split_data.inventory_digest(gold.inventory),consent_sha256=split_data.digest(gold.consent),split_receipt_sha256=split_data.digest(gold.split['receipt']),annotations_sha256=gold.annotations_sha256,review_sha256=gold.review_sha256,context_sha256=handoff.digest(context),checkpoint_metadata=metadata)
    if any(report.get(k)!=value for k,value in expected.items()):raise TrainerError('mlx_return_evaluation_not_current')


def collect(args):
    if not args.opt_in:raise TrainerError('explicit_opt_in_required')
    from mlx_evaluate import restore_actual
    from local_model import quiet_runtime
    authorization=handoff.Handoff(args.handoff_dir);authorization.authorize('actual-training')
    report=evaluation(args.evaluation_dir,authorization)
    engine,training,context,current=restore_actual(args)
    _,gold,_=current_inputs(args,authorization)
    check_evaluation(report,gold,handoff.file_identity(Path(args.checkpoint)/'metadata.json'),context)
    with quiet_runtime(),tempfile.TemporaryDirectory(prefix='fdec-mlx-collect-') as name:
        stage=Path(name).resolve()
        if not stage.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not stage.name.startswith('fdec-mlx-collect-') or stage.is_symlink() or stage.is_junction():raise TrainerError('unsafe_mlx_collection_staging')
        import numpy as np
        export=mlx_export_adapter.write(stage/'adapter',adapter={k:np.array(v) for k,v in engine.state()['adapter'].items()},config=engine.config,model_id=engine.profile['model_id'],revision=engine.profile['revision'])
        artifacts={relative:Path(args.checkpoint)/relative.split('/')[-1] for relative in ('checkpoint/.owner','checkpoint/state.safetensors','checkpoint/metadata.json','checkpoint/receipt.json')}
        artifacts.update({relative:Path(args.evaluation_dir)/relative.split('/')[-1] for relative in ('evaluation/report.json','evaluation/probe.safetensors','evaluation/receipt.json')})
        artifacts.update({relative:stage/relative for relative in ('adapter/adapter_model.safetensors','adapter/adapter_config.json')})
        result=handoff.create_return(args.output_dir,handoff=authorization,report=dict(schema='fdec-mlx-trained-return/v1',simulation=False,actual_apple_execution=True,actual_email_training=True,checkpoint_complete=True,evaluation_report_sha256=handoff.file_identity(Path(args.evaluation_dir)/'report.json')['sha256'],export=export,gguf_runtime_verified=False),artifacts=artifacts)
        current()
    return dict(**result,gguf_runtime_verified=False,conversion_and_primary_verification_required=True)


def verify_actual(directory,*,authorization,args):
    """Runs on the original host; never imports MLX or forges a Torch checkpoint."""
    if args is None or not getattr(args,'export_dir',None) or not getattr(args,'model_dir',None) or not getattr(args,'llama_cpp_dir',None):raise TrainerError('actual_return_requires_verified_private_export')
    from local_model import verify_snapshot
    import train,training_inputs,split_data
    from admission import recheck as recheck_test
    training,gold,key=current_inputs(args,authorization)
    config=read_config(args.config);profile=verify_snapshot(args.model_dir)
    metadata=handoff.read(Path(directory)/'checkpoint/metadata.json')
    context=metadata['context']
    expected=train.run_context(config,type('RecordedMLXIdentity',(),{'identity':context['model']})(),training,'mlx')
    model=context.get('model',{})
    if context!=expected or model.get('engine')!='mlx' or model.get('model_id')!=profile['model_id'] or model.get('revision')!=profile['revision'] or model.get('dtype')!='float32-base-and-adapter' or model.get('runtime',{}).get('profile_sha256')!=authorization.manifest['runtime_profile_sha256']:raise TrainerError('returned_mlx_training_context_invalid')
    def current():
        training_inputs.recheck(training,key=key);recheck_test(gold,key=key);authorization.authorize('actual-training',source=False)
    step,state=checkpoints.load(Path(directory)/'checkpoint',context=context,key=key,reader=lambda raw:mlx_codec.decode(raw,from_numpy=lambda value:value),current_check=current)
    if step!=config['max_steps'] or state.get('schema')!='fdec-mlx-state/v1' or int(state['optimizer']['step'])!=step:raise TrainerError('returned_mlx_training_incomplete')
    report=evaluation(Path(directory)/'evaluation',authorization)
    check_evaluation(report,gold,handoff.file_identity(Path(directory)/'checkpoint/metadata.json'),context)
    converted=mlx_export_adapter.tensors(state['adapter'],rank=config['rank'])
    from safetensors.numpy import load_file
    import numpy as np
    exported=load_file(str(Path(directory)/'adapter/adapter_model.safetensors'))
    if set(converted)!=set(exported) or any(not np.array_equal(value,exported[name]) for name,value in converted.items()):raise TrainerError('mlx_return_peft_tensors_differ')
    if handoff.read(Path(directory)/'adapter/adapter_config.json')!=mlx_export_adapter.configuration(config,profile['model_id'],profile['revision']):raise TrainerError('mlx_return_peft_config_changed')
    sys.path.append(str(ROOT/'training/export'))
    from common import candidate,VARIANTS,verify_candidate,write_json,digest_file
    from exporter import converter_checkout,convert,sbom
    from lineage import provenance
    from formats import inspect_gguf
    import runtime_load
    checkout,converter=converter_checkout(args.llama_cpp_dir)
    import importlib.metadata
    for name,version in (('torch','2.15.0'),('transformers','5.23.0'),('peft','0.22.0')):
        if importlib.metadata.version(name)!=version:raise TrainerError('primary_mlx_export_runtime_unverified')
    with __import__('local_model').quiet_runtime():
        import torch
        from transformers import AutoModelForCausalLM
        from peft import PeftModel
        model=PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(str(args.model_dir),local_files_only=True,trust_remote_code=False,use_safetensors=True,dtype=torch.float32,attn_implementation='eager'),str(Path(directory)/'adapter'),local_files_only=True).eval()
        probe=torch.tensor([[1,2,3]])
        with torch.inference_mode():actual=model(input_ids=probe).logits.cpu().numpy()
        reference=load_file(str(Path(directory)/'evaluation/probe.safetensors'))['logits']
        if actual.shape!=reference.shape or not np.isfinite(reference).all() or not np.allclose(actual,reference,atol=1e-4,rtol=1e-4):raise TrainerError('mlx_to_peft_numeric_probe_mismatch')
        export_context=dict(kind='fdec-trained-export/v1',variants=list(VARIANTS),base_model_sha256=next(row['digest'] for row in profile['files'] if row['path']=='model.safetensors'),training_provenance=provenance(training),checkpoint_metadata_sha256=handoff.file_identity(Path(directory)/'checkpoint/metadata.json')['sha256'],converter_revision=converter['llama_cpp_revision'],model_runtime_load_verified=False,producer_engine='mlx',handoff_sha256=authorization.sha256)
        def build(output):
            private_paths.verify(output,owner_token=(output/'.owner').read_text(encoding='ascii'))
            with tempfile.TemporaryDirectory(prefix='fdec-mlx-export-',dir=output.parent) as name:
                stage=Path(name).resolve()
                if not stage.is_relative_to(output.parent.resolve()) or not stage.name.startswith('fdec-mlx-export-') or stage.is_symlink() or stage.is_junction():raise TrainerError('unsafe_mlx_export_staging')
                executable,built=runtime_load.build(checkout,stage/'runtime',converter['llama_cpp_revision']);converter_checkout(checkout)
                shutil.copytree(Path(directory)/'adapter',output/'adapter')
                tokenizer=output/'tokenizer';tokenizer.mkdir()
                for name in ('tokenizer.json','tokenizer_config.json','vocab.json','merges.txt','config.json','generation_config.json','LICENSE'):shutil.copyfile(Path(args.model_dir)/name,tokenizer/name)
                convert(checkout,'convert_lora_to_gguf.py',output/'adapter',output/'adapter-f16.gguf',base=Path(args.model_dir))
                convert(checkout,'convert_hf_to_gguf.py',Path(args.model_dir),output/'base-f16.gguf')
                merged=model.merge_and_unload(safe_merge=True).eval()
                with torch.inference_mode():merged_probe=merged(input_ids=probe).logits.cpu().numpy()
                if not np.allclose(actual,merged_probe,atol=1e-4,rtol=1e-4):raise TrainerError('mlx_peft_merged_numeric_probe_mismatch')
                merged_dir=stage/'merged';merged.save_pretrained(str(merged_dir),safe_serialization=True)
                for name in ('tokenizer.json','tokenizer_config.json','vocab.json','merges.txt'):shutil.copyfile(Path(args.model_dir)/name,merged_dir/name)
                convert(checkout,'convert_hf_to_gguf.py',merged_dir,output/'classifier-f16.gguf')
                verification=dict(mlx_peft_numeric_probe=True,merged_numeric_probe=True,adapter=inspect_gguf(output/'adapter-f16.gguf',expected_adapter=True),merged=inspect_gguf(output/'classifier-f16.gguf',expected_adapter=False),runtime=runtime_load.compare(output,executable,built,current))
                converter_checkout(checkout)
                export_context['model_runtime_load_verified']=True
                write_json(output/'verification.json',verification)
                write_json(output/'dataset-manifest.json',dict(schema='fdec-export-datasets/v1',**provenance(training),sources=source_provenance(training.inventory),contains_email_or_personal_data=False,public_weight_rights='separate-review-required'))
                write_json(output/'evaluation.json',report)
                (output/'README.md').write_text('# Private MLX-trained candidate\n\nBase: '+profile['model_id']+' at '+profile['revision']+'.\n\nNo public weight permission. See measured evaluation.json; no calibrated-probability or 119-language reliability claim.\n',encoding='utf-8')
                write_json(output/'handoff-completion.json',dict(schema='fdec-post-mac-completion/v1',handoff_sha256=authorization.sha256,source=authorization.manifest['source'],checkpoint_metadata_sha256=export_context['checkpoint_metadata_sha256'],evaluation_sha256=handoff.file_identity(Path(directory)/'evaluation/report.json')['sha256'],private_artifacts_verified=True,model_runtime_verified=True,public_weight_permission=False,next_step='Resume original workstation; preserve unfinished D003 baseline/CUDA/gate/review obligations'))
                write_json(output/'sbom.cdx.json',sbom(output))
        candidate(args.export_dir,build=build,context=export_context,current_check=current,key=key)
        verify_candidate(Path(args.export_dir),key=key);private_paths.verify(Path(args.export_dir));current();authorization.authorize('actual-training')
    return dict(received_artifacts_verified=True,native_checkpoint_decoded=True,actual_apple_execution=True,actual_email_training=True,training_return_complete=True,public_weight_permission=False,export_manifest_sha256=digest_file(Path(args.export_dir)/'manifest.json')['sha256'],return_notice=handoff.RETURN_NOTICE)
