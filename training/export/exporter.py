"""Offline private export implementation. Actual trained-model integration is pending."""
from collections import Counter
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from common import ROOT, ExportError, VARIANTS, candidate, runtime, write_json, digest_file, reject_links
from lineage import checkpoint_context, inputs, provenance
import training_inputs
import checkpoints
import training_boundary
import split_data as splits
from local_model import quiet_runtime, verify_snapshot


def converter_checkout(path):
    path = reject_links(path).resolve()
    profile = runtime()
    head = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30, check=True).stdout.strip()
    changed = subprocess.run(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, timeout=30, check=True).stdout
    if head != profile["llama_cpp_revision"] or changed:
        raise ExportError("converter_checkout_not_pinned_and_clean")
    for row in profile["converter_documents"]:
        if digest_file(path / row["path"])["sha256"] != row["sha256"]:
            raise ExportError("converter_source_changed")
    return path, profile


def convert(checkout, script, source, destination, *, base=None):
    # Fixed audited scripts/flags, no remote-model identifier or arbitrary shell.
    command = [sys.executable, str(checkout / script), str(source), "--outfile", str(destination), "--outtype", "f16"]
    if base is not None: command += ["--base", str(base)]
    environment = os.environ.copy()
    environment.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1")
    result = subprocess.run(command, cwd=checkout, env=environment, capture_output=True, timeout=900)
    if result.returncode or not destination.is_file():
        raise ExportError("offline_gguf_conversion_failed")


def sbom(artifact_directory=None):
    # Metadata hashes identify installed distribution metadata, not audited
    # binary packages. No runtime is redistributed inside the model candidate.
    components = []
    import hashlib
    for distribution in sorted(importlib.metadata.distributions(), key=lambda item: item.metadata["Name"].casefold()):
        name, version = distribution.metadata["Name"], distribution.version
        raw = (distribution.read_text("METADATA") or "").encode()
        components.append(dict(type="library", name=name, version=version, purl=f"pkg:pypi/{name.lower().replace('_','-')}@{version}",
                               hashes=[dict(alg="SHA-256", content=hashlib.sha256(raw).hexdigest())], properties=[dict(name="fdec:hash-scope", value="installed-METADATA-only; not a wheel-redistribution audit")]))
    if artifact_directory is not None:
        for path in sorted(artifact_directory.rglob("*")):
            if path.is_file() and path.suffix in (".gguf", ".safetensors"):
                components.append(dict(type="file", name=path.relative_to(artifact_directory).as_posix(), hashes=[dict(alg="SHA-256",content=digest_file(path)["sha256"])]))
    return dict(bomFormat="CycloneDX", specVersion="1.6", version=1, metadata=dict(component=dict(type="machine-learning-model", name="FDEmailClassifier", version="private-unreleased")), components=components)


def run(args):
    if not args.opt_in: raise ExportError("explicit_opt_in_required")
    key = splits.authority_key()
    snapshot, context, base_profile = checkpoint_context(args, key)
    if context["config"]["backend"] != "lora":
        raise ExportError("qlora_export_requires_quantized_base_equivalence_validation")
    checkout, converter = converter_checkout(args.llama_cpp_dir)
    import runtime_load
    from common import private_output
    private_output(args.output_dir, ROOT)
    for name, version in (("torch", "2.15.0"), ("transformers", "5.23.0"), ("peft", "0.22.0")):
        if importlib.metadata.version(name) != version: raise ExportError("unverified_export_model_runtime")
    def current_check():
        if training_inputs.admit(**inputs(args, key)) != snapshot:
            raise ExportError("export_training_provenance_changed")
        training_inputs.recheck(snapshot, key=key)
    with quiet_runtime():
        import torch
        from transformers import AutoModelForCausalLM
        from peft import LoraConfig, get_peft_model, PeftModel
        from formats import inspect_gguf
        from torch_engine import TARGET_MODULES
        import io
        _, state = checkpoints.load(args.checkpoint, context=context, key=key, reader=lambda raw: torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True), current_check=current_check)
        if not isinstance(state, dict) or set(state) != {"schema", "adapter", "parameter_order", "optimizer", "rng_cpu", "rng_cuda"} or state["schema"] != "fdec-torch-peft-state/v1":
            raise ExportError("unsupported_checkpoint_tensor_state")
        base = AutoModelForCausalLM.from_pretrained(str(args.model_dir), local_files_only=True, trust_remote_code=False, use_safetensors=True, dtype=torch.float32, attn_implementation="eager").to("cpu").eval()
        config = context["config"]
        model = get_peft_model(base, LoraConfig(task_type="CAUSAL_LM", r=config["rank"], lora_alpha=config["alpha"], lora_dropout=0.0, bias="none", target_modules=TARGET_MODULES))
        parameters = {name: value for name, value in model.named_parameters() if value.requires_grad}
        if list(parameters) != state["parameter_order"] or set(parameters) != set(state["adapter"]): raise ExportError("adapter_parameter_identity_changed")
        with torch.no_grad():
            for name, value in parameters.items():
                saved = state["adapter"][name]
                if saved.shape != value.shape or saved.dtype != torch.float32 or not torch.isfinite(saved).all().item(): raise ExportError("invalid_adapter_tensor")
                value.copy_(saved)
        model.eval()
        model.peft_config["default"].base_model_name_or_path = base_profile["model_id"]
        model.peft_config["default"].revision = base_profile["revision"]
        verify_snapshot(args.model_dir)
        tensor_identity = next(row["digest"] for row in base_profile["files"] if row["path"] == "model.safetensors")
        export_context = dict(kind="fdec-trained-export/v1", variants=list(VARIANTS), base_model_sha256=tensor_identity, training_provenance=provenance(snapshot),
                              checkpoint_metadata_sha256=digest_file(Path(args.checkpoint) / "metadata.json")["sha256"], converter_revision=converter["llama_cpp_revision"],
                              model_runtime_load_verified=False, note="Runtime probe is numerical, not classifier-quality or full-logit equivalence")
        def build(output):
            with tempfile.TemporaryDirectory(prefix="fdec-runtime-export-", dir=output.parent) as temporary_build:
                runtime_root = Path(temporary_build).resolve()
                if not runtime_root.is_relative_to(output.parent.resolve()) or not runtime_root.name.startswith("fdec-runtime-export-") or runtime_root.is_symlink() or runtime_root.is_junction(): raise ExportError("unsafe_runtime_staging")
                converter_checkout(checkout)
                executable, build_record = runtime_load.build(checkout, runtime_root / "build", converter["llama_cpp_revision"])
                converter_checkout(checkout)
                build_with_runtime(output, executable, build_record)
        def build_with_runtime(output, executable, build_record):
            adapter = output / "adapter"
            adapter.mkdir()
            model.save_pretrained(str(adapter), safe_serialization=True)
            card = "# FDEmailClassifier private candidate\n\nNot cleared for public weight distribution.\n\nBase: Qwen/Qwen3-0.6B at " + base_profile["revision"] + ".\n\nActual measured language coverage, classifier quality and calibrated probabilities: unverified.\n\nSee dataset-manifest.json, sbom.cdx.json and manifest.json. No runtime or dataset is bundled.\n"
            (adapter / "README.md").write_text(card, encoding="utf-8")
            (output / "README.md").write_text(card, encoding="utf-8")
            tokenizer = output / "tokenizer"
            tokenizer.mkdir()
            for name in ("tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt", "generation_config.json", "config.json", "LICENSE"):
                shutil.copyfile(Path(args.model_dir) / name, tokenizer / name)
            # Numerical loader probe has no email or natural-language fixture.
            probe = torch.tensor([[1,2,3]], dtype=torch.long)
            with torch.inference_mode(): reference = model(input_ids=probe).logits.detach()
            reloaded = PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(str(args.model_dir), local_files_only=True, trust_remote_code=False, use_safetensors=True, dtype=torch.float32, attn_implementation="eager"), str(adapter), local_files_only=True).eval()
            with torch.inference_mode(): reproduced = reloaded(input_ids=probe).logits.detach()
            if not torch.allclose(reference, reproduced, atol=1e-6, rtol=1e-6): raise ExportError("peft_adapter_load_roundtrip_failed")
            convert(checkout, "convert_lora_to_gguf.py", adapter, output / "adapter-f16.gguf", base=Path(args.model_dir))
            convert(checkout, "convert_hf_to_gguf.py", Path(args.model_dir), output / "base-f16.gguf")
            with tempfile.TemporaryDirectory(prefix="fdec-merged-export-", dir=output.parent) as temporary:
                stage = Path(temporary).resolve()
                if not stage.is_relative_to(output.parent.resolve()) or not stage.name.startswith("fdec-merged-export-") or stage.is_symlink() or stage.is_junction(): raise ExportError("unsafe_export_staging")
                merged = reloaded.merge_and_unload(safe_merge=True).eval()
                with torch.inference_mode(): merged_result = merged(input_ids=probe).logits.detach()
                if not torch.allclose(reference, merged_result, atol=1e-4, rtol=1e-4): raise ExportError("merged_adapter_probe_failed")
                merged.save_pretrained(str(stage), safe_serialization=True)
                for name in ("tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"):
                    shutil.copyfile(Path(args.model_dir) / name, stage / name)
                convert(checkout, "convert_hf_to_gguf.py", stage, output / "classifier-f16.gguf")
            checks = dict(peft_load_roundtrip=True, merged_probe=True, gguf_adapter=inspect_gguf(output / "adapter-f16.gguf", expected_adapter=True), gguf_model=inspect_gguf(output / "classifier-f16.gguf", expected_adapter=False), llama_cpp_model_runtime_load_verified=False)
            checks["runtime"] = runtime_load.compare(output, executable, build_record, current_check)
            checks["llama_cpp_model_runtime_load_verified"] = True
            export_context["model_runtime_load_verified"] = True
            export_context["runtime_executable_sha256"] = build_record["executable_sha256"]
            write_json(output / "verification.json", checks)
            counts = Counter(splits.canonical_json(row["source"]) for row in splits.inventory_rows(snapshot.inventory))
            sources=[]
            for encoded,count in sorted(counts.items()):
                identity=splits.strict_json(encoded)
                rights=training_boundary.assert_training_source(identity,purpose="commercial_training")
                descriptor=rights["descriptor"]
                sources.append(dict(identity=identity,inventory_records=count,training_license=descriptor["license"],attribution=descriptor["attribution"],source_audit_sha256=descriptor["audit_sha256"],public_weight_rights="separate-review-required"))
            write_json(output / "dataset-manifest.json", dict(schema="fdec-export-datasets/v1", **provenance(snapshot), sources=sources, contains_email_or_personal_data=False, source_weight_redistribution_clearance="separate-audit-required"))
            write_json(output / "sbom.cdx.json", sbom(output))
        return candidate(args.output_dir, build=build, context=export_context, current_check=current_check, key=key)
