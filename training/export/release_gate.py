"""Separate documented weight-redistribution audit; never infer it from training grants."""
from pathlib import Path
from datetime import datetime, timezone
import re
from common import ROOT, ExportError, VARIANTS, verify_candidate, digest_file
import split_data as splits
from ingest_dataset import reject_links

OBLIGATIONS = {"base-license-and-notices", "dataset-training-and-public-weight-rights", "annotation-and-prompt-rights", "generator-provider-terms", "tokenizer-rights", "model-card-and-attribution"}


def binding(root, value, *, suffix):
    if not isinstance(value, dict) or set(value) != {"path", "sha256"} or not isinstance(value["path"], str) or not re.fullmatch(r"models/audits/[A-Za-z0-9_-]+\." + suffix, value["path"]):
        raise ExportError("invalid_weight_rights_binding")
    path = reject_links(Path(root) / value["path"])
    if digest_file(path)["sha256"] != value["sha256"]:
        raise ExportError("weight_rights_evidence_changed")
    return path


def check(directory, *, key, current_check, policy_root=ROOT):
    """Library policy_root is for isolated counterfactual tests, never a CLI flag."""
    try:
        manifest = verify_candidate(directory, key=key)
        context = manifest["context"]
        if context.get("kind") != "fdec-trained-export/v1" or set(context.get("variants", ())) != set(VARIANTS) or context.get("model_runtime_load_verified") is not True:
            raise ValueError()
        required = {"adapter/adapter_model.safetensors", "adapter/adapter_config.json", "base-f16.gguf", "adapter-f16.gguf", "classifier-f16.gguf", "tokenizer/tokenizer_config.json", "tokenizer/tokenizer.json", "tokenizer/LICENSE", "README.md", "dataset-manifest.json", "sbom.cdx.json", "verification.json"}
        if not required <= {row["path"] for row in manifest["files"]}:
            raise ValueError()
        manifest_hash = digest_file(Path(directory) / "manifest.json")["sha256"]
        policy = splits.read_json(Path(policy_root) / "models/release-policy-v1.json", 100_000)
        if not isinstance(policy, dict) or set(policy) != {"schema", "scope", "audits", "note"} or policy["schema"] != "fdec-weight-release-policy/v1" or policy["scope"] != "specialized-email-classifier" or not isinstance(policy["audits"], list):
            raise ValueError()
        entries = [row for row in policy["audits"] if row.get("manifest_sha256") == manifest_hash]
        if len(entries) != 1 or set(entries[0]) != {"manifest_sha256", "audit"}:
            raise ValueError()
        audit = splits.read_json(binding(policy_root, entries[0]["audit"], suffix="json"), 100_000)
        fields = {"schema", "status", "model_manifest_sha256", "base_model_sha256", "dataset_manifest_sha256", "annotation_sha256", "prompt_sha256", "allowed_variants", "public_weight_distribution", "obligations_satisfied", "legal_evidence", "reviewer", "reviewed_at"}
        if not isinstance(audit, dict) or set(audit) != fields or audit["schema"] != "fdec-model-redistribution-audit/v1" or audit["status"] != "cleared" or audit["public_weight_distribution"] is not True or not isinstance(audit["reviewer"], str) or not audit["reviewer"] or set(audit["obligations_satisfied"]) != OBLIGATIONS or set(audit["allowed_variants"]) != set(VARIANTS) or not isinstance(audit["legal_evidence"], list) or not audit["legal_evidence"]:
            raise ValueError()
        if splits.utc(audit["reviewed_at"]) > datetime.now(timezone.utc): raise ValueError()
        expected = dict(model_manifest_sha256=manifest_hash, base_model_sha256=context["base_model_sha256"], dataset_manifest_sha256=digest_file(Path(directory) / "dataset-manifest.json")["sha256"], annotation_sha256=context["training_provenance"]["annotations_sha256"], prompt_sha256=context["training_provenance"]["prompt_sha256"])
        if any(audit[name] != value for name, value in expected.items()):
            raise ValueError()
        for item in audit["legal_evidence"]:
            binding(policy_root, item, suffix="md")
        current_check(context["training_provenance"])
        verify_candidate(directory, key=key)
        return dict(schema="fdec-weight-release-admission/v1", eligible_for_operator_review=True, published=False, manifest_sha256=manifest_hash,
                    audit_sha256=entries[0]["audit"]["sha256"], note="Separate explicit operator publication authorization is still required")
    except Exception:
        raise ExportError("public_weight_redistribution_not_cleared") from None
