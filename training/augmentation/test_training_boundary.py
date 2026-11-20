"""Permitted technical fixtures only; no example becomes actual training data."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import augment as a
import training_boundary as b
import ingest_dataset as ingestion
import test_ingestion as ingestion_fixture
import pyarrow as pa
import pyarrow.parquet as pq


class TrainingBoundaryTests(unittest.TestCase):
    def setUp(self):
        # Reuse the actual ingestion fixture builder and guard, not a mock grant
        # in the production policy. Its root cannot be selected through a CLI.
        self.fixture = ingestion_fixture.IngestionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.fixture.admit((a.canonical(self.fixture.sample()) + "\n").encode())
        self.receipt = ingestion.ingest(**self.fixture.arguments)
        self.run = Path(self.fixture.arguments["output_dir"])
        self.policy = self.make_policy(self.receipt)
        self.save_policy()

    def binding(self, relative):
        return dict(path=relative, sha256=b.text_hash(self.root / relative))

    def make_policy(self, receipt):
        usage = self.root / "training/augmentation/DATA-USAGE-v2.md"
        usage.parent.mkdir(parents=True, exist_ok=True)
        usage.write_bytes((a.ROOT / "training/augmentation/DATA-USAGE-v2.md").read_bytes())
        return dict(schema="fdec-independent-training-sources/v1", scope="specialized-email-classifier", codex_data_usage="software_fixture_only", policy_evidence=self.binding("training/augmentation/DATA-USAGE-v2.md"), sources=[dict(identity={name: receipt["input"][name] for name in ("dataset_id", "revision", "artifact", "sha256")}, authoring_provider="human-authored-reviewed", openai_derived=False, allowed_purposes=["commercial_training", "evaluation"], evidence=[self.binding(path) for path in ("docs/legal/datasets/audit.json", "docs/legal/datasets/observations.json", "docs/legal/datasets/report.md")])])

    def save_policy(self):
        path = self.root / b.POLICY_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(a.canonical(self.policy), encoding="utf-8")

    def admit(self, **options):
        return b.admit_training_run(self.run, policy_root=self.root, **options)

    def write_receipt(self, receipt):
        (self.run / "receipt.json").write_text(a.canonical(receipt) + "\n", encoding="utf-8")

    def test_independent_ingestion_bytes_and_labels_have_verified_snapshot(self):
        original = (self.run / "records.jsonl").read_bytes()
        result = self.admit(include_records=True)
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["records_sha256"], self.receipt["records_sha256"])
        self.assertEqual(result["source"]["descriptor"], self.receipt["input"])
        self.assertTrue(result["requires_split_and_consent"])
        self.assertEqual(result["scope"], "source-integrity-and-origin-only")
        result["records"][0]["body"] = "changed technical token"
        self.assertEqual((self.run / "records.jsonl").read_bytes(), original)

    def test_real_production_independent_source_metadata_uses_existing_audit(self):
        policy = b.read_json(a.ROOT / b.POLICY_PATH)
        identity = policy["sources"][0]["identity"]
        for purpose in b.PURPOSES:
            result = b.assert_training_source(identity, purpose=purpose)
            self.assertEqual(result["descriptor"]["dataset_id"], "weijianzhg/email-triage-action-seed")
            self.assertEqual(result["descriptor"]["purpose"], purpose)
            self.assertEqual(result["authoring_provider"], "anthropic-via-openrouter-uploader-declared")
        for dataset_id in ("imnim/multiclass-email-classification", "talby/spamassassin"):
            with self.assertRaises(b.TrainingBoundaryError):
                b.assert_training_source(dict(identity, dataset_id=dataset_id), purpose="commercial_training")

    def test_actual_pinned_parquet_decoder_replays_independent_snapshot(self):
        buffer = pa.BufferOutputStream()
        pq.write_table(pa.Table.from_pylist([self.fixture.sample(), self.fixture.sample()]), buffer)
        self.fixture.admit(buffer.getvalue().to_pybytes(), ".parquet")
        self.fixture.arguments["output_dir"] = self.root / "training/data/parquet"
        self.receipt = ingestion.ingest(**self.fixture.arguments)
        self.run = Path(self.fixture.arguments["output_dir"])
        self.policy = self.make_policy(self.receipt)
        self.save_policy()
        result = self.admit(include_records=True)
        self.assertEqual(result["rows"], 1)
        self.assertEqual(len(result["records"][0]["annotations"]), 2)

    def test_both_codex_run_types_and_their_annotation_streams_are_not_training(self):
        plan = dict(schema="fdec-augmentation-plan/v1", seed=7, quotas=[dict(language="en", topic="work", target=1, observed=0)])
        for pack in b.FIXTURE_PACKS:
            directory = self.fixture.base / pack
            a.generate(plan, output_dir=directory, pack_id=pack, purpose="software_fixture", opt_in=True)
            annotation = json.loads((directory / "annotations.jsonl").read_text())
            self.assertEqual(annotation["schema"], "fdec-augmentation-annotation/v1")
            self.assertEqual(annotation["data_usage"]["purpose"], "software_fixture")
            self.assertFalse(annotation["data_usage"]["training_allowed"])
            with patch.object(b, "assert_training_source") as guard, self.assertRaisesRegex(b.TrainingBoundaryError, "technical_fixture_not_training_data"):
                b.admit_training_run(directory, policy_root=self.root)
            guard.assert_not_called()

    def test_accidental_matching_audit_and_registry_promotion_cannot_allow_codex(self):
        parent = a.ROOT / "training/outputs"
        with tempfile.TemporaryDirectory(prefix="boundary-promotion-", dir=parent) as temporary:
            directory = Path(temporary).resolve()
            self.assertTrue(directory.is_relative_to(parent))
            self.assertFalse(directory.is_symlink() or directory.is_junction())
            original = a.read_json(a.REGISTRY)
            for index, original_entry in enumerate(original["packs"]):
                for renamed in (False, True):
                    audit = a.read_json(a.ROOT / original_entry["audit"]["path"])
                    entry = deepcopy(original_entry)
                    if renamed:
                        entry["id"] = "renamed-codex-fixture"
                        audit["pack_id"] = entry["id"]
                    purposes = ["software_fixture", "commercial_training", "evaluation"]
                    audit["allowed_purposes"] = purposes
                    entry["allowed_purposes"] = purposes
                    path = directory / f"audit-{index}-{renamed}.json"
                    path.write_text(a.canonical(audit), encoding="utf-8")
                    entry["audit"] = dict(path=path.relative_to(a.ROOT).as_posix(), sha256=a.file_hash(path))
                    registry = directory / "registry.json"
                    registry.write_text(a.canonical(dict(schema="fdec-augmentation-sources/v1", packs=[entry])), encoding="utf-8")
                    with patch.object(a, "REGISTRY", registry):
                        for purpose in b.PURPOSES:
                            with self.subTest(pack=entry["id"], purpose=purpose), self.assertRaisesRegex(a.AugmentationError, "template_training_rights_not_approved"):
                                a.load_pack(entry["id"], purpose)

    def test_openai_origin_or_unknown_provider_denied_despite_source_license(self):
        for mutate in (lambda e: e.update(openai_derived=True), lambda e: e.update(authoring_provider="openai"), lambda e: e.update(authoring_provider="unknown")):
            policy = deepcopy(self.policy)
            mutate(self.policy["sources"][0])
            self.save_policy()
            with self.assertRaisesRegex(b.TrainingBoundaryError, "independent_source_origin_not_admitted"):
                self.admit()
            self.policy = policy

    def test_changed_rights_evidence_and_duplicate_source_policy_denied(self):
        report = self.root / "docs/legal/datasets/report.md"
        report.write_text("Changed isolated technical audit", encoding="utf-8")
        with self.assertRaisesRegex(b.TrainingBoundaryError, "independent_source_evidence_changed"):
            self.admit()
        self.policy["sources"].append(deepcopy(self.policy["sources"][0]))
        self.save_policy()
        with self.assertRaisesRegex(b.TrainingBoundaryError, "duplicate_independent_source"):
            self.admit()

    def test_changed_raw_bytes_are_rejected_before_parser_without_mutation(self):
        raw = self.run / self.receipt["source_file"]
        raw.write_bytes(b"technical changed source")
        changed = raw.read_bytes()
        with patch.object(ingestion, "rows") as parser, self.assertRaisesRegex(b.TrainingBoundaryError, "training_source_checksum_mismatch"):
            self.admit()
        parser.assert_not_called()
        self.assertEqual(raw.read_bytes(), changed)

    def test_copied_text_or_labels_cannot_be_laundered_by_updating_checksum(self):
        path = self.run / "records.jsonl"
        original = json.loads(path.read_text())
        for mutate in (lambda row: row.update(body="copied technical fixture token"), lambda row: row["annotations"][0]["labels"].update(action="reply")):
            row = deepcopy(original)
            mutate(row)
            content = (a.canonical(row) + "\n").encode()
            path.write_bytes(content)
            receipt = deepcopy(self.receipt)
            receipt["records_sha256"] = hashlib.sha256(content).hexdigest()
            self.write_receipt(receipt)
            with self.assertRaisesRegex(b.TrainingBoundaryError, "normalized_training_text_or_labels_changed"):
                self.admit()
            self.assertEqual(path.read_bytes(), content)

    def test_parsing_uses_verified_bytes_even_if_file_changes_after_snapshot(self):
        parser = ingestion.rows
        raw = self.run / self.receipt["source_file"]
        original_body = self.fixture.sample()["body"]
        def alter_disk_after_snapshot(snapshot):
            raw.write_bytes(b"modified after snapshot")
            return parser(snapshot)
        with patch.object(ingestion, "rows", side_effect=alter_disk_after_snapshot):
            result = self.admit(include_records=True)
        self.assertEqual(result["records"][0]["body"], original_body)
        self.assertEqual(raw.read_bytes(), b"modified after snapshot")

    def test_changed_receipt_counters_implementation_purpose_or_paths_fail(self):
        for change in (dict(input_rows=True), dict(implementation_sha256="0" * 64), dict(source_file="../outside"), dict(records_file="outside.jsonl"), dict(decoder="unapproved"), dict(schema="fdec-native-augmentation-receipt/v1")):
            self.write_receipt(dict(self.receipt, **change))
            with self.subTest(field=next(iter(change))), self.assertRaises(b.TrainingBoundaryError):
                self.admit()
        self.write_receipt(self.receipt)
        with self.assertRaisesRegex(b.TrainingBoundaryError, "training_ingestion_purpose_changed"):
            self.admit(purpose="evaluation")

    def test_unlisted_revisions_and_changed_artifacts_have_no_admission(self):
        original = deepcopy(self.receipt)
        for change in (dict(revision="main"), dict(artifact="unapproved.jsonl"), dict(sha256="0" * 64)):
            modified = deepcopy(original)
            modified["input"].update(change)
            self.write_receipt(modified)
            with self.assertRaisesRegex(b.TrainingBoundaryError, "unapproved_independent_source"):
                self.admit()

    def test_missing_corrupt_or_linked_proofs_fail_without_data_logging(self):
        receipt_path = self.run / "receipt.json"
        for content in (b"", b"private technical sentinel", b'{"schema":"one","schema":"two"}', b"\xff"):
            receipt_path.write_bytes(content)
            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(output), self.assertRaises(b.TrainingBoundaryError) as error:
                self.admit()
            self.assertRegex(str(error.exception), r"^[a-z_]+$")
            self.assertEqual(output.getvalue(), "")
        self.write_receipt(self.receipt)
        link = self.fixture.base / "linked-run"
        link.symlink_to(self.run, target_is_directory=True)
        with self.assertRaises(b.TrainingBoundaryError):
            b.admit_training_run(link, policy_root=self.root)


if __name__ == "__main__":
    unittest.main()
