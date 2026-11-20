"""Verify a private complete numerical-model fixture; never clear real weights."""
import argparse
import json
from pathlib import Path
from common import ExportError, ROOT, verify_candidate
import release_gate


def verify(path):
    path=Path(path)
    manifest=verify_candidate(path)
    context=manifest["context"]
    if context.get("kind")!="technical-container-fixture" or context.get("actual_trained_model_used") is not False or context.get("model_runtime_load_verified") is not True:raise ExportError("not_verified_numerical_model_fixture")
    names={item["path"] for item in manifest["files"]}
    required={"base-f16.gguf","adapter-f16.gguf","classifier-f16.gguf","adapter/adapter_model.safetensors","adapter/adapter_config.json","adapter/README.md","tokenizer/config.json","tokenizer/generation_config.json","tokenizer/LICENSE","tokenizer/tokenizer.json","tokenizer/tokenizer_config.json","tokenizer/vocab.json","tokenizer/merges.txt","README.md","dataset-manifest.json","verification.json","sbom.cdx.json"}
    if not required<=names:raise ExportError("incomplete_model_fixture")
    report=json.loads((path/"verification.json").read_text())
    if report["model_training_performed"] is not False or report["pretrained_tensors_downloaded"] is not False or report["peft_load_roundtrip"] is not True or report["model_inference_roundtrip_verified"] is not True or report["runtime"]["merged_adapter_probe_equal"] is not True:raise ExportError("model_fixture_checks_missing")
    # The real default-deny registry must reject the actual complete fixture.
    try:release_gate.check(path,key=None,current_check=lambda value:None)
    except ExportError:pass
    else:raise ExportError("technical_model_fixture_release_not_denied")
    return dict(scope="complete-random-tensor-model-only",artifact_integrity=True,peft_roundtrip=True,gguf_load_and_two_token_roundtrip=True,tokenizer_chat_metadata=True,provenance_card_sbom_inventory=True,real_registry_release_denied=True,actual_email_training=False,public_weights_cleared=False)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--candidate-dir",required=True)
    args=parser.parse_args()
    try:print(json.dumps(verify(args.candidate_dir)))
    except Exception:
        print("numerical_model_verification_rejected")
        raise SystemExit(2)
