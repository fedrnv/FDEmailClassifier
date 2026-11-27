"""Exercise the Gemma cohort in the existing signed software fixture."""

import hashlib
import json
import shutil
from unittest.mock import patch

import test_finetune as trainer_tests
import gemma_source

splits = trainer_tests.splits
inputs = trainer_tests.inputs
TrainerError = trainer_tests.config.TrainerError


class GemmaAdmissionTests(trainer_tests.TrainingAdmissionTests):
    @classmethod
    def prepare_fixture(cls, fixture):
        for name in ("verification-v1.md", "aggregate-v1.json"):
            relative = gemma_source.EVIDENCE / name
            target = fixture.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(trainer_tests.ROOT / relative, target)
        payloads = (
            {"subject": "Fixture subject", "body": "One software protocol phrase."},
            {"subject": "Other fixture subject", "body": "A different technical token set."},
            {"subject": "Rejected fixture", "body": "synthetic@example.invalid"},
            {"subject": "Extra field fixture", "body": "Synthetic token", "closing": "test"},
        )
        sample = [
            {"id": index, "instruction": "technical fixture only", "output": json.dumps(record)}
            for index, record in enumerate(payloads)
        ]
        raw = "".join(json.dumps(item) + "\n" for item in sample).encode()
        identity = dict(gemma_source.IDENTITY, sha256=hashlib.sha256(raw).hexdigest())
        for mocked in (patch.object(gemma_source, "IDENTITY", identity),
                       patch.object(gemma_source, "SIZE", len(raw))):
            mocked.start()
            cls.addClassCleanup(mocked.stop)
        path = fixture.base / "gemma-fixture.jsonl"
        path.write_bytes(raw)
        cls.source_run = fixture.root / "training/data/gemma-run"
        gemma_source.create_run(path, cls.source_run, purpose="commercial_training", policy_root=fixture.root)
        receipt, records = gemma_source.replay(raw, purpose="commercial_training", policy_root=fixture.root)
        cls.projected = [
            splits.prepare_record(row, receipt, consent_id=splits.digest(row["content_id"]))
            for row in records
        ]
        fixture.runs.append(cls.source_run)
        fixture.inventory["records"].extend(cls.projected)
        fixture.signed = fixture.sign(revision=2, previous=splits.digest(fixture.signed))
        splits.activate_consent(fixture.inventory, fixture.signed, key=fixture.key,
                                policy_root=fixture.root, now=fixture.now)

    def test_projection_is_screened_and_indivisible(self):
        snapshot = inputs.admit(**self.arguments)
        self.assertEqual(len(self.projected), 2)
        ids = {row["record_id"] for row in self.projected}
        roles = {row["split"] for row in snapshot.split["manifest"]["assignments"]
                 if row["record_id"] in ids}
        self.assertEqual(len(roles), 1)

    def test_changed_source_or_receipt_rejected_before_training(self):
        for name in ("source.jsonl", "receipt.json"):
            with self.subTest(name=name):
                path = self.source_run / name
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b"x")
                    with self.assertRaises(TrainerError):
                        inputs.admit(**self.arguments)
                finally:
                    path.write_bytes(original)

    def test_changed_audit_rejected_before_training(self):
        for name in ("verification-v1.md", "aggregate-v1.json"):
            with self.subTest(name=name):
                path = self.fixture.root / gemma_source.EVIDENCE / name
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b"x")
                    with self.assertRaises(TrainerError):
                        inputs.admit(**self.arguments)
                finally:
                    path.write_bytes(original)

    def test_z_revocation_is_checked_on_reuse(self):
        fixture = self.fixture
        snapshot = inputs.admit(**self.arguments)
        changed = fixture.sign(revoke=self.projected[0]["record_id"], revision=3,
                               previous=splits.digest(fixture.signed))
        splits.activate_consent(fixture.inventory, changed, key=fixture.key,
                                policy_root=fixture.root, now=fixture.now)
        with self.assertRaises(TrainerError):
            inputs.recheck(snapshot, key=fixture.key, policy_root=fixture.root, now=fixture.now)
