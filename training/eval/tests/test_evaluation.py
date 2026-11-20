"""Hand-computed metric oracles and real runner failure boundaries, no model."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "training/eval"))
import classification_metrics as metrics
import metric_oracle as oracle
import evaluate
from baseline_metrics import EvaluationError
import split_data as splits


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(oracle.FIXTURE.read_text())
        self.gold = self.fixture["gold"]
        self.predictions = self.fixture["predictions"]

    def test_frozen_four_row_oracle_all_topics_and_languages(self):
        value = oracle.report()
        self.assertFalse(value["actual_model_executed"])
        self.assertFalse(value["model_quality_claim"])
        self.assertEqual(value["scope"], "software-metric-oracle-only")
        overall = value["metrics"]["overall"]
        topics = overall["topics"]
        self.assertEqual(set(topics["counts"]), set(metrics.TOPICS))
        self.assertTrue(all(row["support"] == 1 for row in topics["counts"].values()))
        self.assertAlmostEqual(topics["micro_f1"], float(Fraction(16, 21)), places=14)
        self.assertAlmostEqual(topics["macro_f1"], float(Fraction(23, 36)), places=14)
        self.assertAlmostEqual(topics["macro_supported_f1"], float(Fraction(23, 36)), places=14)
        self.assertEqual(topics["macro_all_labels_denominator"], 12)
        self.assertEqual(topics["counts"]["finance"]["f1"], 0)
        self.assertAlmostEqual(topics["counts"]["legal"]["f1"], 2/3)
        self.assertEqual(overall["heads"]["topics"]["accuracy"], .5)
        self.assertEqual(overall["heads"]["priority"]["accuracy"], .5)
        self.assertEqual(overall["heads"]["action"]["accuracy"], .5)
        self.assertEqual(overall["invalid_outputs"], 1)
        self.assertEqual(topics["decision_coverage"], .75)
        self.assertAlmostEqual(value["metrics"]["by_language"]["en"]["topics"]["micro_f1"], .8)
        self.assertAlmostEqual(value["metrics"]["by_language"]["de"]["topics"]["micro_f1"], 8/11)
        self.assertEqual(value["metrics"]["by_language"]["en"]["heads"]["action"]["accuracy"], 1)
        self.assertEqual(value["metrics"]["by_language"]["de"]["heads"]["action"]["accuracy"], 0)

    def test_binary_false_positive_denominators_and_unresolved_bounds(self):
        report = metrics.measure(self.gold, self.predictions)
        spam = report["overall"]["heads"]["spam"]
        self.assertEqual((spam["tp"], spam["fp"], spam["tn"], spam["fn_decided"]), (0, 1, 1, 1))
        self.assertEqual(spam["clear_support"], 3)
        self.assertEqual(spam["unresolved_clear"], 1)
        self.assertEqual(spam["false_positive_rate"], .5)
        self.assertEqual(spam["false_positive_rate_denominator"], 2)
        self.assertEqual(spam["unresolved_fpr_bounds"], dict(lower=1/3, upper=2/3, denominator=3))
        self.assertEqual(spam["recall_with_unresolved_as_misses"], 0)
        phishing = report["overall"]["heads"]["phishing"]
        self.assertEqual((phishing["fp"], phishing["tn"], phishing["unresolved_flagged"]), (2, 1, 1))
        self.assertEqual(phishing["false_positive_rate"], 2/3)
        self.assertEqual(report["by_language"]["en"]["heads"]["spam"]["false_positive_rate"], 1)
        german = report["by_language"]["de"]["heads"]["spam"]
        self.assertEqual(german["false_positive_rate"], 0)
        self.assertEqual(german["unresolved_fpr_bounds"], dict(lower=0, upper=.5, denominator=2))

    def test_masks_and_no_support_never_become_false_negatives_or_zero_rates(self):
        report = metrics.measure(self.gold, self.predictions)
        malware = report["overall"]["heads"]["malware"]
        self.assertEqual(malware["eligible"], 0)
        for field in ("accuracy", "decision_coverage", "false_positive_rate", "recall_with_unresolved_as_misses"):
            self.assertIsNone(malware[field])
        self.assertEqual(malware["unresolved_fpr_bounds"], dict(lower=None, upper=None, denominator=0))
        rows = deepcopy(self.gold)
        for row in rows:
            row["mask"]["topics"] = False
        topic = metrics.measure(rows, self.predictions)["overall"]["topics"]
        self.assertIsNone(topic["micro_f1"])
        self.assertIsNone(topic["macro_f1"])
        self.assertIsNone(topic["macro_supported_f1"])
        self.assertEqual(topic["macro_all_labels_denominator"], 0)

    def test_all_unresolved_outputs_cannot_produce_perfect_correctness_or_fpr(self):
        for status in ("invalid", "unknown", "abstained", "unknown-head"):
            prediction = None
            if status != "invalid":
                prediction = deepcopy(self.gold[0]["classification"])
                if status == "unknown-head":
                    prediction["security"] = dict.fromkeys(("spam", "phishing", "malware"), "unknown")
                else:
                    prediction.update(status=status, topics=[], priority="unknown", suggested_action="review")
            result = metrics.measure(self.gold, [deepcopy(prediction) for _ in self.gold])["overall"]
            binary = result["heads"]["phishing"]
            self.assertEqual(binary["decided"], 0)
            self.assertIsNone(binary["false_positive_rate"])
            self.assertEqual(binary["unresolved_fpr_bounds"], dict(lower=0, upper=1, denominator=3))
            if status != "unknown-head":
                self.assertEqual(result["topics"]["micro_f1"], 0)
                self.assertEqual(result["heads"]["action"]["accuracy"], 0)

    def test_unsupported_topics_macro_definition_and_order_invariance(self):
        rows = [self.gold[0]]
        perfect = [deepcopy(rows[0]["classification"])]
        report = metrics.measure(rows, perfect)
        self.assertEqual(report["overall"]["topics"]["macro_supported_f1"], 1)
        self.assertAlmostEqual(report["overall"]["topics"]["macro_f1"], 2/12)
        base = metrics.measure(self.gold, self.predictions)
        self.assertEqual(base, metrics.measure(list(reversed(self.gold)), list(reversed(self.predictions))))
        before = deepcopy((self.gold, self.predictions))
        metrics.measure(self.gold, self.predictions)
        self.assertEqual((self.gold, self.predictions), before)

    def test_invalid_alignment_schema_duplicates_and_uncertain_gold_reject(self):
        examples = [(self.gold, self.predictions[:-1]), ([], []), ([self.gold[0], self.gold[0]], [None, None]), (self.gold, {}), (self.gold, [dict(private="token")] * 4)]
        uncertain = deepcopy(self.gold)
        uncertain[0]["classification"]["priority"] = "unknown"
        examples.append((uncertain, self.predictions))
        for gold, predictions in examples:
            with self.assertRaises(EvaluationError) as error:
                metrics.measure(gold, predictions)
            self.assertNotIn("token", str(error.exception))

    def test_language_buckets_extend_without_claiming_language_accuracy(self):
        # 119 distinct syntactic three-letter tags, not a claim about real
        # ISO identities, translations or Qwen performance in 119 languages.
        rows, predictions = [], []
        for index in range(119):
            row = deepcopy(self.gold[0])
            row["record_id"] = hashlib.sha256(str(index).encode()).hexdigest()
            row["language"] = "a" + chr(97 + index // 26) + chr(97 + index % 26)
            rows.append(row)
            predictions.append(deepcopy(row["classification"]))
        report = metrics.measure(rows, predictions)
        self.assertEqual(len(report["by_language"]), 119)
        self.assertTrue(all(value["heads"]["priority"]["accuracy"] == 1 for value in report["by_language"].values()))

    def test_real_cli_requires_admission_before_model_and_sanitizes_errors(self):
        arguments = SimpleNamespace(opt_in=True, output_dir=ROOT / "training/outputs/nonexistent-evaluation-test", inventory="missing-private-token", consent="missing", split_dir="missing", annotations="missing", source_run=["missing"], model_dir="missing")
        with patch.object(evaluate, "LocalQwen") as model, patch.object(splits, "authority_key", return_value=b"x" * 32):
            with self.assertRaises(Exception):
                evaluate.run(arguments)
            model.assert_not_called()
        self.assertFalse(arguments.output_dir.exists())
        command = [sys.executable, str(ROOT / "training/eval/evaluate.py")]
        invalid = subprocess.run(command + ["--private-token"], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertNotIn("private-token", invalid.stderr)

    def test_frozen_fixture_cli_writes_structured_report_and_preserves_prior_state(self):
        with tempfile.TemporaryDirectory(prefix="fdec-metric-oracle-") as name:
            directory = Path(name).resolve()
            if not directory.is_relative_to(Path(tempfile.gettempdir()).resolve()) or directory.is_symlink() or directory.is_junction() or not directory.name.startswith("fdec-metric-oracle-"):
                raise AssertionError("unsafe_metric_fixture_directory")
            output = directory / "report"
            command = [sys.executable, str(ROOT / "training/eval/metric_oracle.py"), "--output-dir", str(output)]
            success = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertFalse(json.loads(success.stdout)["actual_model_executed"])
            content = (output / "metrics.json").read_bytes()
            receipt = json.loads((output / "receipt.json").read_text())
            self.assertEqual(receipt["report_sha256"], hashlib.sha256(content).hexdigest())
            report = json.loads(content)
            self.assertEqual(report, oracle.report())
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual((output / "metrics.json").read_bytes(), content)
            self.assertNotIn(str(output), rejected.stdout + rejected.stderr)
            self.assertFalse(report["actual_model_executed"])
            self.assertFalse(report["model_quality_claim"])


class AdmissionIntegrationTests(unittest.TestCase):
    def test_current_revocation_stops_between_predictions_and_preserves_output(self):
        # Reuse the real three-source counterfactual policy/split fixture.
        # Only a protocol double sees tokens; no actual model is constructed.
        sys.path.insert(0, str(ROOT / "training/baseline/tests"))
        import test_baseline
        setup = test_baseline.AdmissionTests()
        self.addCleanup(setup.doCleanups)
        setup.setUp()
        f = setup.fixture
        original_admit, original_recheck = evaluate.admit, evaluate.recheck
        arguments = SimpleNamespace(opt_in=True, output_dir=f.base / "evaluation-result", inventory=setup.arguments["inventory_path"], consent=setup.arguments["consent_path"],
                                    split_dir=setup.split_dir, annotations=setup.arguments["annotations_path"], source_run=f.runs, model_dir=f.base / "unused-model")
        def revoked_prediction(messages):
            # An operator activates a new snapshot while a prediction is in
            # flight. The next private-text use must be rejected immediately.
            rid = setup.annotations["rows"][0]["record_id"]
            changed = f.sign(revoke=rid, revision=2, previous=splits.digest(f.signed))
            splits.activate_consent(f.inventory, changed, key=f.key, policy_root=f.root, now=f.now)
            return json.dumps(setup.annotations["rows"][0]["classification"])
        with patch.object(evaluate, "admit", side_effect=lambda **values: original_admit(**values, policy_root=f.root, now=f.now)), \
             patch.object(evaluate, "recheck", side_effect=lambda snapshot, **values: original_recheck(snapshot, **values, policy_root=f.root, now=f.now)), \
             patch.object(splits, "authority_key", return_value=f.key), patch.object(evaluate, "LocalQwen") as model:
            model.return_value.infer.side_effect = revoked_prediction
            with self.assertRaises(EvaluationError):
                evaluate.run(arguments)
            self.assertEqual(model.return_value.infer.call_count, 1)
            self.assertFalse(arguments.output_dir.exists())
            with self.assertRaises(EvaluationError):
                evaluate.run(arguments)
            self.assertEqual(model.call_count, 1)
            self.assertFalse(arguments.output_dir.exists())


if __name__ == "__main__":
    unittest.main()
