"""Actual numerical containers and counterfactual license policies; no real weights."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "training/export"))
import common
import formats
import release_gate
import exporter
import split_data as splits


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fdec-export-contract-")
        self.base = Path(self.temporary.name).resolve()
        self.addCleanup(self.cleanup)
        self.key = secrets.token_bytes(32)

    def cleanup(self):
        if not self.base.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not self.base.name.startswith("fdec-export-contract-") or self.base.is_symlink() or self.base.is_junction():
            raise AssertionError("unsafe_export_fixture_cleanup")
        self.temporary.cleanup()

    def test_real_gguf_safetensors_roundtrip_and_fixture_release_denial(self):
        report = {}
        def build(path):
            report.update(formats.numerical_round_trip(path))
            common.write_json(path / "verification.json", report)
        destination = self.base / "fixture"
        common.candidate(destination, build=build, context=dict(kind="technical-container-fixture"), current_check=lambda: None)
        self.assertTrue(report["safetensors_roundtrip"])
        self.assertEqual(report["gguf_roundtrip"]["tensors"], 2)
        self.assertFalse(report["model_inference_roundtrip_verified"])
        common.verify_candidate(destination)
        with self.assertRaises(common.ExportError):
            release_gate.check(destination, key=self.key, current_check=lambda value: None)
        before = (destination / "manifest.json").read_bytes()
        with self.assertRaises(Exception):
            common.candidate(destination, build=build, context={}, current_check=lambda: None)
        self.assertEqual((destination / "manifest.json").read_bytes(), before)

    def test_malformed_gguf_nan_and_unexpected_architecture_reject(self):
        import gguf
        import numpy as np
        for name, arch, value in (("nan", "qwen3", float("nan")), ("arch", "llama", 1.0)):
            path = self.base / (name + ".gguf")
            writer = gguf.GGUFWriter(str(path), arch)
            writer.add_tensor("test.weight", np.array([[value]], dtype=np.float32))
            writer.write_header_to_file(); writer.write_kv_data_to_file(); writer.write_tensors_to_file(); writer.close()
            with self.assertRaises(common.ExportError): formats.inspect_gguf(path)
        path = self.base / "bad.gguf"
        path.write_bytes(b"GGUF-not-a-real-container")
        with self.assertRaises(common.ExportError): formats.inspect_gguf(path)

    def test_signed_candidate_hash_rebinding_extras_and_rollback(self):
        def build(path): (path / "payload.json").write_text('{"technical":true}')
        path = self.base / "signed"
        common.candidate(path, build=build, context=dict(kind="fdec-trained-export/v1"), current_check=lambda: None, key=self.key)
        common.verify_candidate(path, key=self.key)
        with self.assertRaises(common.ExportError): common.verify_candidate(path)
        with self.assertRaises(common.ExportError): common.verify_candidate(path, key=b"x"*32)
        (path / "payload.json").write_text('{"technical":false}')
        manifest = json.loads((path / "manifest.json").read_text())
        manifest["files"][0].update(common.digest_file(path / "payload.json"))
        (path / "manifest.json").write_text(splits.canonical_json(manifest)+"\n")
        receipt = json.loads((path / "receipt.json").read_text())
        receipt["manifest_sha256"] = common.digest_file(path / "manifest.json")["sha256"]
        (path / "receipt.json").write_text(json.dumps(receipt))
        with self.assertRaises(common.ExportError): common.verify_candidate(path, key=self.key)
        def broken(path):
            (path / "partial.json").write_text("partial")
            raise ValueError("private-diagnostic")
        output = self.base / "failed"
        with self.assertRaises(common.ExportError): common.candidate(output, build=broken, context={}, current_check=lambda: None)
        self.assertFalse(output.exists())

    def make_counterfactual_release(self):
        # Simulated audit and bytes only, never a real weight rights decision.
        context = dict(kind="fdec-trained-export/v1", variants=list(common.VARIANTS), model_runtime_load_verified=True, base_model_sha256="a"*64, training_provenance=dict(annotations_sha256="b"*64, prompt_sha256="c"*64))
        def build(path):
            for name in ("adapter/adapter_model.safetensors", "adapter/adapter_config.json", "base-f16.gguf", "adapter-f16.gguf", "classifier-f16.gguf", "tokenizer/tokenizer_config.json", "tokenizer/tokenizer.json", "tokenizer/LICENSE", "README.md", "dataset-manifest.json", "sbom.cdx.json", "verification.json"):
                target=path/name; target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(b"counterfactual software policy fixture, not model weights")
        path=self.base/"counterfactual-candidate"
        common.candidate(path,build=build,context=context,current_check=lambda:None,key=self.key)
        policy_root=self.base/"policy"; (policy_root/"models/audits").mkdir(parents=True)
        legal=policy_root/"models/audits/fixture.md"; legal.write_text("Counterfactual software-only rights evidence; no real authorship or legal clearance.\n")
        manifest_hash=common.digest_file(path/"manifest.json")["sha256"]
        audit=dict(schema="fdec-model-redistribution-audit/v1",status="cleared",model_manifest_sha256=manifest_hash,base_model_sha256="a"*64,dataset_manifest_sha256=common.digest_file(path/"dataset-manifest.json")["sha256"],annotation_sha256="b"*64,prompt_sha256="c"*64,allowed_variants=list(common.VARIANTS),public_weight_distribution=True,obligations_satisfied=sorted(release_gate.OBLIGATIONS),legal_evidence=[dict(path="models/audits/fixture.md",sha256=common.digest_file(legal)["sha256"])],reviewer="counterfactual-test-only",reviewed_at="2026-01-01T00:00:00Z")
        common.write_json(policy_root/"models/audits/fixture.json",audit)
        policy=dict(schema="fdec-weight-release-policy/v1",scope="specialized-email-classifier",audits=[dict(manifest_sha256=manifest_hash,audit=dict(path="models/audits/fixture.json",sha256=common.digest_file(policy_root/"models/audits/fixture.json")["sha256"]))],note="Counterfactual software fixture only")
        common.write_json(policy_root/"models/release-policy-v1.json",policy)
        return path,policy_root,audit,policy

    def test_separate_documented_rights_gate_and_current_authority(self):
        path,root,audit,policy=self.make_counterfactual_release()
        observed=[]
        result=release_gate.check(path,key=self.key,current_check=lambda value:observed.append(value),policy_root=root)
        self.assertTrue(result["eligible_for_operator_review"])
        self.assertFalse(result["published"])
        self.assertEqual(len(observed),1)
        # The actual project's empty policy grants this candidate nothing.
        with self.assertRaises(common.ExportError): release_gate.check(path,key=self.key,current_check=lambda value:None)
        def revoked(value): raise ValueError("revoked")
        with self.assertRaises(common.ExportError): release_gate.check(path,key=self.key,current_check=revoked,policy_root=root)
        for field,value in (("public_weight_distribution",False),("base_model_sha256","d"*64),("dataset_manifest_sha256","d"*64),("annotation_sha256","d"*64),("prompt_sha256","d"*64),("obligations_satisfied",["base-license-and-notices"]),("allowed_variants",["peft-lora-f32"])):
            changed=deepcopy(audit);changed[field]=value
            audit_path=root/"models/audits/fixture.json";audit_path.write_text(splits.canonical_json(changed))
            policy["audits"][0]["audit"]["sha256"]=common.digest_file(audit_path)["sha256"]
            (root/"models/release-policy-v1.json").write_text(splits.canonical_json(policy))
            with self.subTest(field=field):
                with self.assertRaises(common.ExportError): release_gate.check(path,key=self.key,current_check=lambda value:None,policy_root=root)

    def test_cli_container_checks_and_missing_actual_input_fail_closed(self):
        destination=self.base/"cli"
        command=[sys.executable,str(ROOT/"training/export/export_cli.py")]
        result=subprocess.run(command+["software-check","--output-dir",str(destination)],capture_output=True,text=True,check=True)
        self.assertFalse(json.loads(result.stdout)["actual_trained_model_used"])
        checked=subprocess.run(command+["verify","--candidate-dir",str(destination)],capture_output=True,text=True,check=True)
        self.assertFalse(json.loads(checked.stdout)["public_weight_redistribution_approved"])
        invalid=subprocess.run(command+["export","--private-token"],capture_output=True,text=True)
        self.assertEqual(invalid.returncode,2)
        self.assertNotIn("private-token",invalid.stderr)
        from types import SimpleNamespace
        from unittest.mock import patch
        args=SimpleNamespace(opt_in=True,inventory="missing",consent="missing",split_dir="missing",annotations="missing",prompt="missing",source_run=["missing"],checkpoint="missing",model_dir="missing",llama_cpp_dir="missing",output_dir=self.base/"not-created")
        with patch.object(splits,"authority_key",return_value=self.key),patch.object(exporter,"converter_checkout") as converter:
            with self.assertRaises(common.ExportError): exporter.run(args)
            converter.assert_not_called()
        self.assertFalse(args.output_dir.exists())

    def test_fresh_runtime_build_identity_and_numerical_probe_protocol(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        import os
        import runtime_load
        build_dir=self.base/"private-build"
        name="llama-completion.exe" if os.name=="nt" else "llama-completion"
        def compile_double(command, **kwargs):
            if "--build" in command:
                executable=build_dir/"bin"/name
                executable.parent.mkdir(parents=True)
                executable.write_bytes(b"technical build-protocol double; never executed")
                (build_dir/"CMakeCache.txt").write_bytes(b"counterfactual compiler configuration")
            return SimpleNamespace(returncode=0,stdout=b"build-protocol")
        with patch.object(runtime_load.subprocess,"run",side_effect=compile_double) as child:
            executable,record=runtime_load.build(self.base/"pinned-source",build_dir,"a"*40)
            self.assertEqual(child.call_count,2)
            self.assertEqual(record["executable_sha256"],common.digest_file(executable)["sha256"])
        with patch.object(runtime_load.subprocess,"run",return_value=SimpleNamespace(returncode=0,stdout=b"numerical-token-output")) as child:
            report=runtime_load.compare(self.base,executable,record,lambda:None)
            self.assertTrue(report["model_load_and_two_token_probe_verified"])
            self.assertEqual(child.call_count,2)
            child.side_effect=[SimpleNamespace(returncode=0,stdout=b"one"),SimpleNamespace(returncode=0,stdout=b"two")]
            with self.assertRaises(common.ExportError):runtime_load.compare(self.base,executable,record,lambda:None)
            child.side_effect=None
            executable.write_bytes(b"changed executable")
            with self.assertRaises(common.ExportError):runtime_load.compare(self.base,executable,record,lambda:None)


if __name__=="__main__":unittest.main()
