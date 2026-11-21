"""Lazy owner-gated Apple MLX engine; no PyTorch dependency or remote loading."""
import importlib.metadata
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

from trainer_config import ROOT,TrainerError,TARGET_MODULES
for area in ('training/baseline','training/eval'):sys.path.append(str(ROOT/area))
from local_model import verify_snapshot,quiet_runtime
import mlx_codec
import mlx_handoff as handoff

TARGET_KEYS=['self_attn.'+name for name in TARGET_MODULES[:4]]+['mlp.'+name for name in TARGET_MODULES[4:]]


def hardware(*,require_power=True):
    if sys.platform!='darwin' or platform.machine()!='arm64':raise TrainerError('apple_silicon_host_required')
    def query(args):
        value=subprocess.run(args,capture_output=True,text=True,timeout=15)
        if value.returncode:raise TrainerError('apple_environment_inspection_failed')
        return value.stdout
    if not re.fullmatch(r'\d+\.\d+(?:\.\d+)?',platform.mac_ver()[0]) or int(platform.mac_ver()[0].split('.')[0])<15:raise TrainerError('macos15_or_newer_required')
    memory=int(query(['sysctl','-n','hw.memsize']).strip())
    brand=query(['sysctl','-n','machdep.cpu.brand_string']).strip()
    if not re.fullmatch(r'Apple M\d+(?: Pro| Max| Ultra)?',brand) or memory<24*1024**3 or shutil.disk_usage(ROOT).free<12*1024**3:raise TrainerError('insufficient_apple_resources')
    ac='AC Power' in query(['pmset','-g','batt'])
    thermal=query(['pmset','-g','therm'])
    restricted=bool(re.search(r'(?:CPU_Speed_Limit|CPU_Scheduler_Limit|GPU_Speed_Limit)\s*=\s*(?:[0-9]|[0-9][0-9])\b',thermal))
    if require_power and (not ac or restricted):raise TrainerError('apple_power_or_thermal_condition_unsuitable')
    return dict(hardware_class=brand,memory_bytes=memory,ac_power=ac,thermal_throttling_detected=restricted,os=platform.mac_ver()[0],architecture='arm64',python=platform.python_version())


def runtime(authorization,purpose):
    authorization.authorize(purpose)
    info=hardware()
    profile=handoff.mac_profile()
    if sys.version_info[:2]!=(3,14):raise TrainerError('audited_mlx_python314_required')
    try:
        if any(importlib.metadata.version(name)!=version for name,version in profile['packages'].items()):raise TrainerError('mlx_runtime_version_mismatch')
    except importlib.metadata.PackageNotFoundError:raise TrainerError('mlx_runtime_package_missing') from None
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    try:import mlx.core as mx
    except ImportError:raise TrainerError('mlx_backend_import_unavailable') from None
    if not mx.metal.is_available():raise TrainerError('apple_metal_backend_required')
    mx.set_default_device(mx.gpu)
    environment=sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions())
    return mx,dict(**info,packages=profile['packages'],profile_sha256=handoff.digest(profile),environment_sha256=handoff.digest(environment))


class MLXEngine:
    def __init__(self,model_dir,config,handoff_dir):
        self.handoff=handoff.Handoff(handoff_dir)
        self.config=config
        if self.handoff.manifest['config']!=config or config['backend']!='lora':raise TrainerError('mlx_handoff_config_mismatch')
        with quiet_runtime():
            self.mx,info=runtime(self.handoff,'actual-training')
            self.profile=verify_snapshot(model_dir)
            from mlx_lm.utils import load_model
            from transformers import AutoTokenizer
            self.mx.random.seed(config['seed'])
            self.model,_=load_model(Path(model_dir),lazy=False,strict=True,trust_remote_code=False)
            from mlx.utils import tree_map
            self.model.update(tree_map(lambda value:value.astype(self.mx.float32),self.model.parameters()))
            self.tokenizer=AutoTokenizer.from_pretrained(str(model_dir),local_files_only=True,trust_remote_code=False)
            self.setup_optimizer()
            verify_snapshot(model_dir)
        self.identity=dict(engine='mlx',model_id=self.profile['model_id'],revision=self.profile['revision'],backend='lora',runtime=info,targets=TARGET_MODULES,dtype='float32-base-and-adapter',optimizer='MLX-AdamW',batch_size=1,export_compatibility='native-MLX; PEFT/GGUF runtime verification required')

    def setup_optimizer(self):
        import mlx.nn as nn
        import mlx.optimizers as optim
        from mlx.utils import tree_flatten,tree_unflatten
        from mlx_lm.tuner.utils import linear_to_lora_layers
        self.model.freeze()
        linear_to_lora_layers(self.model,len(self.model.layers),dict(rank=self.config['rank'],scale=self.config['alpha']/self.config['rank'],dropout=0.0,keys=TARGET_KEYS))
        parameters=dict(tree_flatten(self.model.trainable_parameters()))
        expected=len(self.model.layers)*len(TARGET_KEYS)*2
        if len(parameters)!=expected or any(not re.fullmatch(r'model.layers.\d+.(?:self_attn|mlp).(?:q|k|v|o|gate|up|down)_proj.lora_[ab]',name) for name in parameters):raise TrainerError('unexpected_mlx_trainable_parameters')
        self.model.update(tree_unflatten({name:value.astype(self.mx.float32) for name,value in parameters.items()}))
        self.parameter_order=sorted(parameters)
        self.optimizer=optim.AdamW(learning_rate=self.config['learning_rate'],weight_decay=self.config['weight_decay'])
        self.optimizer.init(self.model.trainable_parameters())
        self.mx.eval(self.model.parameters(),self.optimizer.state)
        self.model.train()
        self.loss_and_grad=nn.value_and_grad(self.model,self.loss)

    def tokenize(self,system,subject,body,classification):
        import split_data as splits
        with quiet_runtime():
            messages=[dict(role='system',content=system),dict(role='user',content=splits.canonical_json(dict(subject=subject,body=body)))]
            prefix=self.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False)
            target=self.tokenizer.encode(splits.canonical_json(classification),add_special_tokens=False)
            eos=self.tokenizer.eos_token_id
            if not isinstance(prefix,list) or not prefix or not target or type(eos) is not int or len(prefix)+len(target)+1>self.config['max_sequence_tokens']:raise TrainerError('training_sequence_invalid_or_over_budget')
            return prefix+target+[eos],[-100]*len(prefix)+target+[eos]

    def loss(self,model,data,targets):
        import mlx.nn as nn
        mx=self.mx
        logits=model(data)[:,:-1,:];targets=targets[:,1:];mask=targets>=0
        count=mx.sum(mask)
        safe=mx.where(mask,targets,0)
        return mx.sum(nn.losses.cross_entropy(logits,safe,reduction='none')*mask)/count

    def update(self,batches,current_check):
        from mlx.utils import tree_map,tree_flatten
        with quiet_runtime():
            if len(batches)!=self.config['gradient_accumulation']:raise TrainerError('mlx_batch_count_mismatch')
            accumulated=None
            for data,targets in batches:
                if not isinstance(data,list) or not isinstance(targets,list) or len(data)!=len(targets) or not 2<=len(data)<=self.config['max_sequence_tokens'] or any(type(t) is not int or t<0 for t in data) or any(type(t) is not int or t<-100 or -100<t<0 for t in targets) or not any(t>=0 for t in targets[1:]):raise TrainerError('mlx_numeric_batch_invalid')
                current_check();self.handoff.authorize(self.handoff.manifest['purpose'],source=False)
                loss,grads=self.loss_and_grad(self.model,self.mx.array([data],dtype=self.mx.int32),self.mx.array([targets],dtype=self.mx.int32))
                self.mx.eval(loss,grads)
                if not bool(self.mx.isfinite(loss).item()):raise TrainerError('mlx_loss_not_finite')
                grads=tree_map(lambda value:value/len(batches),grads)
                accumulated=grads if accumulated is None else tree_map(lambda left,right:left+right,accumulated,grads)
            norm=self.mx.sqrt(sum(self.mx.sum(value*value) for _,value in tree_flatten(accumulated)))
            if not bool(self.mx.isfinite(norm).item()):raise TrainerError('mlx_gradients_not_finite')
            factor=self.mx.minimum(1.0,self.config['max_grad_norm']/(norm+1e-12))
            accumulated=tree_map(lambda value:value*factor,accumulated)
            current_check();self.handoff.authorize(self.handoff.manifest['purpose'],source=False)
            self.optimizer.update(self.model,accumulated)
            self.mx.eval(self.model.parameters(),self.optimizer.state)

    def state(self):
        from mlx.utils import tree_flatten,tree_map
        adapter=dict(tree_flatten(self.model.trainable_parameters()))
        state=dict(schema='fdec-mlx-state/v1',parameter_order=self.parameter_order,adapter=adapter,optimizer=self.optimizer.state,rng=self.mx.random.state[0])
        self.mx.eval(adapter,state['optimizer'],state['rng'])
        return tree_map(lambda value:self.mx.array(value) if isinstance(value,self.mx.array) else value,state)

    def restore(self,state):
        from mlx.utils import tree_flatten,tree_unflatten,tree_map
        mx=self.mx;actual=dict(tree_flatten(self.model.trainable_parameters()))
        if not isinstance(state,dict) or set(state)!={'schema','parameter_order','adapter','optimizer','rng'} or state['schema']!='fdec-mlx-state/v1' or state['parameter_order']!=self.parameter_order or set(state['adapter'])!=set(actual):raise TrainerError('mlx_training_state_incompatible')
        for name,value in state['adapter'].items():
            if value.shape!=actual[name].shape or value.dtype!=mx.float32 or not bool(mx.all(mx.isfinite(value)).item()):raise TrainerError('mlx_adapter_state_invalid')
        old=dict(tree_flatten(self.optimizer.state));new=dict(tree_flatten(state['optimizer']))
        if set(old)!=set(new):raise TrainerError('mlx_optimizer_layout_changed')
        for name,value in new.items():
            if hasattr(old[name],'shape'):
                if not hasattr(value,'shape') or value.shape!=old[name].shape or value.dtype!=old[name].dtype or not bool(mx.all(mx.isfinite(value)).item()):raise TrainerError('mlx_optimizer_tensor_invalid')
            elif type(value) is not type(old[name]):raise TrainerError('mlx_optimizer_scalar_invalid')
        key=state['rng']
        if key.shape!=(2,) or key.dtype!=mx.uint32:raise TrainerError('mlx_rng_state_invalid')
        # Pinned MLX 0.32.4 exposes a read-only RNG sentinel. Its documented
        # seed->key source maps uint64 to high/low uint32. Reconstruct that seed
        # and verify the exact restored key, rather than replacing the sentinel.
        seed=(int(key[0].item())<<32)|int(key[1].item())
        mx.random.seed(seed)
        if not bool(mx.array_equal(mx.random.state[0],key).item()):raise TrainerError('mlx_rng_restore_not_exact')
        self.model.update(tree_unflatten(state['adapter']));self.optimizer.state=state['optimizer']
        mx.eval(self.model.parameters(),self.optimizer.state)

    def write(self,state,path):
        import numpy as np
        mlx_codec.encode(state,path,to_numpy=np.array)

    def read(self,raw):return mlx_codec.decode(raw,from_numpy=self.mx.array)

    def validate_cursor(self,step):
        if int(self.optimizer.state['step'].item())!=step:raise TrainerError('mlx_optimizer_cursor_mismatch')
