"""End-to-end guarded compact input fixtures. No actual model runs."""

from copy import deepcopy
from datetime import timedelta
import hashlib
import hmac
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
for area in ("training/finetune", "training/baseline", "training/eval", "training/export", "tests/d002"):
    sys.path.append(str(ROOT / area))

import admission
import baseline
import disk_inventory
import evaluate
import lineage
import mlx_handoff
import split_data as splits
import test_pipeline
import train
import training_inputs
from baseline_metrics import DIMENSIONS, EvaluationError
from trainer_config import TrainerError


@unittest.skipUnless(os.name == "posix", "Compact inventories require private POSIX storage")
class CompactInputTests(unittest.TestCase):
    def setUp(self):
        fixture = self.fixture = test_pipeline.PipelineTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()

    def sign(self, inventory, previous, *, revoke=None):
        fixture = self.fixture
        payload = deepcopy(previous["payload"])
        payload.update(revision=payload["revision"] + 1, previous_snapshot_sha256=splits.digest(previous),
                       inventory_sha256=splits.inventory_digest(inventory))
        for grant in payload["grants"]:
            if grant["record_id"] == revoke:
                grant["status"] = "revoked"
        signed = splits.envelope(payload, fixture.key)
        splits.activate_consent(inventory, signed, key=fixture.key, policy_root=fixture.root, now=fixture.now)
        return signed

    def prepare(self, *, change_fingerprint=False):
        f = self.fixture
        records = deepcopy(f.inventory["records"])
        if change_fingerprint:
            hashes = records[0]["shingles"]
            replacement = splits.digest("altered fixture fingerprint")
            self.assertNotIn(replacement, hashes)
            records[0]["shingles"] = sorted(hashes[1:] + [replacement])
        path = f.root / "training/data/packed"
        disk_inventory.pack(iter(records), output_dir=path, opt_in=True, policy_root=f.root)
        self.inventory = splits.read_inventory(path)
        self.identity = splits.inventory_digest(self.inventory)
        self.signed = self.sign(self.inventory, f.signed)
        split_path = f.root / "training/outputs/split"
        self.receipt = splits.build(self.inventory, self.signed, output_dir=split_path, key=f.key,
                                    seed=19, ratios=dict(train=10, validation=10, test=80),
                                    opt_in=True, policy_root=f.root, now=f.now)
        manifest = splits.read_json(split_path / "manifest.json")
        f.write("training/data/consent-snapshot.json", self.signed)
        prompt = f.root / "training/data/prompt.json"
        f.write("training/data/prompt.json", dict(schema="fdec-independent-training-prompt/v1",
                system="technical fixture", origin="independently-reviewed-non-openai"))
        self.common = dict(inventory_path=path, consent_path=f.root / "training/data/consent-snapshot.json",
                           split_dir=split_path, source_runs=f.runs, key=f.key, policy_root=f.root, now=f.now)
        self.roles = {}
        for role in ("train", "test"):
            ids = self.roles[role] = {row["record_id"] for row in manifest["assignments"] if row["split"] == role}
            rows = [dict(record_id=identifier, language=("en", "de")[index % 2],
                         classification=dict(schema_version="1", status="classified", topics=["work"],
                                             priority="normal", security=dict(spam="clear", phishing="clear", malware="clear"),
                                             suggested_action="review"),
                         mask=dict.fromkeys(DIMENSIONS, True)) for index, identifier in enumerate(sorted(ids))]
            area = "training" if role == "train" else "baseline"
            annotations = f.root / f"training/data/{area}-annotations.json"
            f.write(f"training/data/{area}-annotations.json", dict(schema=f"fdec-{area}-annotations/v1", rows=rows))
            payload = dict(schema=f"fdec-{area}-label-review/v1", inventory_sha256=self.identity,
                           consent_sha256=splits.digest(self.signed), split_receipt_sha256=splits.digest(self.receipt),
                           annotations_sha256=hashlib.sha256(annotations.read_bytes()).hexdigest(),
                           reviewer_kind="independently-reviewed-non-openai",
                           evidence_sha256=splits.digest("synthetic review fixture"),
                           issued_at=test_pipeline.stamp(f.now - timedelta(minutes=1)),
                           valid_until=test_pipeline.stamp(f.now + timedelta(minutes=10)))
            args = dict(self.common, annotations_path=annotations)
            if role == "train":
                args["prompt_path"] = prompt
                payload["prompt_sha256"] = hashlib.sha256(prompt.read_bytes()).hexdigest()
                domain, anchor = training_inputs.DOMAIN, training_inputs.REVIEW_ANCHOR
                self.train_args = args
            else:
                domain, anchor = admission.REVIEW_DOMAIN, admission.REVIEW_ANCHOR
                self.test_args = args
            f.write(anchor, dict(schema=f"fdec-signed-{area}-review/v1", payload=payload,
                                 hmac_sha256=hmac.new(f.key, domain + splits.canonical_json(payload).encode(), hashlib.sha256).hexdigest()))

    def test_real_admission_role_isolation_and_checkpoint_report_identities(self):
        self.prepare()
        f = self.fixture
        training = training_inputs.admit(**self.train_args)
        held_out = admission.admit(**self.test_args)
        self.assertEqual(set(training.texts), self.roles["train"])
        self.assertEqual(set(held_out.texts), self.roles["test"])
        self.assertFalse(set(training.texts) & set(held_out.texts))
        self.assertEqual(lineage.provenance(training)["inventory_sha256"], self.identity)
        self.assertEqual(train.run_context({}, SimpleNamespace(identity={}), training, "mlx")["inventory_sha256"], self.identity)

        for relative in (mlx_handoff.PROFILE, "training/baseline/qwen-stock-v1.json"):
            f.write(relative, splits.read_json(ROOT / relative))
        subprocess.run(["git", "-C", str(f.root), "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(f.root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "-m", "Isolated handoff fixture"], check=True, capture_output=True)
        handoff_inputs = {name: value for name, value in self.train_args.items() if name != "key"}
        with patch.object(splits, "authority_key", return_value=f.key):
            mlx_handoff.prepare(f.base / "handoff", purpose="actual-training", inputs=handoff_inputs,
                                config_path=ROOT / "training/config/mlx-trainer-v1.json", root=f.root)
        kit = mlx_handoff.Handoff(f.base / "handoff", root=f.root)
        self.assertEqual(kit.manifest["input_manifest_hashes"]["inventory"], self.identity)
        self.assertEqual(kit.manifest["input_manifest_hashes"]["split"], splits.digest(self.receipt))

        for consumer in (baseline, evaluate):
            with self.subTest(consumer=consumer.__name__):
                output = f.base / consumer.__name__
                args = SimpleNamespace(opt_in=True, output_dir=output, inventory=self.common["inventory_path"],
                                       consent=self.common["consent_path"], split_dir=self.common["split_dir"],
                                       annotations=self.test_args["annotations_path"], source_run=f.runs, model_dir=f.base)
                model = Mock(identity={"id": "technical-fixture"})
                model.infer.return_value = splits.canonical_json(held_out.gold[0]["classification"])
                with patch.object(consumer, "admit", side_effect=lambda **values: admission.admit(**values, policy_root=f.root, now=f.now)), \
                     patch.object(consumer, "recheck", side_effect=lambda snapshot, key: admission.recheck(snapshot, key=key, policy_root=f.root, now=f.now)), \
                     patch.object(consumer, "LocalQwen", return_value=model), patch.object(splits, "authority_key", return_value=f.key):
                    self.assertEqual(consumer.run(args)["status"], "measured")
                self.assertEqual(model.infer.call_count, len(self.roles["test"]))
                self.assertEqual(splits.read_json(output / "metrics.json")["inventory_sha256"], self.identity)

        self.sign(self.inventory, self.signed, revoke=next(iter(self.roles["test"])))
        with self.assertRaisesRegex(TrainerError, "training_authority_changed"):
            training_inputs.recheck(training, key=f.key, policy_root=f.root, now=f.now)
        with self.assertRaisesRegex(EvaluationError, "held_out_authority_changed"):
            admission.recheck(held_out, key=f.key, policy_root=f.root, now=f.now)

    def test_signed_but_incorrect_packed_fingerprint_is_rejected_by_both_roles(self):
        self.prepare(change_fingerprint=True)
        with self.assertRaisesRegex(TrainerError, "training_text_binding_changed"):
            training_inputs.admit(**self.train_args)
        with self.assertRaisesRegex(EvaluationError, "inventory_text_binding_changed"):
            admission.admit(**self.test_args)
