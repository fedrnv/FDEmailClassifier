"""D002 software integration only: generated tokens, simulated rights/consent.

Counterfactual fixture policies are isolated from the production registry and
cannot be selected through production CLIs. No model consumes any fixture row.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
for area in ("training/scripts", "training/labels", "training/splits", "training/augmentation"):
    sys.path.insert(0, str(ROOT / area))
import ingest_dataset as ingestion
from normalize_email import canonical_json
import map_annotations as labels
import split_data as splits
import augment
import training_boundary as boundary
import sinabis_source as sinabis
import pyarrow as pa
import pyarrow.parquet as pq


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stamp(value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fdec-d002-pipeline-")
        self.base = Path(self.temporary.name).resolve()
        self.addCleanup(self.cleanup)
        self.root = self.base / "policy"
        self.root.mkdir()
        subprocess.run(["git", "-C", str(self.root), "init", "--quiet"], check=True, capture_output=True)
        (self.root / ".gitignore").write_text("/training/data/\n/training/outputs/\n", encoding="utf-8")
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.key = secrets.token_bytes(32)
        self.sources, observations, decisions, selections = [], [], [], []
        for number, suffix in enumerate((".parquet", ".jsonl", ".eml")):
            rows = [dict(subject=f"Gate token {index}", body="technical software fixture " + sha(f"{number}:{index}".encode()) * 2) for index in range(2 if number == 0 else 1)]
            if suffix == ".parquet":
                buffer = pa.BufferOutputStream()
                pq.write_table(pa.Table.from_pylist(rows), buffer)
                payload = buffer.getvalue().to_pybytes()
            elif suffix == ".jsonl":
                payload = ("\n".join(canonical_json(row) for row in rows) + "\n").encode()
            else:
                message = EmailMessage()
                message["Subject"] = rows[0]["subject"]
                message["From"] = "fixture@mail.invalid"
                message.set_content(rows[0]["body"])
                message.add_attachment(b"software attachment token", maintype="application", subtype="octet-stream", filename="fixture.bin")
                payload = message.as_bytes()
            artifact = dict(path="rows" + suffix, git_blob_sha1=hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest(), sha256=sha(payload), size=len(payload))
            observed = dict(id=f"fixture/gate-source-{number}", revision="a" * 40, declared_license="MIT", provenance="uploader-declared-synthetic", artifacts=[artifact])
            observations.append(observed)
            decisions.append({**{key: observed[key] for key in ("id", "revision", "declared_license", "artifacts")}, "status": "allowed", "scope": "specialized-email-classifier", "allowed_purposes": ["commercial_training", "evaluation"], "reason": "Counterfactual software policy only; no real-world ownership or dataset approval"})
            selections.append(dict(id=observed["id"], revision=observed["revision"]))
            source_path = self.base / f"source-{number}{suffix}"
            source_path.write_bytes(payload)
            self.sources.append(dict(dataset_id=observed["id"], revision=observed["revision"], artifact=artifact["path"], sha256=artifact["sha256"], input_path=source_path))
        self.write("docs/legal/datasets/observations.json", dict(schema="fdec-dataset-observations/v1", datasets=observations))
        (self.root / "docs/legal/datasets/report.md").write_text("Software-only counterfactual rights/provider policy. Simulated reviewed origin and grants; not real authorship, permission or training-data approval.\n", encoding="utf-8")
        audit = dict(schema="fdec-dataset-audit/v1", reviewed_at=stamp(self.now), reviewer="software-fixture", observations=self.binding("docs/legal/datasets/observations.json"), report=self.binding("docs/legal/datasets/report.md"), decisions=decisions)
        self.write("docs/legal/datasets/audit.json", audit)
        self.write("training/datasets/allowlist.json", dict(schema="fdec-dataset-allowlist/v1", audit=self.binding("docs/legal/datasets/audit.json"), datasets=selections))
        usage = self.root / "training/augmentation/DATA-USAGE-v2.md"
        usage.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / "training/augmentation/DATA-USAGE-v2.md", usage)
        evidence = [self.binding(path) for path in ("docs/legal/datasets/audit.json", "docs/legal/datasets/observations.json", "docs/legal/datasets/report.md")]
        entries = [dict(identity={key: source[key] for key in ("dataset_id", "revision", "artifact", "sha256")}, authoring_provider="human-authored-reviewed", openai_derived=False, allowed_purposes=["commercial_training", "evaluation"], evidence=evidence) for source in self.sources]
        self.write(boundary.POLICY_PATH, dict(schema="fdec-independent-training-sources/v1", scope="specialized-email-classifier", codex_data_usage="software_fixture_only", policy_evidence=self.binding("training/augmentation/DATA-USAGE-v2.md"), sources=entries))
        self.runs, self.receipts, self.snapshots, records = [], [], [], []
        for number, source in enumerate(self.sources):
            run = self.root / f"training/data/source-{number}"
            receipt = ingestion.ingest(**{key: source[key] for key in ("dataset_id", "revision", "artifact", "input_path")}, purpose="commercial_training", target="specialized-email-classifier", output_dir=run, opt_in=True, policy_root=self.root)
            admitted = boundary.admit_training_run(run, policy_root=self.root, include_records=True)
            self.runs.append(run)
            self.receipts.append(receipt)
            self.snapshots.append(admitted)
            for normalized in admitted["records"]:
                prepared = splits.prepare_record(normalized, receipt, consent_id=splits.digest(["fixture-consent", source["dataset_id"], normalized["content_id"]]), thread_id=splits.digest("fixture-thread") if number == 0 else None)
                records.append(prepared)
        self.inventory = dict(schema="fdec-split-inventory/v1", normalization_version=splits.NORMALIZATION_VERSION, feature_policy=deepcopy(splits.FEATURE_POLICY), records=records)
        self.signed = self.sign()
        splits.activate_consent(self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now)

    def cleanup(self):
        if not self.base.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not self.base.name.startswith("fdec-d002-pipeline-") or self.base.is_symlink() or self.base.is_junction():
            raise AssertionError("unsafe_pipeline_fixture_cleanup")
        self.temporary.cleanup()

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(value) + "\n", encoding="utf-8")

    def binding(self, relative):
        return dict(path=relative, sha256=sha((self.root / relative).read_bytes().replace(b"\r\n", b"\n")))

    def sign(self, *, revoke=None, revision=1, previous=None):
        grants = [dict(record_id=row["record_id"], consent_id=row["consent_id"], evidence_sha256=splits.digest(["simulated-grant", row["record_id"]]), status="revoked" if row["record_id"] == revoke else "granted", purposes=["commercial_training", "evaluation"], expires_at=stamp(self.now + timedelta(minutes=30))) for row in self.inventory["records"]]
        payload = dict(schema="fdec-consent-ledger/v1", revision=revision, previous_snapshot_sha256=previous, inventory_sha256=splits.digest(self.inventory), issued_at=stamp(self.now - timedelta(minutes=1)), valid_until=stamp(self.now + timedelta(hours=1)), grants=grants)
        return splits.envelope(payload, self.key)

    def build(self, name="split"):
        path = self.root / "training/outputs" / name
        receipt = splits.build(self.inventory, self.signed, output_dir=path, key=self.key, seed=19, opt_in=True, policy_root=self.root, now=self.now)
        verified = splits.verify(path, self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now, include_manifest=True)
        self.assertEqual(verified["receipt"], receipt)
        return path, verified["manifest"]

    def test_verified_formats_annotation_join_and_signed_split_round_trip(self):
        path, manifest = self.build()
        self.assertEqual(len(self.inventory["records"]), 4)
        self.assertEqual({row["split"] for row in manifest["assignments"]}, {"train", "validation", "test"})
        source_roles, thread_roles = {}, set()
        for record in self.inventory["records"]:
            assigned, = [item for item in manifest["assignments"] if item["record_id"] == record["record_id"]]
            source_roles.setdefault(record["source"]["dataset_id"], set()).add(assigned["split"])
            if record["thread_id"]:
                thread_roles.add(assigned["split"])
        self.assertTrue(all(len(roles) == 1 for roles in source_roles.values()))
        self.assertEqual(len(thread_roles), 1)
        for snapshot in self.snapshots:
            for normalized in snapshot["records"]:
                annotations = [dict(source_row=0, labels=dict(category="work", priority="normal", action="review", security="normal"))]
                encoded = (canonical_json(annotations) + "\n").encode()
                annotation_source = dict(dataset_id="fdec/canonical-annotations", revision="1", artifact="annotations.jsonl", sha256=sha(encoded))
                mapped = labels.map_annotations(content_id=normalized["content_id"], source=annotation_source, annotations=annotations)
                labels.validate_projection(mapped["classification"])
                self.assertEqual(mapped["content_id"], normalized["content_id"])
                self.assertEqual(mapped["source"]["sha256"], sha(encoded))
                self.assertTrue(mapped["training_mask"]["topics"])
                self.assertFalse(mapped["training_mask"]["malware"])
                self.assertTrue(any(row["content_sha256"] == normalized["content_id"] for row in self.inventory["records"]))
        raw_manifest = (path / "manifest.json").read_text()
        self.assertNotIn('"body"', raw_manifest)
        self.assertNotIn('"subject"', raw_manifest)

    def test_changed_labels_and_rebound_checksum_reject_before_reuse(self):
        path, _ = self.build()
        before = (path / "manifest.json").read_bytes()
        run = self.runs[0]
        records = [json.loads(line) for line in (run / "records.jsonl").read_text().splitlines()]
        records[0]["annotations"][0]["labels"]["category"] = "finance"
        data = ("\n".join(canonical_json(row) for row in records) + "\n").encode()
        (run / "records.jsonl").write_bytes(data)
        receipt = deepcopy(self.receipts[0])
        receipt["records_sha256"] = sha(data)
        (run / "receipt.json").write_text(canonical_json(receipt), encoding="utf-8")
        with self.assertRaisesRegex(boundary.TrainingBoundaryError, "normalized_training_text_or_labels_changed"):
            boundary.admit_training_run(run, policy_root=self.root, include_records=True)
        self.assertEqual((path / "manifest.json").read_bytes(), before)
        self.assertEqual((run / "records.jsonl").read_bytes(), data)

    def test_current_revocation_invalidates_old_split_without_overwrite(self):
        path, _ = self.build()
        before = (path / "manifest.json").read_bytes()
        updated = self.sign(revoke=self.inventory["records"][0]["record_id"], revision=2, previous=splits.digest(self.signed))
        splits.activate_consent(self.inventory, updated, key=self.key, policy_root=self.root, now=self.now)
        with self.assertRaisesRegex(splits.SplitError, "consent_snapshot_no_longer_current"):
            splits.verify(path, self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now)
        with self.assertRaises(splits.SplitError):
            splits.build(self.inventory, updated, output_dir=self.root / "training/outputs/revoked", key=self.key, opt_in=True, policy_root=self.root, now=self.now)
        self.assertFalse((self.root / "training/outputs/revoked").exists())
        self.assertEqual((path / "manifest.json").read_bytes(), before)

    def test_rebound_split_assignment_and_untrusted_annotation_remain_invalid(self):
        path, manifest = self.build()
        manifest["assignments"][0]["split"] = "test" if manifest["assignments"][0]["split"] != "test" else "train"
        data = (canonical_json(manifest) + "\n").encode()
        (path / "manifest.json").write_bytes(data)
        receipt = json.loads((path / "receipt.json").read_text())
        receipt["manifest_sha256"] = sha(data)
        (path / "receipt.json").write_text(canonical_json(receipt), encoding="utf-8")
        with self.assertRaisesRegex(splits.SplitError, "provenance_or_contamination"):
            splits.verify(path, self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now)
        normalized = self.snapshots[0]["records"][0]
        source = dict(dataset_id="fdec/canonical-annotations", revision="1", artifact="annotations.jsonl", sha256=sha(b"software-annotation-fixture"))
        mapped = labels.map_annotations(content_id=normalized["content_id"], source=source, annotations=[dict(source_row=0, labels=dict(category="work")), dict(source_row=1, labels=dict(category="finance"))])
        self.assertFalse(mapped["training_mask"]["topics"])


class FixtureBoundaryInteractions(unittest.TestCase):
    def test_generation_translation_outputs_cannot_enter_training_or_split_ingestion(self):
        with tempfile.TemporaryDirectory(prefix="fdec-d002-codex-") as directory:
            base = Path(directory)
            for pack in boundary.FIXTURE_PACKS:
                output = base / pack
                plan = dict(schema="fdec-augmentation-plan/v1", seed=7, quotas=[dict(language="en", topic="work", target=2, observed=0)])
                receipt = augment.generate(plan, output_dir=output, pack_id=pack, purpose="software_fixture", opt_in=True)
                capsules = augment.read_capsules(output / "capsules.jsonl")
                translated = augment.translate(capsules, language="de", output_dir=base / (pack + "-de"), pack_id=pack, purpose="software_fixture", opt_in=True)
                self.assertFalse(receipt["training_allowed"])
                self.assertFalse(translated["training_allowed"])
                with self.assertRaisesRegex(boundary.TrainingBoundaryError, "technical_fixture_not_training_data"):
                    boundary.admit_training_run(output)
                sample = json.loads((output / "samples.jsonl").read_text().splitlines()[0])
                with self.assertRaisesRegex(splits.SplitError, "unsupported_ingestion_provenance"):
                    splits.prepare_record(sample, receipt, consent_id="0" * 64)

    def test_sinabis_rights_metadata_is_not_a_canonical_ingestion_or_label_grant(self):
        admitted = boundary.assert_training_source(sinabis.IDENTITY, purpose="commercial_training")
        self.assertTrue(admitted["requires_origin_projection"])
        self.assertTrue(admitted["requires_independent_labels"])
        self.assertFalse(admitted["release_approved"])
        fake = dict(schema="fdec-unlabelled-source-email/v1", content_id="0" * 64, source=sinabis.IDENTITY, annotations=[])
        with self.assertRaises(labels.MappingError):
            labels.map_normalized_record(fake)
        with self.assertRaises(splits.SplitError):
            splits.prepare_record(fake, dict(schema="fdec-sinabis-preparation/v1"), consent_id="0" * 64)


if __name__ == "__main__":
    unittest.main()
