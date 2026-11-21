"""Private MLX->PEFT float32 tensor layout export, not GGUF/runtime clearance."""
import re
from trainer_config import TrainerError,TARGET_MODULES


def configuration(config,model_id,revision):
    return dict(peft_type='LORA',task_type='CAUSAL_LM',r=config['rank'],lora_alpha=config['alpha'],lora_dropout=0.0,bias='none',target_modules=TARGET_MODULES,base_model_name_or_path=model_id,revision=revision,inference_mode=True)


def tensors(adapter,*,rank):
    import numpy as np
    result={}
    layers=set()
    for name,value in adapter.items():
        match=re.fullmatch(r'model\.layers\.(\d+)\.(self_attn|mlp)\.(q|k|v|o|gate|up|down)_proj\.lora_([ab])',name)
        array=np.array(value,copy=True)
        if not match or array.dtype!=np.float32 or array.ndim!=2 or not np.isfinite(array).all() or array.shape[1 if match[4]=='a' else 0]!=rank:raise TrainerError('mlx_adapter_export_tensor_invalid')
        layers.add(int(match[1]))
        other=name[:-1]+('b' if match[4]=='a' else 'a')
        if other not in adapter:raise TrainerError('mlx_adapter_export_pair_missing')
        result['base_model.model.'+name[:-1]+match[4].upper()+'.weight']=array.T.copy()
    if not result:raise TrainerError('mlx_adapter_export_empty')
    expected={f'model.layers.{layer}.{("self_attn" if name in TARGET_MODULES[:4] else "mlp")}.{name}.lora_{side}' for layer in range(max(layers)+1) for name in TARGET_MODULES for side in ('a','b')}
    if set(adapter)!=expected:raise TrainerError('mlx_adapter_export_target_layout_changed')
    return result


def write(directory,*,adapter,config,model_id,revision):
    from safetensors.numpy import save_file,load_file
    import numpy as np
    from mlx_handoff import write as write_json
    directory.mkdir()
    converted=tensors(adapter,rank=config['rank'])
    save_file(converted,str(directory/'adapter_model.safetensors'))
    restored=load_file(str(directory/'adapter_model.safetensors'))
    if set(converted)!=set(restored) or any(not np.array_equal(value,restored[name]) for name,value in converted.items()):raise TrainerError('mlx_peft_safetensors_roundtrip_failed')
    write_json(directory/'adapter_config.json',configuration(config,model_id,revision))
    return dict(peft_float32_tensor_layout_verified=True,scale=config['alpha']/config['rank'],tensors=len(converted),full_model_runtime_or_gguf_verified=False,public_weight_permission=False)
