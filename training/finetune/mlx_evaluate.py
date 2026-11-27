"""Admitted held-out MLX evaluation and numeric bridge probe; never log emails."""
from datetime import datetime,timezone
from pathlib import Path
import secrets
import sys

from trainer_config import ROOT,TrainerError,read as read_config
for area in ('training/eval','training/baseline'):sys.path.append(str(ROOT/area))
import training_inputs
import split_data as splits
from admission import admit as admit_test,recheck as recheck_test
from classification_metrics import measure
from prompt import messages,parse,PROMPT_SHA256,MAX_INPUT_TOKENS,MAX_NEW_TOKENS
from baseline_metrics import EvaluationError
from local_model import quiet_runtime
from ingest_dataset import private_output,remove_owned,reject_links
import checkpoints
import mlx_handoff as handoff


def input_arguments(args,*,training):
    common=dict(inventory_path=args.inventory,consent_path=args.consent,split_dir=args.split_dir,source_runs=args.source_run)
    if training:common.update(annotations_path=args.training_annotations,prompt_path=args.training_prompt)
    else:common.update(annotations_path=args.annotations)
    return common


def restore_actual(args):
    import train
    from mlx_engine import MLXEngine
    key=splits.authority_key();arguments=input_arguments(args,training=True)
    snapshot=training_inputs.admit(**arguments,key=key)
    config=read_config(args.config)
    authorization=handoff.Handoff(args.handoff_dir)
    expected=dict(inventory=splits.inventory_digest(snapshot.inventory),consent=splits.digest(snapshot.consent),split=splits.digest(snapshot.split['receipt']),annotations=snapshot.annotations_sha256,prompt=snapshot.prompt_sha256,review=snapshot.review_sha256)
    if authorization.manifest['input_manifest_hashes']!=expected:raise TrainerError('mlx_handoff_training_inputs_changed')
    engine=MLXEngine(reject_links(args.model_dir),config,args.handoff_dir)
    context=train.run_context(config,engine,snapshot,'mlx')
    def current():
        training_inputs.recheck(snapshot,key=key);engine.handoff.authorize('actual-training',source=False)
    step,state=checkpoints.load(args.checkpoint,context=context,key=key,reader=engine.read,current_check=current)
    if step!=config['max_steps']:raise TrainerError('actual_mlx_training_not_complete')
    engine.restore(state);engine.validate_cursor(step)
    return engine,snapshot,context,current


def run(args):
    if args.opt_in is not True:raise TrainerError('explicit_opt_in_required')
    key=splits.authority_key();gold_args=input_arguments(args,training=False)
    gold=admit_test(**gold_args,key=key)
    output=private_output(args.output_dir,ROOT)
    engine,training,context,current=restore_actual(args)
    predictions=[]
    with quiet_runtime():
        from mlx_lm.generate import stream_generate
        mx=engine.mx;engine.model.eval()
        for row in gold.gold:
            current();recheck_test(gold,key=key)
            prompt=engine.tokenizer.apply_chat_template(messages(*gold.texts[row['record_id']]),tokenize=True,add_generation_prompt=True,enable_thinking=False)
            if not 1<=len(prompt)<=MAX_INPUT_TOKENS:raise TrainerError('mlx_evaluation_input_budget_exceeded')
            segments=[];finish=None
            for generated in stream_generate(engine.model,engine.tokenizer,prompt=prompt,max_tokens=MAX_NEW_TOKENS,sampler=lambda logits:mx.argmax(logits,axis=-1)):
                segments.append(generated.text);finish=generated.finish_reason
            try:prediction=parse(''.join(segments)) if finish=='stop' else None
            except EvaluationError:prediction=None
            predictions.append(prediction)
        probe=mx.array([[1,2,3]],dtype=mx.int32);logits=engine.model(probe);mx.eval(logits)
        import numpy as np
        reference=np.array(logits,dtype=np.float32)
    if training_inputs.admit(**input_arguments(args,training=True),key=key)!=training or admit_test(**gold_args,key=key)!=gold:raise TrainerError('mlx_evaluation_inputs_changed')
    current();recheck_test(gold,key=key)
    report=dict(schema='fdec-mlx-evaluation/v1',scope='admitted-trained-MLX-held-out-model',actual_model_executed=True,actual_apple_execution=True,handoff_sha256=engine.handoff.sha256,created_at=datetime.now(timezone.utc).isoformat(),model=engine.identity,checkpoint_metadata=handoff.file_identity(Path(args.checkpoint)/'metadata.json'),context_sha256=handoff.digest(context),prompt_sha256=PROMPT_SHA256,inventory_sha256=splits.inventory_digest(gold.inventory),consent_sha256=splits.digest(gold.consent),split_receipt_sha256=splits.digest(gold.split['receipt']),annotations_sha256=gold.annotations_sha256,review_sha256=gold.review_sha256,metrics=measure(gold.gold,predictions),public_artifact_release_approved=False)
    owned=False;token=secrets.token_hex(32)
    try:
        output.parent.mkdir(parents=True,exist_ok=True);output.mkdir(mode=0o700);owned=True;(output/'.owner').write_text(token,encoding='ascii')
        import private_paths
        private_paths.verify(output,owner_token=token)
        from safetensors.numpy import save_file
        save_file({'logits':reference},str(output/'probe.safetensors'))
        handoff.write(output/'report.json',report)
        files={name:handoff.file_identity(output/name) for name in ('report.json','probe.safetensors')}
        receipt=dict(schema='fdec-mlx-evaluation-receipt/v1',files=files)
        receipt['hmac_sha256']=handoff.signature(receipt,engine.handoff.key,b'fdec-mlx-evaluation/v1\0')
        current();recheck_test(gold,key=key);engine.handoff.authorize('actual-training')
        handoff.write(output/'receipt.json',receipt)
        return dict(status='measured',rows=len(gold.gold),languages=len(report['metrics']['by_language']),actual_apple_execution=True,public_artifact_release_approved=False)
    except Exception:
        if owned:remove_owned(output,token)
        raise TrainerError('mlx_evaluation_not_committed') from None
