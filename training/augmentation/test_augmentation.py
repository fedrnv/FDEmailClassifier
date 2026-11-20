"""Software fixtures only. Never export these examples to model training."""

from collections import Counter
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import augment as a

sys.path.insert(0, str(a.ROOT / "training/labels"))
from map_annotations import map_annotations


def plan(*cells, seed=1):
    return dict(schema="fdec-augmentation-plan/v1", seed=seed, quotas=list(cells) or [cell()])


def cell(language="en", topic="health", target=3, observed=0):
    return dict(language=language, topic=topic, target=target, observed=observed)


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class AugmentationTests(unittest.TestCase):
    def setUp(self):
        parent = a.ROOT / "training/outputs"
        parent.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="augmentation-test-", dir=parent)
        self.base = Path(self.temporary.name).resolve()
        self.addCleanup(self.cleanup_fixture)
        self.pack = a.load_pack("codex-fixture-v1", "software_fixture")
        self.arguments = dict(output_dir=self.base / "run", pack_id="codex-fixture-v1", purpose="software_fixture", opt_in=True)

    def cleanup_fixture(self):
        if not self.base.is_relative_to(a.ROOT / "training/outputs") or not self.base.name.startswith("augmentation-test-") or self.base.is_symlink() or self.base.is_junction():
            raise AssertionError("unsafe_fixture_cleanup")
        self.temporary.cleanup()

    def generate(self, value=None, name="run"):
        arguments = dict(self.arguments, output_dir=self.base / name)
        return a.generate(value or plan(), **arguments)

    def test_six_language_twelve_class_default_deficits_and_private_hashes(self):
        configuration = a.read_json(a.ROOT / "training/config/augmentation-default-v1.json")
        receipt = self.generate(configuration)
        generated = rows(self.base / "run/samples.jsonl")
        actual = Counter((row["language"], row["labels"]["category"]) for row in generated)
        self.assertEqual(receipt["rows"], 288)
        self.assertEqual(len(actual), 72)
        self.assertEqual(actual, {(c["language"], c["topic"]): max(c["target"] - c["observed"], 0) for c in configuration["quotas"]})
        self.assertEqual({row["script"] for row in generated}, {"Latn", "Cyrl", "Hans", "Arab"})
        for name, binding in receipt["files"].items():
            content = (self.base / "run" / name).read_bytes()
            self.assertEqual(a.sha(content), binding["sha256"])
            self.assertEqual(len(content), binding["bytes"])
            self.assertEqual(len(rows(self.base / "run" / name)), binding["rows"])
        self.assertFalse(receipt["training_allowed"])
        self.assertTrue(all(row["provenance"]["training_allowed"] is False for row in generated))
        self.assertTrue(all(row["provenance"]["quality_review"] == "required" for row in generated))
        result = a.private_output(self.base / "next", a.ROOT)
        self.assertEqual(result, self.base / "next")
        ignored = subprocess.run(["git", "-C", str(a.ROOT), "check-ignore", "-q", "--", str(self.base / "run/samples.jsonl")], capture_output=True)
        self.assertEqual(ignored.returncode, 0)

    def test_aggregate_counts_only_fill_measured_deficit_and_zero_is_explicit(self):
        receipt = self.generate(plan(cell(target=7, observed=5), cell("de", "legal", target=2, observed=8)))
        self.assertEqual(receipt["rows"], 2)
        self.assertEqual([item["generated"] for item in receipt["request"]["quotas"]], [0, 2])
        empty = self.generate(plan(cell(target=2, observed=2)), "empty")
        self.assertEqual(empty["rows"], 0)
        self.assertEqual((self.base / "empty/samples.jsonl").read_bytes(), b"")
        self.assertTrue((self.base / "empty/receipt.json").is_file())

    def test_repeatable_bytes_and_receipts_not_dependent_on_output_path(self):
        first = self.generate()
        second = self.generate(name="repeat")
        self.assertEqual(first, second)
        for name in (*first["files"], "receipt.json"):
            self.assertEqual((self.base / "run" / name).read_bytes(), (self.base / "repeat" / name).read_bytes())
        third = self.generate(plan(seed=2), "changed-seed")
        self.assertNotEqual(first["files"]["samples.jsonl"]["sha256"], third["files"]["samples.jsonl"]["sha256"])

    def test_quota_order_independence_of_messages(self):
        cells = [cell("en", "health"), cell("ar", "legal")]
        first = self.generate(plan(*cells))
        second = self.generate(plan(*reversed(cells)), "reordered")
        self.assertEqual(first["files"], second["files"])
        self.assertNotEqual(first["request"]["plan_sha256"], second["request"]["plan_sha256"])

    def test_translation_preserves_labels_roots_and_cross_seed_families(self):
        for topic in a.TOPICS:
            original = a.render(self.pack, topic=topic, language="en", seed=23, index=0)
            for language in ("de", "ru", "es", "zh", "ar"):
                translated = a.translate_capsule(original["provenance"]["capsule"], language, self.pack)
                self.assertEqual(translated["labels"], original["labels"])
                self.assertEqual(translated["provenance"]["origin_id"], original["provenance"]["origin_id"])
                self.assertEqual(translated["provenance"]["family_id"], original["provenance"]["family_id"])
                self.assertEqual(translated["provenance"]["translation_parent_id"], original["content_id"])
                self.assertNotEqual(translated["body"], original["body"])
                if language in ("ru", "zh", "ar"):
                    self.assertTrue(any(ord(char) > 127 for char in translated["body"]))
        families = {a.render(self.pack, topic="health", language="en", seed=seed, index=0)["provenance"]["family_id"] for seed in range(20)}
        self.assertEqual(len(families), 2)  # All cosmetic variants stay in two scenario groups.

    def test_translation_source_slice_validates_all_inputs(self):
        self.generate(plan(cell("en"), cell("de")))
        capsules = a.read_capsules(self.base / "run/capsules.jsonl")
        receipt = a.translate(capsules, language="ar", source_language="en", **dict(self.arguments, output_dir=self.base / "translated"))
        self.assertEqual(receipt["rows"], 3)
        self.assertEqual({row["language"] for row in rows(self.base / "translated/samples.jsonl")}, {"ar"})
        altered = deepcopy(capsules)
        next(row for row in altered if row["language"] == "de")["body"] = "private sentinel"
        with self.assertRaises(a.AugmentationError):
            a.translate(altered, language="ar", source_language="en", **dict(self.arguments, output_dir=self.base / "bad-slice"))
        self.assertFalse((self.base / "bad-slice").exists())

    def test_mapping_bridge_uses_actual_annotation_artifact_hash(self):
        receipt = self.generate()
        for item in rows(self.base / "run/annotations.jsonl"):
            result = map_annotations(content_id=item["content_id"], source=receipt["annotation_source"], annotations=item["annotations"])
            self.assertEqual(result["classification"]["topics"], ["health"])
            self.assertEqual(result["source"]["sha256"], a.sha((self.base / "run/annotations.jsonl").read_bytes()))
        # Valid metadata is not a training license; the receipt still denies it.
        self.assertFalse(receipt["training_allowed"])

    def test_no_opt_in_does_not_load_rights_or_create_output(self):
        with patch.object(a, "load_pack") as guard, self.assertRaisesRegex(a.AugmentationError, "explicit_opt_in_required"):
            a.generate(plan(), **dict(self.arguments, opt_in=False))
        guard.assert_not_called()
        self.assertFalse(self.arguments["output_dir"].exists())

    def test_provider_output_training_and_evaluation_rights_fail_closed(self):
        for purpose in ("commercial_training", "evaluation", "redistribution", "internal_training", "", "software_fixture "):
            with self.subTest(purpose=purpose), patch.object(a, "_publish") as publish, self.assertRaisesRegex(a.AugmentationError, "template_training_rights_not_approved"):
                a.generate(plan(), **dict(self.arguments, purpose=purpose))
            publish.assert_not_called()
        with self.assertRaisesRegex(a.AugmentationError, "unapproved_template_pack"):
            a.generate(plan(), **dict(self.arguments, pack_id="human-owned-without-audit"))
        self.assertFalse(self.arguments["output_dir"].exists())

    def test_invalid_quota_inputs_preserve_original_state(self):
        invalid = [None, {}, dict(plan(), seed=True), dict(plan(), seed=-1), dict(plan(), quotas=[]), dict(plan(), quotas="private"), plan(cell(target=-1)), plan(cell(target=True)), plan(cell(target=1001)), plan(cell(observed=-1)), plan(cell(language="fr")), plan(cell(topic="unknown")), plan(cell(), cell()), dict(plan(), body="private sentinel"), plan(*[cell(topic=topic, target=1000) for topic in a.TOPICS])]
        for value in invalid:
            before = deepcopy(value)
            with self.subTest(kind=type(value).__name__), self.assertRaises(a.AugmentationError):
                a.generate(value, **self.arguments)
            self.assertEqual(value, before)
            self.assertFalse(self.arguments["output_dir"].exists())

    def test_capsule_tampering_and_real_text_never_reaches_output(self):
        record = a.render(self.pack, topic="health", language="en", seed=1, index=0)
        capsule = record["provenance"]["capsule"]
        invalid = ["private sentinel", {}, dict(capsule, body="private sentinel"), dict(capsule, context_sha256="0" * 64), dict(capsule, purpose="commercial_training"), dict(capsule, seed=True), dict(capsule, content_id="0" * 64), dict(capsule, pack_id="other")]
        for value in invalid:
            before = deepcopy(value)
            output = io.StringIO()
            with self.subTest(kind=type(value).__name__), redirect_stdout(output), redirect_stderr(output), patch.object(a, "_publish") as publish, self.assertRaises(a.AugmentationError) as error:
                a.translate([value], language="de", **self.arguments)
            self.assertRegex(str(error.exception), r"^[a-z_]+$")
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(value, before)
            publish.assert_not_called()

    def test_invalid_capsule_files_and_duplicate_keys(self):
        source = self.base / "capsules.jsonl"
        for payload in (b"", b"\n", b"private sentinel", b"x" * 8193, b'{"schema":"one","schema":"two"}\n', b"\xff\n"):
            source.write_bytes(payload)
            with self.subTest(length=len(payload)), self.assertRaises(a.AugmentationError):
                a.read_capsules(source)
        with self.assertRaises(a.AugmentationError):
            a.read_json(self.base / "missing")

    def test_no_network_calls_during_generation_or_translation(self):
        with patch("socket.create_connection", side_effect=AssertionError("network not allowed")), patch("urllib.request.urlopen", side_effect=AssertionError("network not allowed")):
            self.generate()
            capsules = a.read_capsules(self.base / "run/capsules.jsonl")
            a.translate(capsules, language="zh", **dict(self.arguments, output_dir=self.base / "offline"))

    def test_failed_final_receipt_removes_only_owned_new_run(self):
        prior = self.base / "prior"
        prior.mkdir()
        (prior / "marker").write_bytes(b"retained")
        with patch.object(a.os, "replace", side_effect=OSError("private sentinel")), self.assertRaisesRegex(a.AugmentationError, "augmentation_write_failed"):
            self.generate()
        self.assertFalse(self.arguments["output_dir"].exists())
        self.assertEqual((prior / "marker").read_bytes(), b"retained")

    def test_partial_stream_write_rollback_and_input_preservation(self):
        configuration = plan()
        before = deepcopy(configuration)
        original = a._write_file
        def fail_capsule(path, data):
            if path.name == "capsules.jsonl":
                raise OSError("private sentinel")
            return original(path, data)
        with patch.object(a, "_write_file", side_effect=fail_capsule), self.assertRaises(a.AugmentationError):
            self.generate(configuration)
        self.assertEqual(configuration, before)
        self.assertFalse(self.arguments["output_dir"].exists())

    def test_existing_unignored_and_linked_outputs_are_preserved(self):
        existing = self.arguments["output_dir"]
        existing.mkdir()
        (existing / "marker").write_bytes(b"retained")
        with self.assertRaises(a.AugmentationError):
            self.generate()
        self.assertEqual((existing / "marker").read_bytes(), b"retained")
        with self.assertRaises(a.AugmentationError):
            a.generate(plan(), **dict(self.arguments, output_dir=a.ROOT / "training/augmentation/not-private"))
        link = self.base / "link"
        link.symlink_to(existing, target_is_directory=True)
        with self.assertRaises(a.AugmentationError):
            a.generate(plan(), **dict(self.arguments, output_dir=link / "nested"))
        self.assertFalse((existing / "nested").exists())

    def test_pinned_registry_audit_and_catalog_reject_mutation(self):
        registry = a.read_json(a.REGISTRY)
        for mutate in (lambda value: value["packs"][0]["catalog"].update(sha256="0" * 64), lambda value: value["packs"].append(deepcopy(value["packs"][0])), lambda value: value["packs"][0]["audit"].update(path="../outside"), lambda value: value.update(schema="future")):
            changed = deepcopy(registry)
            mutate(changed)
            path = self.base / "registry.json"
            path.write_text(a.canonical(changed), encoding="utf-8")
            with patch.object(a, "REGISTRY", path), self.assertRaises(a.AugmentationError):
                a.load_pack("codex-fixture-v1", "software_fixture")

    def test_catalog_rejects_contacts_external_hosts_and_incomplete_translations(self):
        for phrase in ("contact@example.com", "https://portal.invalid", "a real.example.com location", "call 123456789", "private\nbody", "<script>", "\ud800"):
            with self.subTest(kind=len(phrase)), self.assertRaises(a.AugmentationError):
                a.phrase(phrase)
        bad = deepcopy(self.pack["catalog"])
        del bad["languages"]["ar"]["scenarios"]["health"]
        with self.assertRaises(a.AugmentationError):
            a.check_catalog(bad)

    def test_duplicate_translation_outputs_and_empty_source_slice_reject(self):
        capsule = a.render(self.pack, topic="health", language="en", seed=1, index=0)["provenance"]["capsule"]
        for capsules, source in (([capsule, capsule], None), ([capsule], "de"), ([], None)):
            with self.assertRaises(a.AugmentationError):
                a.translate(capsules, language="de", source_language=source, **self.arguments)
            self.assertFalse(self.arguments["output_dir"].exists())

    def test_cli_reports_only_counts_and_static_errors(self):
        configuration = self.base / "plan.json"
        configuration.write_text(a.canonical(plan()), encoding="utf-8")
        generated = subprocess.run([sys.executable, str(a.ROOT / "training/augmentation/generate.py"), "--plan", str(configuration), "--output-dir", str(self.base / "cli"), "--pack-id", "codex-fixture-v1", "--purpose", "software_fixture", "--opt-in"], capture_output=True, text=True)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        self.assertEqual(set(json.loads(generated.stdout)), {"schema", "rows", "training_allowed", "samples_sha256"})
        translated = subprocess.run([sys.executable, str(a.ROOT / "training/augmentation/translate_synthetic.py"), "--capsules", str(self.base / "cli/capsules.jsonl"), "--source-language", "en", "--language", "ar", "--output-dir", str(self.base / "cli-translated"), "--pack-id", "codex-fixture-v1", "--purpose", "software_fixture", "--opt-in"], capture_output=True, text=True)
        self.assertEqual(translated.returncode, 0, translated.stderr)
        for filename in ("generate.py", "translate_synthetic.py"):
            result = subprocess.run([sys.executable, str(a.ROOT / "training/augmentation" / filename), "private sentinel"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("sentinel", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
