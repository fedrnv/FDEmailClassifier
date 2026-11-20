"""Full model export/load acceptance on random numerical tensors, never emails.

Uses a tiny randomly initialized Qwen3 and the independently licensed published
tokenizer. No optimizer/training, pretrained model weights or category gold is
used. Every output is permanently marked technical-container-fixture.
"""
import importlib.metadata
import json
from pathlib import Path
import shutil
import tempfile

from common import ROOT, ExportError, candidate, digest_file, write_json
from exporter import converter_checkout, convert, sbom
from formats import inspect_gguf
import runtime_load


def run(output_dir, checkout, *, reuse_observed_build=False):
    profile=json.loads((ROOT/"models/export-model-runtime-v1.json").read_text())
    if any(importlib.metadata.version(name)!=version for name,version in profile["packages"].items()):raise ExportError("model_check_runtime_mismatch")
    checkout,converter=converter_checkout(checkout)
    observed=json.loads((ROOT/"Tasks/items/ai/FDEC-019-model-export-and-provenance/evidence/tokenizer-observations-v1.json").read_text())
    tokenizer=ROOT/"training/data/export-qwen-tokenizer-v1"
    for item in observed["files"]:
        if digest_file(tokenizer/item["path"])!={name:item[name] for name in ("sha256","size")}:raise ExportError("model_check_tokenizer_changed")
    import torch
    from transformers import Qwen3Config,Qwen3ForCausalLM,AutoModelForCausalLM
    from peft import LoraConfig,get_peft_model,PeftModel
    from torch_engine import TARGET_MODULES
    torch.set_num_threads(1);torch.manual_seed(104729);torch.use_deterministic_algorithms(True)
    report={}
    context=dict(kind="technical-container-fixture",actual_trained_model_used=False,actual_synthetic_model_used=True,model_runtime_load_verified=False)
    def build(output):
        with tempfile.TemporaryDirectory(prefix="fdec-tiny-export-",dir=output.parent) as name:
            stage=Path(name).resolve()
            if not stage.is_relative_to(output.parent.resolve()) or not stage.name.startswith("fdec-tiny-export-") or stage.is_symlink() or stage.is_junction():raise ExportError("unsafe_tiny_model_staging")
            base_dir=stage/"base";merged_dir=stage/"merged"
            if reuse_observed_build:
                proof_path=ROOT/"Tasks/items/ai/FDEC-019-model-export-and-provenance/evidence/runtime-build-v3.json"
                record=json.loads(proof_path.read_text())
                if record["source_revision"]!=converter["llama_cpp_revision"]:raise ExportError("observed_build_source_mismatch")
                relative=record.pop("executable_relative")
                if relative not in ("build/bin/llama-completion.exe","build/bin/Release/llama-completion.exe","build/bin/llama-completion"):raise ExportError("invalid_observed_build_path")
                executable=ROOT/"training/outputs/fdec019-build-probe-v3"/relative
                if digest_file(executable)["sha256"]!=record["executable_sha256"]:raise ExportError("observed_build_binary_changed")
            else:
                executable,record=runtime_load.build(checkout,stage/"runtime",converter["llama_cpp_revision"])
                converter_checkout(checkout)
            config=Qwen3Config(vocab_size=151936,hidden_size=32,intermediate_size=64,num_hidden_layers=1,num_attention_heads=4,num_key_value_heads=2,head_dim=8,max_position_embeddings=128,attention_dropout=0.0,tie_word_embeddings=True,bos_token_id=151643,eos_token_id=151645,pad_token_id=151643,attn_implementation="eager")
            base=Qwen3ForCausalLM(config).eval()
            base.save_pretrained(str(base_dir),safe_serialization=True)
            for item in observed["files"]:shutil.copyfile(tokenizer/item["path"],base_dir/item["path"])
            metadata=output/"tokenizer";metadata.mkdir()
            for item in observed["files"]:shutil.copyfile(tokenizer/item["path"],metadata/item["path"])
            for item in ("config.json","generation_config.json"):shutil.copyfile(base_dir/item,metadata/item)
            model=get_peft_model(base,LoraConfig(task_type="CAUSAL_LM",r=2,lora_alpha=4,lora_dropout=0.0,bias="none",target_modules=TARGET_MODULES)).eval()
            with torch.no_grad():
                for param_name,value in model.named_parameters():
                    if "lora_B" in param_name:value.normal_(mean=0.0,std=0.001)
            model.peft_config["default"].base_model_name_or_path="fdec-technical-qwen3-tiny"
            adapter=output/"adapter";model.save_pretrained(str(adapter),safe_serialization=True)
            (adapter/"README.md").write_text("# Technical random-tensor model fixture\n\nNo actual email training or public weight clearance.\n",encoding="utf-8")
            probe=torch.tensor([[1,2,3]])
            with torch.inference_mode():reference=model(input_ids=probe).logits
            loaded=PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(str(base_dir),local_files_only=True,trust_remote_code=False,attn_implementation="eager"),str(adapter),local_files_only=True).eval()
            with torch.inference_mode():restored=loaded(input_ids=probe).logits
            if not torch.allclose(reference,restored,atol=1e-6,rtol=1e-6):raise ExportError("tiny_peft_roundtrip_failed")
            merged=loaded.merge_and_unload(safe_merge=True).eval()
            with torch.inference_mode():merged_logits=merged(input_ids=probe).logits
            if not torch.allclose(reference,merged_logits,atol=1e-4,rtol=1e-4):raise ExportError("tiny_merge_roundtrip_failed")
            merged.save_pretrained(str(merged_dir),safe_serialization=True)
            for item in observed["files"]:shutil.copyfile(tokenizer/item["path"],merged_dir/item["path"])
            convert(checkout,"convert_lora_to_gguf.py",adapter,output/"adapter-f16.gguf",base=base_dir)
            convert(checkout,"convert_hf_to_gguf.py",base_dir,output/"base-f16.gguf")
            convert(checkout,"convert_hf_to_gguf.py",merged_dir,output/"classifier-f16.gguf")
            report.update(actual_synthetic_model_used=True,actual_trained_model_used=False,model_training_performed=False,pretrained_tensors_downloaded=False,
                          peft_load_roundtrip=True,merge_probe_max_absolute_error=float((reference-merged_logits).abs().max()),
                          gguf_adapter=inspect_gguf(output/"adapter-f16.gguf",expected_adapter=True),gguf_base=inspect_gguf(output/"base-f16.gguf",expected_adapter=False),gguf_merged=inspect_gguf(output/"classifier-f16.gguf",expected_adapter=False))
            report["runtime"]=runtime_load.compare(output,executable,record,lambda:None)
            report["model_inference_roundtrip_verified"]=True
            context["model_runtime_load_verified"]=True
            write_json(output/"verification.json",report)
            write_json(output/"dataset-manifest.json",dict(schema="fdec-export-datasets/v1",sources=[],scope="technical-random-tensors-only",actual_email_training=False))
            (output/"README.md").write_text("# Technical random-tensor Qwen3 model\n\nNo actual email training, classifier-quality claim or public weight clearance.\n",encoding="utf-8")
            write_json(output/"sbom.cdx.json",sbom(output))
    candidate(output_dir,build=build,context=context,current_check=lambda:None)
    return report
