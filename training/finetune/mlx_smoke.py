"""Actual owner-confirmed Apple numerical LoRA/checkpoint smoke, never emails."""
from pathlib import Path
import tempfile
import time

from trainer_config import TrainerError
from mlx_engine import MLXEngine,runtime
from local_model import quiet_runtime
import checkpoints
import mlx_handoff as handoff
import mlx_export_adapter


def run(*,opt_in=False,handoff_dir,output_dir):
    if opt_in is not True:raise TrainerError('explicit_opt_in_required')
    authorization=handoff.Handoff(handoff_dir)
    with quiet_runtime():
        mx,info=runtime(authorization,'numeric-smoke')
        from mlx_lm.models.qwen3 import Model,ModelArgs
        from mlx.utils import tree_flatten
        import numpy as np
        config=dict(authorization.manifest['config'],max_steps=4,gradient_accumulation=1,rank=2,alpha=4,max_sequence_tokens=128,checkpoint_interval=2)
        def fresh():
            mx.random.seed(config['seed'])
            engine=MLXEngine.__new__(MLXEngine)
            engine.config,engine.mx,engine.handoff=config,mx,authorization
            engine.model=Model(ModelArgs(model_type='qwen3',hidden_size=32,num_hidden_layers=1,intermediate_size=64,num_attention_heads=4,rms_norm_eps=1e-6,vocab_size=128,num_key_value_heads=2,max_position_embeddings=128,head_dim=8,tie_word_embeddings=True,rope_theta=10000.0))
            engine.setup_optimizer()
            return engine
        batch=[([int(value) for value in np.random.default_rng(104729).integers(3,128,32)],None)]
        batch=[(batch[0][0],batch[0][0])]
        def advance(engine):
            # Exercise evolving global RNG, so a broken restore cannot pass just
            # because dropout is zero and the key never changed after init.
            mx.eval(mx.random.uniform(shape=(1,)))
            engine.update(batch,lambda:authorization.authorize('numeric-smoke',source=False))
        def equal(left,right):
            if isinstance(left,mx.array):return isinstance(right,mx.array) and left.dtype==right.dtype and left.shape==right.shape and bool(mx.array_equal(left,right).item())
            if isinstance(left,dict):return isinstance(right,dict) and set(left)==set(right) and all(equal(left[k],right[k]) for k in left)
            if isinstance(left,(list,tuple)):return type(left) is type(right) and len(left)==len(right) and all(equal(a,b) for a,b in zip(left,right))
            return left==right
        start=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='fdec-mlx-smoke-') as name:
            stage=Path(name).resolve()
            if not stage.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not stage.name.startswith('fdec-mlx-smoke-') or stage.is_symlink() or stage.is_junction():raise TrainerError('unsafe_mlx_smoke_staging')
            whole=fresh();initial=whole.state()['adapter']
            frozen={key:mx.array(value) for key,value in tree_flatten(whole.model.parameters()) if key not in initial}
            for _ in range(4):advance(whole)
            expected=whole.state()
            if equal(initial,expected['adapter']) or any(not equal(value,dict(tree_flatten(whole.model.parameters()))[key]) for key,value in frozen.items()):raise TrainerError('mlx_smoke_parameter_mutation_invalid')
            interrupted=fresh()
            for _ in range(2):advance(interrupted)
            context=dict(schema='fdec-mlx-smoke-context/v1',config=config,handoff_sha256=authorization.sha256,source=authorization.manifest['source'],runtime=info)
            check=lambda:authorization.authorize('numeric-smoke',source=False)
            checkpoints.save(stage/'interrupted',state=interrupted.state(),context=context,step=2,key=authorization.key,writer=interrupted.write,current_check=check)
            resumed=fresh()
            step,state=checkpoints.load(stage/'interrupted',context=context,key=authorization.key,reader=resumed.read,current_check=check)
            if step!=2:raise TrainerError('mlx_smoke_checkpoint_cursor_invalid')
            resumed.restore(state);resumed.validate_cursor(step)
            for _ in range(2):advance(resumed)
            if not equal(expected,resumed.state()):raise TrainerError('mlx_smoke_resume_not_exact')
            checkpoints.save(stage/'checkpoint',state=resumed.state(),context=context,step=4,key=authorization.key,writer=resumed.write,current_check=check)
            converted=mlx_export_adapter.write(stage/'adapter',adapter={key:np.array(value) for key,value in resumed.state()['adapter'].items()},config=config,model_id='fdec-technical-random-qwen3',revision='numeric-only-no-publisher-tensors')
            report=dict(schema='fdec-mlx-numeric-smoke/v1',result='PASS',simulation=False,actual_apple_execution=True,actual_email_training=False,stock_weights_downloaded=False,steps_per_path=4,checkpoint_resume_exact=True,optimizer_rng_exact=True,adapter_updated=True,frozen_base_unchanged=True,runtime=info,elapsed_seconds=time.monotonic()-start,export=converted)
            handoff.write(stage/'runtime-proof.json',report)
            artifacts={relative:stage/relative for relative in ('checkpoint/.owner','checkpoint/state.safetensors','checkpoint/metadata.json','checkpoint/receipt.json','adapter/adapter_model.safetensors','adapter/adapter_config.json','runtime-proof.json')}
            result=handoff.create_return(output_dir,handoff=authorization,report=report,artifacts=artifacts)
    return dict(**result,actual_apple_execution=True,checkpoint_resume_exact=True,public_weight_permission=False)
