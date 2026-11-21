"""Bounded numerical safetensors tree; never pickle, email text or model code."""
import json
import math
import re

from trainer_config import TrainerError

MAX_LEAVES=10000
MAX_DEPTH=24
DTYPES=frozenset(('float16','float32','int32','int64','uint32','uint64','bool'))


def encode(value, path, *, to_numpy):
    import numpy as np
    from safetensors.numpy import save
    arrays={}
    count=0
    def pack(item,depth):
        nonlocal count
        count+=1
        if depth>MAX_DEPTH or count>MAX_LEAVES:raise TrainerError('mlx_state_tree_limit')
        if item is None or type(item) in (bool,int,float,str):
            if type(item) is float and not math.isfinite(item) or type(item) is str and len(item)>256:raise TrainerError('mlx_state_scalar_invalid')
            return ['scalar',item]
        if isinstance(item,dict):
            if any(type(key) is not str or not re.fullmatch(r'[A-Za-z0-9_.-]{1,256}',key) for key in item):raise TrainerError('mlx_state_key_invalid')
            return ['dict',[[key,pack(item[key],depth+1)] for key in sorted(item)]]
        if type(item) in (list,tuple):return ['tuple' if type(item) is tuple else 'list',[pack(entry,depth+1) for entry in item]]
        data=np.array(to_numpy(item),copy=True)
        if data.dtype.name not in DTYPES or data.ndim>4 or data.size>64_000_000 or not np.isfinite(data).all():raise TrainerError('mlx_state_tensor_invalid')
        name=f'tensor_{len(arrays):05d}';arrays[name]=data
        return ['array',name]
    layout=pack(value,0)
    metadata=json.dumps(layout,separators=(',',':'),ensure_ascii=True)
    if len(metadata)>500000:raise TrainerError('mlx_state_layout_limit')
    raw=save(arrays,metadata={'fdec-layout-v1':metadata})
    if len(raw)>512_000_000:raise TrainerError('mlx_state_size_limit')
    with path.open('xb') as out:out.write(raw)


def decode(raw, *, from_numpy):
    import numpy as np
    from safetensors.numpy import load
    from ingest_dataset import strict_json
    try:
        if len(raw)>512_000_000 or len(raw)<10:raise ValueError()
        size=int.from_bytes(raw[:8],'little')
        if not 2<=size<=1_000_000 or 8+size>len(raw):raise ValueError()
        header=strict_json(raw[8:8+size].decode())
        metadata=header.get('__metadata__')
        if not isinstance(metadata,dict) or set(metadata)!={'fdec-layout-v1'} or len(metadata['fdec-layout-v1'])>500000:raise ValueError()
        layout=strict_json(metadata['fdec-layout-v1'])
        arrays=load(raw);used=set();count=0
        def unpack(node,depth):
            nonlocal count
            count+=1
            if count>MAX_LEAVES or depth>MAX_DEPTH or not isinstance(node,list) or len(node)!=2:raise ValueError()
            kind,payload=node
            if kind=='scalar':
                if payload is not None and type(payload) not in (bool,int,float,str):raise ValueError()
                if type(payload) is float and not math.isfinite(payload) or type(payload) is str and len(payload)>256:raise ValueError()
                return payload
            if kind=='array':
                if type(payload) is not str or payload in used or payload not in arrays:raise ValueError()
                data=arrays[payload]
                if data.dtype.name not in DTYPES or data.ndim>4 or data.size>64_000_000 or not np.isfinite(data).all():raise ValueError()
                used.add(payload);return from_numpy(data)
            if kind in ('list','tuple') and isinstance(payload,list):
                values=[unpack(entry,depth+1) for entry in payload]
                return tuple(values) if kind=='tuple' else values
            if kind=='dict' and isinstance(payload,list):
                result={}
                for row in payload:
                    if not isinstance(row,list) or len(row)!=2 or type(row[0]) is not str or not re.fullmatch(r'[A-Za-z0-9_.-]{1,256}',row[0]) or row[0] in result:raise ValueError()
                    result[row[0]]=unpack(row[1],depth+1)
                return result
            raise ValueError()
        result=unpack(layout,0)
        if used!=set(arrays):raise ValueError()
        return result
    except Exception:
        raise TrainerError('mlx_state_decode_rejected') from None
