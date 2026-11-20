"""Native grammar software checks; no generated row is supplied to training."""

from collections import Counter
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import augment as a
import native_templates as n

sys.path.insert(0, str(a.ROOT / "training/labels"))
from map_annotations import map_annotations


class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = a.load_pack("fdec-native-templates-v1", "software_fixture")
        cls.plan = a.read_json(a.ROOT / "training/config/fdec-native-plan-v1.json")
        cls.records, cls.counts = a.plan_rows(cls.plan, cls.pack)

    def setUp(self):
        parent = a.ROOT / "training/outputs"
        parent.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="native-test-", dir=parent)
        self.base = Path(self.temporary.name).resolve()
        self.addCleanup(self.cleanup_fixture)

    def cleanup_fixture(self):
        if not self.base.is_relative_to(a.ROOT / "training/outputs") or not self.base.name.startswith("native-test-") or self.base.is_symlink() or self.base.is_junction():
            raise AssertionError("unsafe_native_fixture_cleanup")
        self.temporary.cleanup()

    def sample(self, topic="work", language="en", index=0, seed=19):
        return a.render(self.pack, topic=topic, language=language, seed=seed, index=index)

    def arguments(self, name="run"):
        return dict(output_dir=self.base / name, pack_id="fdec-native-templates-v1", purpose="software_fixture", opt_in=True)

    def test_all_topics_languages_priorities_security_actions_and_true_variation(self):
        report = n.quality_report(self.records, self.pack, a)
        self.assertEqual(report["rows"], 3456)
        self.assertEqual(report["unique_messages"], 3456)
        self.assertGreaterEqual(report["structural_variants"], 64)
        self.assertEqual(report["template_families"], 24)
        self.assertFalse(report["training_rights_established"])
        for language in self.pack["catalog"]["languages"]:
            for topic in a.TOPICS:
                selected = [row for row in self.records if row["language"] == language and row["labels"]["category"] == topic]
                self.assertEqual(len(selected), 48)
                self.assertEqual(set(row["labels"]["priority"] for row in selected), set(a.PRIORITIES))
                self.assertEqual(set(row["labels"]["security"] for row in selected), set(a.SECURITY))
                self.assertEqual(set(row["labels"]["action"] for row in selected if row["labels"]["security"] == "normal"), set(a.ACTIONS))
                self.assertTrue(all(row["labels"]["action"] == "review" for row in selected if row["labels"]["security"] == "phishing"))
                self.assertTrue(all(row["labels"]["action"] == "archive" for row in selected if row["labels"]["security"] == "spam"))

    def test_real_native_commercial_admission_is_not_fabricated(self):
        # Negative safety evidence. This is explicitly NOT a positive AC-04 PASS.
        for pack in ("fdec-native-templates-v1", "codex-fixture-v1"):
            for purpose in ("commercial_training", "evaluation"):
                with self.subTest(pack=pack, purpose=purpose), self.assertRaisesRegex(a.AugmentationError, "template_training_rights_not_approved"):
                    a.load_pack(pack, purpose)
        self.assertEqual(self.pack["audit"]["allowed_purposes"], ["software_fixture"])
        self.assertEqual(self.pack["audit"]["authoring_origin"], n.ORIGIN)

    def test_previous_fixture_catalog_audit_and_rights_evidence_are_unchanged(self):
        expected = {"training/config/synthetic-catalog-v1.json": "8c388ca1be9114133edaa591aaf2ab5a3b676a939d93a494a29e60d274ca78de", "training/config/augmentation-rights-v1.json": "b8ecad734d298bce6c586eec96815766059f1bf19da827488fe17dc258094a75", "training/augmentation/RIGHTS.md": "6eebf499de5da4d8fafdc04e7298acc7b3f3fc559ac76a418882aeb434cd5ac1"}
        for path, wanted in expected.items():
            self.assertEqual(a.file_hash(a.ROOT / path), wanted)
        old = a.load_pack("codex-fixture-v1", "software_fixture")
        self.assertEqual(old["catalog"]["schema"], "fdec-original-parallel-templates/v1")

    def test_native_facts_are_new_resources_not_renamed_fixture_sentences(self):
        old = a.load_pack("codex-fixture-v1", "software_fixture")["catalog"]["languages"]
        old_facts = {fact for section in old.values() for facts in section["scenarios"].values() for fact in facts}
        native_facts = {fact for section in self.pack["catalog"]["languages"].values() for facts in section["facts"].values() for fact in facts}
        self.assertEqual(len(native_facts), 144)
        self.assertFalse(old_facts & native_facts)

    def test_artificial_identity_slots_only_use_reserved_fictional_namespaces(self):
        for row in self.records:
            identity = row["synthetic_identity"]
            self.assertRegex(identity["person_label"], r"^FDEC-PERSON-[A-F0-9]{24}$")
            self.assertRegex(identity["email"], r"^person-[a-f0-9]{24}@mail\.invalid$")
            self.assertRegex(identity["account_reference"], r"^FDEC-ACCOUNT-[A-F0-9]{24}$")
            self.assertEqual(identity["namespace"], "fdec.invalid/v1")
            self.assertFalse(row["provenance"]["training_allowed"])
            self.assertEqual(row["provenance"]["authoring_origin"], n.ORIGIN)

    def test_parallel_translation_preserves_labels_identity_and_lineage(self):
        for topic in a.TOPICS:
            original = self.sample(topic)
            for language in ("de", "ru", "es", "zh", "ar"):
                translated = a.translate_capsule(original["provenance"]["capsule"], language, self.pack)
                self.assertEqual(translated["labels"], original["labels"])
                self.assertEqual(translated["synthetic_identity"], original["synthetic_identity"])
                self.assertEqual(translated["provenance"]["origin_id"], original["provenance"]["origin_id"])
                self.assertEqual(translated["provenance"]["family_id"], original["provenance"]["family_id"])
                self.assertEqual(translated["provenance"]["translation_parent_id"], original["content_id"])
                self.assertNotEqual(translated["body"], original["body"])
                self.assertEqual(n.quality_report([translated], self.pack, a)["rows"], 1)

    def test_existing_split_policy_rejects_cross_source_and_family_partitions(self):
        original = self.sample()
        translated = a.translate_capsule(original["provenance"]["capsule"], "ru", self.pack)
        unrelated = self.sample("health", index=7)
        selected = [original, translated, unrelated]
        assignments = {row["content_id"]: "train" for row in selected}
        self.assertEqual(n.validate_partition(selected, assignments, self.pack, a)["cross_split_components"], 0)
        for row in (translated, unrelated):
            bad = dict(assignments, **{row["content_id"]: "test"})
            with self.assertRaisesRegex(a.AugmentationError, "native_train_test_leakage"):
                n.validate_partition(selected, bad, self.pack, a)
        with self.assertRaises(a.AugmentationError):
            n.validate_partition(selected, {}, self.pack, a)

    def test_seed_changes_preserve_scenario_families_not_independent_test_samples(self):
        selected = [self.sample("work", index=index, seed=seed) for seed in range(5) for index in range(10)]
        self.assertEqual(len({row["provenance"]["family_id"] for row in selected}), 2)
        self.assertEqual(len({row["content_id"] for row in selected}), 50)
        self.assertGreater(len({row["provenance"]["origin_id"] for row in selected}), 2)

    def test_regeneration_checks_actual_text_annotations_identity_and_provenance(self):
        for mutate in (lambda row: row["labels"].update(category="other"), lambda row: row.update(body="private sentinel"), lambda row: row["synthetic_identity"].update(email="real@example.invalid"), lambda row: row["provenance"].update(family_id="0" * 64), lambda row: row["provenance"].update(translation_parent_id="0" * 64)):
            row = self.sample()
            mutate(row)
            before = deepcopy(row)
            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(output), self.assertRaises(a.AugmentationError) as error:
                n.quality_report([row], self.pack, a)
            self.assertRegex(str(error.exception), r"^[a-z_]+$")
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(row, before)

    def test_duplicate_messages_are_rejected(self):
        original = self.sample()
        with self.assertRaisesRegex(a.AugmentationError, "duplicate_native_message"):
            n.quality_report([original, deepcopy(original)], self.pack, a)

    def test_unsafe_format_expressions_and_incomplete_languages_reject(self):
        for expression in ("{person.__class__}", "{person[secret]}", "{person!r}", "{person:1000000}", "{unknown}", "{"):
            catalog = deepcopy(self.pack["catalog"])
            catalog["languages"]["en"]["greetings"][0] = expression
            with self.subTest(expression=expression), self.assertRaises(a.AugmentationError):
                a.check_catalog(catalog)
        catalog = deepcopy(self.pack["catalog"])
        del catalog["languages"]["ar"]["facts"]["health"]
        with self.assertRaises(a.AugmentationError):
            a.check_catalog(catalog)
        with self.assertRaises(a.AugmentationError):
            self.sample(language="fr")

    def test_catalog_and_quota_interfaces_have_capacity_for_119_vetted_resources(self):
        # Schema-capacity probe only: these are private-use test IDs, not translations.
        catalog = deepcopy(self.pack["catalog"])
        ids = ["q" + chr(97 + index // 26) + chr(97 + index % 26) for index in range(119)]
        catalog["languages"] = {language: deepcopy(self.pack["catalog"]["languages"]["en"]) for language in ids}
        a.check_catalog(catalog)
        in_memory = {**self.pack, "catalog": catalog}
        quotas = [dict(language=language, topic=topic, target=0, observed=0) for language in ids for topic in a.TOPICS]
        records, counts = a.plan_rows(dict(schema="fdec-augmentation-plan/v1", seed=1, quotas=quotas), in_memory)
        self.assertEqual(records, [])
        self.assertEqual(len(counts), 119 * 12)

    def test_native_output_bytes_quality_and_canonical_annotations_repeat(self):
        plan = dict(schema="fdec-augmentation-plan/v1", seed=19, quotas=[dict(language="en", topic=topic, target=4, observed=0) for topic in a.TOPICS])
        first = a.generate(plan, **self.arguments())
        second = a.generate(plan, **self.arguments("repeat"))
        self.assertEqual(first, second)
        self.assertEqual(first["schema"], "fdec-native-augmentation-receipt/v1")
        self.assertEqual(first["quality"]["rows"], 48)
        self.assertFalse(first["training_allowed"])
        for name in (*first["files"], "receipt.json"):
            self.assertEqual((self.base / "run" / name).read_bytes(), (self.base / "repeat" / name).read_bytes())
        annotations = [json.loads(line) for line in (self.base / "run/annotations.jsonl").read_text().splitlines()]
        for row in annotations:
            mapped = map_annotations(content_id=row["content_id"], source=first["annotation_source"], annotations=row["annotations"])
            self.assertEqual(mapped["classification"]["topics"], [row["annotations"][0]["labels"]["category"]])
        # Accepted annotation shape is never used as a substitute for source rights.
        self.assertFalse(first["quality"]["training_rights_established"])

    def test_zero_deficit_has_explicit_empty_native_receipt(self):
        plan = dict(schema="fdec-augmentation-plan/v1", seed=1, quotas=[dict(language="en", topic="work", target=1, observed=1)])
        receipt = a.generate(plan, **self.arguments())
        self.assertEqual(receipt["rows"], 0)
        self.assertEqual(receipt["quality"]["unique_messages"], 0)

    def test_native_cli_retains_rights_denial_and_logs_no_message_fields(self):
        plan = dict(schema="fdec-augmentation-plan/v1", seed=1, quotas=[dict(language="en", topic="work", target=1, observed=0)])
        path = self.base / "plan.json"
        path.write_text(a.canonical(plan), encoding="utf-8")
        base = [sys.executable, str(a.ROOT / "training/augmentation/generate.py"), "--plan", str(path), "--pack-id", "fdec-native-templates-v1", "--output-dir", str(self.base / "cli"), "--opt-in", "--purpose"]
        denied = subprocess.run(base + ["commercial_training"], capture_output=True, text=True)
        self.assertEqual(denied.returncode, 2)
        self.assertIn("template_training_rights_not_approved", denied.stderr)
        self.assertFalse((self.base / "cli").exists())
        allowed = subprocess.run(base + ["software_fixture"], capture_output=True, text=True)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(json.loads(allowed.stdout)["rows"], 1)
        self.assertNotIn("FDEC-PERSON", allowed.stdout + allowed.stderr)
        self.assertNotIn("mail.invalid", allowed.stdout + allowed.stderr)


if __name__ == "__main__":
    unittest.main()
