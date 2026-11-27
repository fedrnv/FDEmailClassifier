"""Numerical fixtures only; no model consumes any technical content or gold."""
from copy import deepcopy
from datetime import timedelta
from fractions import Fraction
import hashlib
import hmac
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "training/calibration"))
import calibrate as calibration
import calibration_cli as cli
import admit_scores as admission
import split_data as splits


class NumericalTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads(cli.FIXTURE.read_text())
        self.artifact = calibration.fit(self.bundle, min_class_support=2, min_tail_support=2)

    def test_validation_thresholds_and_independent_label_scales(self):
        values = self.artifact["policies"]["en"]
        self.assertEqual(len(values), 23)
        self.assertEqual((values["topic:work"]["threshold"], values["topic:work"]["negative_cut"], values["topic:work"]["positive_cut"]), (0, -1, 2))
        self.assertEqual((values["security:phishing"]["threshold"], values["security:phishing"]["negative_cut"], values["security:phishing"]["positive_cut"]), (10, 8, 14))
        self.assertFalse(self.artifact["probabilities_estimated"])
        self.assertEqual(self.artifact["policies"]["de"]["topic:work"]["status"], "unsupported")
        self.assertEqual(values["topic:health"]["status"], "unsupported")
        count = calibration.evaluate(self.artifact, self.bundle)["counts"]["en/topic:work"]
        self.assertEqual(count, dict(eligible=4, decided=2, correct=2, fp=0, fn=0, abstained=2, coverage=.5, correct_fraction_all_eligible=.5))

    def test_shared_rust_boundary_vectors_missing_and_invalid_bands(self):
        vectors = json.loads((cli.FIXTURE.parent / "boundaries-v1.json").read_text())
        policy = dict(status="supported", **{key: vectors[key] for key in ("minimum", "maximum", "negative_cut", "positive_cut")})
        for case in vectors["cases"]:
            self.assertEqual(calibration.decide(policy, case["score"]), case["decision"])
        self.assertEqual(calibration.decide(None, 1), "abstained:unsupported")
        for value in (float("nan"), float("inf"), True):
            self.assertEqual(calibration.decide(policy, value), "abstained:unmeasured")
        for change in (dict(negative_cut=2), dict(minimum=4), dict(positive_cut=None, negative_cut=None)):
            with self.assertRaises(calibration.CalibrationError):
                calibration.decide(dict(policy, **change), 0)

    def test_test_labels_scores_and_languages_cannot_fit_policies(self):
        changed = deepcopy(self.bundle)
        for row in changed["rows"]:
            if row["role"] == "test":
                row.update(score=9999, gold=1-row["gold"], language="fr")
        self.assertEqual(self.artifact, calibration.fit(changed, min_class_support=2, min_tail_support=2))
        shuffled = deepcopy(self.bundle)
        random.Random(17).shuffle(shuffled["rows"])
        self.assertEqual(self.artifact, calibration.fit(shuffled, min_class_support=2, min_tail_support=2))

    def test_histogram_threshold_matches_independent_brute_force_fraction_oracle(self):
        rng = random.Random(104729)
        for _ in range(30):
            changed = deepcopy(self.bundle)
            candidates = [row for row in changed["rows"] if row["language"] == "en" and row["label"] == "topic:work" and row["role"] == "validation"]
            for row in candidates:
                row["score"] = rng.randint(-3, 3)
            def score(threshold):
                tp = sum(row["gold"] == 1 and row["score"] >= threshold for row in candidates)
                fp = sum(row["gold"] == 0 and row["score"] >= threshold for row in candidates)
                fn = sum(row["gold"] == 1 and row["score"] < threshold for row in candidates)
                return Fraction(2*tp, 2*tp+fp+fn), threshold
            expected = max(set(row["score"] for row in candidates), key=score)
            actual = calibration.fit(changed, min_class_support=2, min_tail_support=2)["policies"]["en"]["topic:work"]["threshold"]
            self.assertEqual(actual, expected)

    def test_missing_and_conflicting_scores_are_explicitly_unsupported(self):
        for value in (None, 0):
            changed = deepcopy(self.bundle)
            for row in changed["rows"]:
                if row["role"] == "validation":
                    row["score"] = value
            artifact = calibration.fit(changed, min_class_support=2, min_tail_support=2)
            self.assertTrue(all(policy["status"] == "unsupported" for values in artifact["policies"].values() for policy in values.values()))
        self.assertEqual(calibration.fit(self.bundle)["policies"]["en"]["topic:work"]["status"], "unsupported")
        changed = deepcopy(self.bundle)
        changed["model"]["sha256"] = "c" * 64
        with self.assertRaises(calibration.CalibrationError):
            calibration.evaluate(self.artifact, changed)

    def test_invalid_role_duplicate_nan_and_group_leakage_reject(self):
        for mutation in ("train", "duplicate", "nan", "bool", "unknown-label", "group-leak", "record-leak", "self-confidence"):
            changed = deepcopy(self.bundle)
            if mutation == "train": changed["rows"][0]["role"] = "train"
            elif mutation == "duplicate": changed["rows"].append(deepcopy(changed["rows"][0]))
            elif mutation == "nan": changed["rows"][0]["score"] = float("nan")
            elif mutation == "bool": changed["rows"][0]["score"] = True
            elif mutation == "unknown-label": changed["rows"][0]["label"] = "private-token"
            elif mutation == "self-confidence": changed["score_kind"] = "model-says-confident"
            else:
                target = next(row for row in changed["rows"] if row["role"] == "test")
                target["group_id" if mutation == "group-leak" else "record_id"] = changed["rows"][0]["group_id" if mutation == "group-leak" else "record_id"]
            with self.subTest(mutation=mutation):
                with self.assertRaises(calibration.CalibrationError):
                    calibration.fit(changed)

    def test_frozen_cli_report_and_existing_output_preservation(self):
        with tempfile.TemporaryDirectory(prefix="fdec-calibration-oracle-") as name:
            base = Path(name).resolve()
            if not base.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not base.name.startswith("fdec-calibration-oracle-") or base.is_symlink() or base.is_junction():
                raise AssertionError("unsafe_calibration_fixture")
            output = base / "report"
            command = [sys.executable, str(ROOT / "training/calibration/calibration_cli.py"), "software-check", "--output-dir", str(output)]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertFalse(json.loads(result.stdout)["probabilities_estimated"])
            before = (output / "metrics.json").read_bytes()
            self.assertEqual(json.loads(before), cli.software_report())
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual((output / "metrics.json").read_bytes(), before)
            self.assertNotIn(str(output), rejected.stderr)


class CurrentAuthorityTests(unittest.TestCase):
    def test_actual_source_replay_signed_scores_and_revocation(self):
        self.check_source_replay(compact=False)

    @unittest.skipUnless(os.name == "posix", "Compact inventories require private POSIX storage")
    def test_compact_source_replay_signed_scores_and_revocation(self):
        self.check_source_replay(compact=True)

    def check_source_replay(self, *, compact):
        sys.path.insert(0, str(ROOT / "tests/d002"))
        import test_pipeline
        f = test_pipeline.PipelineTests()
        self.addCleanup(f.doCleanups)
        f.setUp()
        def supersede(previous, *, revoke=None):
            payload = deepcopy(previous["payload"])
            payload.update(inventory_sha256=splits.inventory_digest(inventory),
                           revision=payload["revision"] + 1,
                           previous_snapshot_sha256=splits.digest(previous))
            for grant in payload["grants"]:
                if grant["record_id"] == revoke:
                    grant["status"] = "revoked"
            signed = splits.envelope(payload, f.key)
            splits.activate_consent(inventory, signed, key=f.key, policy_root=f.root, now=f.now)
            return signed

        if compact:
            from disk_inventory import pack

            inventory_path = f.root / "training/data/packed"
            pack(f.inventory["records"], output_dir=inventory_path, opt_in=True, policy_root=f.root)
            inventory = splits.read_inventory(inventory_path)
            signed = supersede(f.signed)
        else:
            inventory_path = f.root / "training/data/inventory.json"
            f.write("training/data/inventory.json", f.inventory)
            inventory, signed = f.inventory, f.signed
        directory = f.root / "training/outputs/split"
        splits.build(inventory, signed, output_dir=directory, key=f.key, seed=19, opt_in=True,
                     policy_root=f.root, now=f.now)
        split = splits.verify(directory, inventory, signed, key=f.key, policy_root=f.root, now=f.now,
                              include_manifest=True)
        manifest = split["manifest"]
        rows = [dict(record_id=row["record_id"], group_id=row["group_id"], role=row["split"], language="en", label="topic:work", score=.5, gold=1) for row in manifest["assignments"] if row["split"] != "train"]
        bundle = dict(schema="fdec-calibration-observations/v1", score_kind=calibration.SCORE_KIND, model=dict(id="counterfactual-numeric-producer", revision="a"*40, sha256="b"*64), rows=rows)
        f.write("training/data/signed.json", signed)
        f.write("training/data/scores.json", bundle)
        payload = dict(schema="fdec-calibration-score-review/v1", inventory_sha256=splits.inventory_digest(inventory), consent_sha256=splits.digest(signed), split_receipt_sha256=splits.digest(split["receipt"]), observations_sha256=hashlib.sha256((f.root / "training/data/scores.json").read_bytes()).hexdigest(), score_kind=calibration.SCORE_KIND, origin="independently-reviewed-non-openai", evidence_sha256=splits.digest("counterfactual review only"), issued_at=test_pipeline.stamp(f.now-timedelta(minutes=1)), valid_until=test_pipeline.stamp(f.now+timedelta(minutes=20)))
        review = dict(schema="fdec-signed-calibration-review/v1", payload=payload, hmac_sha256=hmac.new(f.key, admission.DOMAIN+splits.canonical_json(payload).encode(), hashlib.sha256).hexdigest())
        f.write(admission.ANCHOR, review)
        arguments = dict(inventory_path=inventory_path, consent_path=f.root / "training/data/signed.json", split_dir=directory, observations_path=f.root / "training/data/scores.json", source_runs=f.runs, key=f.key, policy_root=f.root, now=f.now)
        admitted, bindings = admission.admit(**arguments)
        self.assertEqual(admitted, bundle)
        self.assertEqual(bindings["inventory_sha256"], splits.inventory_digest(inventory))
        before = arguments["observations_path"].read_bytes()
        changed = deepcopy(bundle)
        changed["rows"][0]["score"] = 999
        f.write("training/data/scores.json", changed)
        with self.assertRaises(calibration.CalibrationError): admission.admit(**arguments)
        arguments["observations_path"].write_bytes(before)
        supersede(signed, revoke=rows[0]["record_id"])
        with self.assertRaises(calibration.CalibrationError): admission.admit(**arguments)
        for pack in admission.boundary.FIXTURE_PACKS:
            with self.assertRaises(admission.boundary.TrainingBoundaryError):
                admission.boundary.prohibit_codex_training(pack, "codex", "evaluation")


if __name__ == "__main__": unittest.main()
