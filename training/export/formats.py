"""Actual safetensors/GGUF I/O, never a claim of model inference equivalence."""
import hashlib
from pathlib import Path
import sys

from common import ExportError, runtime


def inspect_gguf(path, *, expected_adapter=None):
    runtime()
    import gguf
    import numpy as np
    reader = None
    try:
        reader = gguf.GGUFReader(str(path), mode="r")
        architecture = reader.fields["general.architecture"].contents()
        if architecture != "qwen3" or not reader.tensors:
            raise ValueError()
        adapter = reader.fields["general.type"].contents() == "adapter" if "general.type" in reader.fields else False
        if expected_adapter is not None and adapter != expected_adapter:
            raise ValueError()
        names = set()
        for tensor in reader.tensors:
            if tensor.name in names or tensor.tensor_type not in (gguf.GGMLQuantizationType.F32, gguf.GGMLQuantizationType.F16) or not np.isfinite(tensor.data).all():
                raise ValueError()
            names.add(tensor.name)
        return dict(format="GGUF", architecture=architecture, adapter=adapter, tensors=len(names), verification="container-only; no model-runtime inference proof")
    except Exception:
        raise ExportError("gguf_container_rejected") from None
    finally:
        if reader is not None:
            reader.data._mmap.close()


def numerical_round_trip(directory):
    runtime()
    import gguf
    import numpy as np
    from safetensors.numpy import save_file, load_file
    tensors = {"base_model.model.model.layers.0.self_attn.q_proj.lora_A.weight": np.arange(16, dtype=np.float32).reshape(2,8) / 16,
               "base_model.model.model.layers.0.self_attn.q_proj.lora_B.weight": np.arange(16, dtype=np.float32).reshape(8,2) / 32}
    save_file(tensors, str(directory / "adapter_model.safetensors"))
    restored = load_file(str(directory / "adapter_model.safetensors"))
    if any(not np.array_equal(value, restored[name]) for name, value in tensors.items()):
        raise ExportError("safetensors_roundtrip_mismatch")
    writer = gguf.GGUFWriter(str(directory / "numeric-lora.gguf"), "qwen3")
    writer.add_string("general.type", "adapter")
    writer.add_string("adapter.type", "lora")
    writer.add_float32("adapter.lora.alpha", 4.0)
    writer.add_string("fdec.scope", "technical-numerical-fixture-only")
    for name, value in tensors.items():
        target = "blk.0.attn_q." + ("lora_a" if ".lora_A." in name else "lora_b")
        writer.add_tensor(target, value.astype(np.float16))
    writer.write_header_to_file(); writer.write_kv_data_to_file(); writer.write_tensors_to_file(); writer.close()
    reader = gguf.GGUFReader(str(directory / "numeric-lora.gguf"), mode="r")
    try:
        for tensor in reader.tensors:
            key = next(name for name in tensors if (".lora_A." in name) == tensor.name.endswith("lora_a"))
            if not np.array_equal(tensor.data.astype(np.float32), tensors[key]):
                raise ExportError("gguf_roundtrip_mismatch")
    finally:
        reader.data._mmap.close()
    return dict(safetensors_roundtrip=True, gguf_roundtrip=inspect_gguf(directory / "numeric-lora.gguf", expected_adapter=True), actual_trained_model_used=False, model_inference_roundtrip_verified=False)
