"""Technical software checks only. No actual model consumes fixture emails."""
from copy import deepcopy
from datetime import timedelta
import hashlib
import hmac
import json
import math
from pathlib import Path
import random
import secrets
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "training/finetune"))
import trainer_config as config
import checkpoints
import training_inputs as inputs
import train
import gpu_check
import torch_engine
import split_data as splits
from baseline_metrics import DIMENSIONS


class ConfigTests(unittest.TestCase):
    def test_technical_cpu_path_cannot_disable_actual_training_gpu_requirement(self):
        value=config.read(ROOT/"training/config/peft-trainer-v1.json")
        with self.assertRaises(config.TrainerError):gpu_check.run_cpu(opt_in=False)
        with self.assertRaises(config.TrainerError):torch_engine.deterministic_runtime(dict(value,backend="qlora"),technical_cpu=True)
        profile=json.loads((ROOT/"training/config/peft-runtime-v1.json").read_text())
        unavailable=SimpleNamespace(cuda=SimpleNamespace(is_available=lambda:False))
        with patch.object(torch_engine.importlib.metadata,"version",side_effect=lambda name:profile["packages"][name]),patch.dict(sys.modules,{"torch":unavailable,"numpy":SimpleNamespace()}),patch.dict(torch_engine.os.environ,{"CUBLAS_WORKSPACE_CONFIG":":4096:8"}):
            with self.assertRaisesRegex(config.TrainerError,"single_bfloat16_cuda_device_required"):
                torch_engine.deterministic_runtime(value)
        command=[sys.executable,str(ROOT/"training/finetune/train.py")]
        missing=subprocess.run(command+["cpu-check"],capture_output=True,text=True)
        self.assertEqual((missing.returncode,missing.stderr),(2,"trainer_execution_rejected\n"))
        unsupported=subprocess.run(command+["train","--technical-cpu"],capture_output=True,text=True)
        self.assertEqual((unsupported.returncode,unsupported.stderr),(2,"trainer_arguments_invalid\n"))

    def test_bounded_config_and_no_implicit_backend_fallback(self):
        value = config.read(ROOT / "training/config/peft-trainer-v1.json")
        self.assertEqual(config.validate(value), value)
        for field, wrong in (("rank", True), ("rank", 0), ("seed", -1), ("learning_rate", float("nan")), ("learning_rate", float("inf")), ("backend", "cpu-fallback"), ("max_steps", 0), ("max_sequence_tokens", 1_000_000), ("extra", 1)):
            changed = dict(value, **{field: wrong})
            with self.subTest(field=field, wrong=str(wrong)):
                with self.assertRaises(config.TrainerError):
                    config.validate(changed)

    def test_reconstructed_cursor_has_complete_epochs(self):
        size, seed = 17, 104729
        sequence = [config.record_index(seed, index, size) for index in range(51)]
        for start in range(0, 51, size):
            self.assertEqual(set(sequence[start:start+size]), set(range(size)))
        self.assertEqual(sequence[21:], [config.record_index(seed, index, size) for index in range(21, 51)])
        self.assertNotEqual(sequence, [config.record_index(seed+1, index, size) for index in range(51)])
        for size, index in ((0, 1), (True, 1), (3, -1)):
            with self.assertRaises(config.TrainerError):
                config.record_index(seed, index, size)

    def test_runtime_profile_binds_observed_candidates_without_claiming_execution(self):
        profile = json.loads((ROOT / "training/config/peft-runtime-v1.json").read_text())
        observation = ROOT / "Tasks/items/ai/FDEC-016-lora-qlora-trainer/evidence/runtime-observations-v1.json"
        self.assertEqual(profile["observation_sha256"], hashlib.sha256(observation.read_bytes().replace(b"\r\n", b"\n")).hexdigest())
        self.assertFalse(profile["runtime_integration_verified"])
        self.assertFalse(profile["distribution_license_audit_complete"])

    def test_cli_diagnostics_and_preflight_do_not_echo_input_or_train(self):
        command = [sys.executable, str(ROOT / "training/finetune/train.py")]
        checked = subprocess.run(command + ["preflight"], capture_output=True, text=True, check=True)
        self.assertFalse(json.loads(checked.stdout)["actual_training"])
        invalid = subprocess.run(command + ["train", "--private-token"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(invalid.stderr, "trainer_arguments_invalid\n")
        with self.assertRaises(config.TrainerError):
            gpu_check.run()
        args = train.argparse.Namespace(opt_in=True, config=ROOT / "training/config/peft-trainer-v1.json", output_dir=ROOT / "training/outputs/nonexistent-finetune-test", stop_after=None,
                                       inventory="missing-private-token", consent="missing", split_dir="missing", annotations="missing", prompt="missing", source_run=["missing"], model_dir="missing", resume=None)
        with patch.object(train, "TorchEngine") as engine, patch.object(splits, "authority_key", return_value=b"x" * 32):
            with self.assertRaises(Exception):
                train.run(args)
            engine.assert_not_called()
        self.assertFalse(args.output_dir.exists())

    def test_teacher_forcing_masks_the_independent_prompt_and_user_input(self):
        calls = {}
        class Tokenizer:
            eos_token_id = 9
            def apply_chat_template(self, messages, **kwargs):
                calls.update(messages=messages, template=kwargs)
                return [1, 2]
            def encode(self, text, **kwargs):
                calls.update(target=text, encoding=kwargs)
                return [3, 4]
        engine = torch_engine.TorchEngine.__new__(torch_engine.TorchEngine)
        engine.tokenizer = Tokenizer()
        engine.config = dict(max_sequence_tokens=5)
        ids, labels = engine.tokenize("independent technical instruction", "technical subject", "technical body", {"technical": True})
        self.assertEqual(ids, [1, 2, 3, 4, 9])
        self.assertEqual(labels, [-100, -100, 3, 4, 9])
        self.assertFalse(calls["template"]["enable_thinking"])
        self.assertFalse(calls["encoding"]["add_special_tokens"])
        self.assertEqual(calls["messages"][0]["content"], "independent technical instruction")
        engine.config["max_sequence_tokens"] = 4
        with self.assertRaises(config.TrainerError):
            engine.tokenize("x", "x", "x", {})


class OrchestrationTests(unittest.TestCase):
    def test_private_run_resume_and_committed_checkpoint_recovery(self):
        # Actual runner/checkpoint code with a numerical protocol double. No
        # transformer runtime, actual email training or GPU result is implied.
        class NumericEngine:
            last = None
            def __init__(self, *args):
                self.identity = dict(kind="counterfactual-numerical-protocol-double")
                self.value, self.updates = 0, 0
                NumericEngine.last = self
            def tokenize(self, *args):
                return ([1, 2, 3], [-100, 2, 3])
            def update(self, batches, current_check):
                for batch in batches:
                    current_check()
                    self.value = self.value * 7 + sum(batch[0])
                self.updates += 1
            def state(self):
                return dict(value=self.value, updates=self.updates)
            def restore(self, state):
                self.value, self.updates = state["value"], state["updates"]
            def write(self, state, path):
                path.write_text(json.dumps(state))
            def read(self, content):
                return json.loads(content)
        with tempfile.TemporaryDirectory(prefix="fdec-trainer-orchestration-") as name:
            directory = Path(name).resolve()
            if not directory.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not directory.name.startswith("fdec-trainer-orchestration-") or directory.is_symlink() or directory.is_junction():
                raise AssertionError("unsafe_orchestration_fixture")
            configuration = config.read(ROOT / "training/config/peft-trainer-v1.json")
            configuration.update(max_steps=4, gradient_accumulation=2, checkpoint_interval=2)
            config_path = directory / "config.json"
            config_path.write_text(json.dumps(configuration))
            rid = "a" * 64
            snapshot = SimpleNamespace(inventory={"technical": True}, consent={"technical": True}, split={"receipt": {"technical": True}},
                                       rows=[dict(record_id=rid, classification={"technical": True})], texts={rid: ("technical", "technical")}, system="technical", annotations_sha256="b" * 64, prompt_sha256="c" * 64, review_sha256="d" * 64)
            arguments = dict(opt_in=True, config=config_path, stop_after=None, inventory="technical", consent="technical", split_dir="technical", annotations="technical", prompt="technical", source_run=["technical"], model_dir=directory, resume=None)
            with patch.object(train, "admit", return_value=snapshot), patch.object(train, "recheck") as authority, patch.object(splits, "authority_key", return_value=b"x" * 32), patch.object(train, "TorchEngine", NumericEngine):
                whole = directory / "whole"
                self.assertEqual(train.run(SimpleNamespace(**arguments, output_dir=whole))["status"], "completed")
                partial = directory / "partial"
                partial_args = dict(arguments, stop_after=2)
                self.assertEqual(train.run(SimpleNamespace(**partial_args, output_dir=partial))["status"], "checkpointed")
                resumed = directory / "resumed"
                resumed_args = dict(arguments, resume=partial / "step-000000002")
                self.assertEqual(train.run(SimpleNamespace(**resumed_args, output_dir=resumed))["status"], "completed")
                self.assertEqual((whole / "step-000000004/state.pt").read_bytes(), (resumed / "step-000000004/state.pt").read_bytes())
                self.assertGreater(authority.call_count, 10)
                publish_failure = directory / "publish-failure"
                with patch.object(train.os, "replace", side_effect=OSError("technical write failure")):
                    with self.assertRaises(config.TrainerError):
                        train.run(SimpleNamespace(**partial_args, output_dir=publish_failure))
                self.assertFalse((publish_failure / "result.json").exists())
                self.assertFalse((publish_failure / ".result.part").exists())
                self.assertTrue((publish_failure / "step-000000002/receipt.json").is_file())
                previous = (partial / "step-000000002/state.pt").read_bytes()
                def withdrawn(*args, **kwargs):
                    if NumericEngine.last and NumericEngine.last.updates >= 3:
                        raise config.TrainerError("withdrawn")
                # Permit the initial pre-step check before the fresh engine is
                # created, then withdraw after this run's first checkpoint.
                NumericEngine.last = None
                authority.side_effect = withdrawn
                failed = directory / "failed"
                with self.assertRaises(config.TrainerError):
                    train.run(SimpleNamespace(**arguments, output_dir=failed))
                # Keep the earlier committed checkpoint after a later step's
                # authority failure, without publishing a completed result.
                self.assertFalse((failed / "result.json").exists())
                self.assertTrue((failed / "step-000000002/receipt.json").is_file())
                self.assertFalse((failed / "step-000000004").exists())
                self.assertEqual((partial / "step-000000002/state.pt").read_bytes(), previous)


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fdec-checkpoint-contract-")
        self.root = Path(self.temporary.name).resolve()
        self.addCleanup(self.cleanup)
        self.key = secrets.token_bytes(32)
        self.context = dict(schema="technical-checkpoint-context", config=dict(max_steps=10), source_sha256="a" * 64)
        self.writer = lambda state, path: path.write_text(json.dumps(state, allow_nan=False), encoding="utf-8")
        self.reader = lambda content: json.loads(content)

    def cleanup(self):
        if not self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not self.root.name.startswith("fdec-checkpoint-contract-") or self.root.is_symlink() or self.root.is_junction():
            raise AssertionError("unsafe_checkpoint_test_cleanup")
        self.temporary.cleanup()

    def save(self, name="state", state=None):
        return checkpoints.save(self.root / name, state={"numerical": [1, 2, 3]} if state is None else state, context=self.context, step=2, key=self.key, writer=self.writer, current_check=lambda: None)

    def load(self, name="state", **kwargs):
        return checkpoints.load(self.root / name, context=self.context, key=self.key, reader=self.reader, current_check=lambda: None, **kwargs)

    def test_numerical_state_resume_matches_uninterrupted_software_oracle(self):
        # Pure numerical state-machine oracle. This is neither torch nor Qwen
        # and must never be reported as supported-GPU acceptance.
        def initial():
            rng = random.Random(17)
            return dict(weight=.25, momentum=0.0, rng=rng.getstate())
        def update(state):
            rng = random.Random()
            old = state["rng"]
            rng.setstate((old[0], tuple(old[1]), old[2]))
            x = rng.random()
            gradient = 2 * (state["weight"] * x - math.sin(x)) * x
            state["momentum"] = .9 * state["momentum"] + gradient
            state["weight"] -= .01 * state["momentum"]
            state["rng"] = rng.getstate()
        whole, partial = initial(), initial()
        for _ in range(5):
            update(whole)
        for _ in range(2):
            update(partial)
        self.save(state=partial)
        step, restored = self.load()
        self.assertEqual(step, 2)
        for _ in range(step, 5):
            update(restored)
        self.assertEqual(restored["weight"], whole["weight"])
        self.assertEqual(restored["momentum"], whole["momentum"])
        self.assertEqual(tuple(restored["rng"][1]), whole["rng"][1])

    def test_hash_rebinding_signature_context_and_extras_reject_before_decoder(self):
        self.save()
        directory = self.root / "state"
        state = directory / "state.pt"
        prior = state.read_bytes()
        state.write_bytes(b'{"numerical":[999]}')
        decoder = Mock(side_effect=AssertionError("must not decode"))
        def rejected(context=None, key=None):
            with self.assertRaises(config.TrainerError):
                checkpoints.load(directory, context=context or self.context, key=key or self.key, reader=decoder, current_check=lambda: None)
            decoder.assert_not_called()
        rejected()
        # An attacker can change all unsigned hashes but cannot forge authority.
        original_metadata = (directory / "metadata.json").read_bytes()
        original_receipt = (directory / "receipt.json").read_bytes()
        metadata = json.loads(original_metadata)
        metadata.update(state_sha256=hashlib.sha256(state.read_bytes()).hexdigest(), state_bytes=len(state.read_bytes()))
        receipt = json.loads(original_receipt)
        receipt["payload"] = metadata
        (directory / "metadata.json").write_text(json.dumps(metadata))
        (directory / "receipt.json").write_text(json.dumps(receipt))
        rejected()
        (directory / "metadata.json").write_bytes(original_metadata)
        (directory / "receipt.json").write_bytes(original_receipt)
        state.write_bytes(prior)
        rejected(context=dict(self.context, source_sha256="b" * 64))
        rejected(key=b"x" * 32)
        (directory / "unexpected").write_bytes(b"extra")
        rejected()
        (directory / "unexpected").unlink()
        (directory / "receipt.json").unlink()
        rejected()

    def test_authority_change_and_write_failure_rollback_preserve_existing_checkpoint(self):
        self.save()
        prior = (self.root / "state/state.pt").read_bytes()
        with self.assertRaises(Exception):
            self.save()
        self.assertEqual((self.root / "state/state.pt").read_bytes(), prior)
        count = 0
        def withdrawn():
            nonlocal count
            count += 1
            if count >= 2:
                raise ValueError("withdrawn")
        with self.assertRaises(config.TrainerError):
            checkpoints.save(self.root / "withdrawn", state={}, context=self.context, step=2, key=self.key, writer=self.writer, current_check=withdrawn)
        self.assertFalse((self.root / "withdrawn").exists())
        def broken(state, path):
            path.write_bytes(b"partial")
            raise ValueError("write failure")
        with self.assertRaises(config.TrainerError):
            checkpoints.save(self.root / "broken", state={}, context=self.context, step=2, key=self.key, writer=broken, current_check=lambda: None)
        self.assertFalse((self.root / "broken").exists())
        self.assertEqual((self.root / "state/state.pt").read_bytes(), prior)


class TrainingAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "tests/d002"))
        import test_pipeline
        f = cls.fixture = test_pipeline.PipelineTests()
        cls.addClassCleanup(f.doCleanups)
        f.setUp()
        cls.directory, _ = f.build()
        cls.split = splits.verify(cls.directory, f.inventory, f.signed, key=f.key, policy_root=f.root, now=f.now, include_manifest=True)
        ids = sorted(row["record_id"] for row in cls.split["manifest"]["assignments"] if row["split"] == "train")
        rows = [dict(record_id=rid, language="en", classification=dict(schema_version="1", status="classified", topics=["work"], priority="normal", security=dict(spam="clear", phishing="clear", malware="clear"), suggested_action="review"), mask={head: True for head in DIMENSIONS}) for rid in ids]
        cls.annotations = dict(schema="fdec-training-annotations/v1", rows=rows)
        f.write("training/data/inventory.json", f.inventory)
        f.write("training/data/consent-snapshot.json", f.signed)
        f.write("training/data/training-annotations.json", cls.annotations)
        f.write("training/data/training-prompt.json", dict(schema="fdec-independent-training-prompt/v1", system="technical-protocol-token", origin="independently-reviewed-non-openai"))
        cls.arguments = dict(inventory_path=f.root / "training/data/inventory.json", consent_path=f.root / "training/data/consent-snapshot.json", split_dir=cls.directory, annotations_path=f.root / "training/data/training-annotations.json", prompt_path=f.root / "training/data/training-prompt.json", source_runs=f.runs, key=f.key, policy_root=f.root, now=f.now)
        cls.annotation_bytes = cls.arguments["annotations_path"].read_bytes()
        cls.prompt_bytes = cls.arguments["prompt_path"].read_bytes()
        payload = dict(schema="fdec-training-label-review/v1", inventory_sha256=splits.digest(f.inventory), consent_sha256=splits.digest(f.signed), split_receipt_sha256=splits.digest(cls.split["receipt"]), annotations_sha256=hashlib.sha256(cls.annotation_bytes).hexdigest(), prompt_sha256=hashlib.sha256(cls.prompt_bytes).hexdigest(), reviewer_kind="independently-reviewed-non-openai", evidence_sha256=splits.digest("counterfactual software review, not real authorship"), issued_at=test_pipeline.stamp(f.now - timedelta(minutes=1)), valid_until=test_pipeline.stamp(f.now + timedelta(minutes=20)))
        cls.review = dict(schema="fdec-signed-training-review/v1", payload=payload, hmac_sha256=hmac.new(f.key, inputs.DOMAIN + splits.canonical_json(payload).encode(), hashlib.sha256).hexdigest())
        f.write(inputs.REVIEW_ANCHOR, cls.review)

    def test_full_train_only_roundtrip(self):
        snapshot = inputs.admit(**self.arguments)
        ids = set(snapshot.texts)
        self.assertEqual(ids, {row["record_id"] for row in snapshot.rows})
        self.assertFalse(ids & {row["record_id"] for row in self.split["manifest"]["assignments"] if row["split"] != "train"})
        self.assertEqual(snapshot.system, "technical-protocol-token")

    def test_partial_heuristic_and_held_out_labels_reject(self):
        try:
            for change in ("partial", "held-out", "duplicate", "unknown"):
                changed = deepcopy(self.annotations)
                if change == "partial":
                    changed["rows"][0]["mask"]["malware"] = False
                elif change == "held-out":
                    changed["rows"][0]["record_id"] = next(row["record_id"] for row in self.split["manifest"]["assignments"] if row["split"] == "test")
                elif change == "duplicate":
                    changed["rows"].append(deepcopy(changed["rows"][0]))
                else:
                    changed["rows"][0]["classification"]["priority"] = "unknown"
                self.fixture.write("training/data/training-annotations.json", changed)
                with self.subTest(change=change):
                    with self.assertRaises(config.TrainerError):
                        inputs.admit(**self.arguments)
        finally:
            self.arguments["annotations_path"].write_bytes(self.annotation_bytes)

    def test_review_bindings_and_independent_prompt_required(self):
        f = self.fixture
        payload = self.review["payload"]
        for field, value in (("prompt_sha256", "b" * 64), ("annotations_sha256", "b" * 64), ("reviewer_kind", "codex"), ("valid_until", "2000-01-01T00:00:00Z")):
            changed = deepcopy(self.review)
            changed["payload"][field] = value
            changed["hmac_sha256"] = hmac.new(f.key, inputs.DOMAIN + splits.canonical_json(changed["payload"]).encode(), hashlib.sha256).hexdigest()
            with self.assertRaises(config.TrainerError):
                inputs.check_review(changed, f.inventory, f.signed, self.split, payload["annotations_sha256"], payload["prompt_sha256"], f.key, f.now)
        try:
            f.write("training/data/training-prompt.json", dict(schema="fdec-independent-training-prompt/v1", system="technical-token", origin="codex"))
            with self.assertRaises(config.TrainerError):
                inputs.admit(**self.arguments)
        finally:
            self.arguments["prompt_path"].write_bytes(self.prompt_bytes)
        for pack in inputs.boundary.FIXTURE_PACKS:
            with self.assertRaises(inputs.boundary.TrainingBoundaryError):
                inputs.boundary.prohibit_codex_training(pack, "codex", "commercial_training")

    def test_z_revocation_is_checked_on_reuse(self):
        f = self.fixture
        snapshot = inputs.admit(**self.arguments)
        changed = f.sign(revoke=snapshot.rows[0]["record_id"], revision=2, previous=splits.digest(f.signed))
        splits.activate_consent(f.inventory, changed, key=f.key, policy_root=f.root, now=f.now)
        with self.assertRaises(config.TrainerError):
            inputs.recheck(snapshot, key=f.key, policy_root=f.root, now=f.now)
        with self.assertRaises(config.TrainerError):
            inputs.admit(**self.arguments)


if __name__ == "__main__":
    unittest.main()
