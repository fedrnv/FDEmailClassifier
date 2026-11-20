"""Technical metadata/token fixtures only; never actual labelled training data."""
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import itertools
import io
import json
from pathlib import Path
import random
import shutil
import string
import tempfile
import unittest
from unittest.mock import patch

import sinabis_source as s
import training_boundary as b


def token(index):
    rng = random.Random(index)
    return "software fixture token " + "".join(rng.choices(string.ascii_letters + string.digits, k=240))


def row(index, *, case=None, size=1, position=1, **changes):
    result = dict(idx=index, file=f"fixture-{index}.eml", case_id=hashlib.sha256(str(case if case is not None else index).encode()).hexdigest(), case_kind="single", case_size=size, position=position,
                  lang="en", subject="Software fixture", text=token(index), message_id=f"fixture-{index}@mail.invalid", in_reply_to="", model="qwen3.6-35b-a3b-awq", model_tag="V1", calendar_method="", duplicate_of="")
    result.update(changes)
    return result


class SinabisTests(unittest.TestCase):
    def isolated_policy(self):
        directory = tempfile.TemporaryDirectory(prefix="fdec-sinabis-policy-")
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for relative in s.EVIDENCE | {s.PROFILE}:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(s.ROOT / relative, path)
        return root

    def save_profile(self, root, profile):
        (root / s.PROFILE).write_text(json.dumps(profile), encoding="utf-8")

    def test_production_source_admission_checks_three_uses_but_not_release(self):
        for purpose in b.PURPOSES:
            admitted = b.assert_training_source(s.IDENTITY, purpose=purpose)
            self.assertEqual(admitted["descriptor"]["license"], "CC-BY-4.0")
            self.assertEqual(admitted["descriptor"]["row_scope"], "reviewed-whole-cases-only")
            self.assertEqual(admitted["downstream_rights"], s.DOWNSTREAM)
            self.assertEqual(admitted["attribution"], s.attribution())
            self.assertFalse(admitted["release_approved"])
            self.assertTrue(admitted["requires_origin_projection"])
            self.assertTrue(admitted["requires_split_and_consent"])
            self.assertTrue(admitted["requires_independent_labels"])

    def test_unapproved_revision_hash_model_and_purposes_fail(self):
        for key, value in (("revision", "0" * 40), ("sha256", "0" * 64), ("artifact", "other.parquet"), ("dataset_id", "sinabis-group/sinabis-10m-synthetic-emails")):
            with self.assertRaises(b.TrainingBoundaryError):
                s.assert_source(dict(s.IDENTITY, **{key: value}), purpose="commercial_training")
        for purpose in ("publish", "commercial_inference", "public_model_distribution", "software_fixture"):
            with self.assertRaises(b.TrainingBoundaryError):
                s.assert_source(s.IDENTITY, purpose=purpose)

    def test_profile_cannot_promote_unknown_or_openai_origin(self):
        root = self.isolated_policy()
        original = b.read_json(root / s.PROFILE)
        for key in ("qwen3.6", "gpt-generated"):
            profile = deepcopy(original)
            profile["origin_policy"][key] = "reviewed_local_qwen"
            self.save_profile(root, profile)
            with self.assertRaisesRegex(s.SinabisError, "profile_changed"):
                s.assert_source(s.IDENTITY, purpose="commercial_training", policy_root=root)

    def test_evidence_attribution_and_separate_distribution_decision_required(self):
        root = self.isolated_policy()
        original = b.read_json(root / s.PROFILE)
        changes = [lambda p: p["evidence"].pop(), lambda p: p["attribution"].pop("warranty_uri"), lambda p: p["downstream_rights"].pop("public_model_distribution"), lambda p: p.update(release_approved=True)]
        for change in changes:
            profile = deepcopy(original)
            change(profile)
            self.save_profile(root, profile)
            with self.assertRaises(s.SinabisError):
                s.assert_source(s.IDENTITY, purpose="commercial_training", policy_root=root)
        self.save_profile(root, original)
        path = root / "training/augmentation/SINABIS-AUDIT-v2.md"
        path.write_bytes(path.read_bytes() + b"tamper")
        with self.assertRaisesRegex(s.SinabisError, "evidence_changed"):
            s.assert_source(s.IDENTITY, purpose="commercial_training", policy_root=root)

    def test_snapshot_checksum_and_opt_in_reject_without_mutation(self):
        with tempfile.TemporaryDirectory(prefix="fdec-sinabis-bytes-") as directory:
            path = Path(directory) / "source.parquet"
            path.write_bytes(b"software fixture only")
            before = path.read_bytes()
            with self.assertRaisesRegex(s.SinabisError, "explicit_opt_in"):
                s.prepare(path)
            with self.assertRaisesRegex(s.SinabisError, "checksum_mismatch"):
                s.prepare(path, opt_in=True)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(sorted(p.name for p in path.parent.iterdir()), ["source.parquet"])

    def test_both_codex_packs_remain_denied_after_new_source_registration(self):
        for pack in b.FIXTURE_PACKS:
            for purpose in b.PURPOSES:
                with self.assertRaisesRegex(b.TrainingBoundaryError, "openai_derived"):
                    b.prohibit_codex_training(pack, "codex-assisted-original", purpose)

    def test_legacy_receipt_cannot_launder_unfiltered_sinabis_rows(self):
        admitted = s.assert_source(s.IDENTITY, purpose="commercial_training")
        with tempfile.TemporaryDirectory(prefix="fdec-sinabis-receipt-") as directory:
            path = Path(directory) / "receipt.json"
            receipt = dict(schema="fdec-ingestion-receipt/v1", normalization_version=b.VERSION, implementation_sha256="0" * 64, python_version="software-fixture", decoder="pyarrow/26.0.1",
                           input=admitted["descriptor"], source_file="source.parquet", records_file="records.jsonl", records_sha256="0" * 64, input_rows=0, unique_rows=0, duplicates=0, annotation_conflicts=0)
            path.write_text(json.dumps(receipt), encoding="utf-8")
            before = path.read_bytes()
            with self.assertRaisesRegex(b.TrainingBoundaryError, "dedicated_preparation"):
                b.admit_training_run(directory)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(sorted(item.name for item in path.parent.iterdir()), ["receipt.json"])

    def test_whole_case_and_linked_duplicate_quarantine(self):
        first = row(1, case=1, size=2, position=1, case_kind="thread")
        second = row(2, case=1, size=2, position=2, case_kind="thread", in_reply_to=first["message_id"], model="qwen3.6", model_tag="QW")
        duplicate = row(3, subject=first["subject"], text=first["text"])
        inputs = [first, second, duplicate, row(4)]
        before = deepcopy(inputs)
        projected = s.project_rows(inputs)
        self.assertEqual(projected["summary"]["quarantined_rows"], 3)
        self.assertEqual(projected["summary"]["quarantined_cases"], 2)
        self.assertEqual(projected["summary"]["unique_records"], 1)
        self.assertEqual(inputs, before)

    def test_incomplete_cases_or_unknown_links_never_silently_pass(self):
        for example in (row(1, size=2), row(1, in_reply_to="missing@mail.invalid"), row(1, duplicate_of="missing.eml")):
            projected = s.project_rows([example])
            self.assertEqual(projected["summary"]["unique_records"], 0)
            self.assertEqual(projected["summary"]["quarantined_rows"], 1)

    def test_rule_based_rows_need_calendar_evidence(self):
        accepted = row(1, model="", model_tag="", case_kind="meeting", calendar_method="REQUEST")
        for example, expected in ((accepted, 1), (dict(accepted, calendar_method=""), 0), (dict(accepted, case_kind="single"), 0)):
            self.assertEqual(s.project_rows([example])["summary"]["unique_records"], expected)

    def test_all_dimensions_missing_no_defaults_or_codex_per_message_labels(self):
        record, = s.project_rows([row(1)])["records"]
        self.assertEqual(record["schema"], "fdec-unverified-source-projection/v1")
        self.assertIsNone(record["source"])
        self.assertEqual(record["labels_origin"], "not_provided_by_source")
        self.assertFalse(record["training_ready"])
        for name in s.DIMENSIONS:
            self.assertEqual(record["dimensions"][name], dict(state="missing", values=[], supervise=False))
        with self.assertRaisesRegex(s.SinabisError, "record_identity"):
            s.project_rows([row(1, labels={"category": "work"})])

    def test_vocabulary_and_29_language_extension_without_coverage_claim(self):
        vocabulary = s.mapping()
        self.assertEqual(len(vocabulary["topics"]), 12)
        self.assertEqual(len(vocabulary["priority"]), 4)
        self.assertEqual(len(vocabulary["action"]), 4)
        self.assertEqual(set(vocabulary["security"]), {"spam", "phishing", "malware"})
        self.assertFalse(vocabulary["automatic_supervision"])
        inputs = [row(index, lang=language) for index, language in enumerate(s.LANGUAGES)]
        self.assertEqual(len(s.project_rows(inputs)["summary"]["languages"]), 29)
        # Pinned production profile still admits only its four observed languages.
        self.assertEqual(s.project_rows([row(1, lang="ja")], allowed_languages=("en", "de", "fr", "it"))["summary"]["quarantined_rows"], 1)

    def test_exact_duplicates_consolidate_all_lineage(self):
        first = row(1)
        second = row(2, subject=first["subject"].upper(), text=first["text"].upper())
        projected = s.project_rows([first, second])
        record, = projected["records"]
        self.assertEqual(projected["summary"]["retained_exact_duplicate_rows"], 1)
        self.assertEqual(record["source_rows"], [0, 1])
        self.assertEqual(len(record["case_ids"]), 2)

    def test_near_duplicate_and_explicit_reply_components_preserved(self):
        first = row(1)
        second = row(2, text=first["text"][:-1] + "X")
        third = row(3, in_reply_to=second["message_id"])
        projected = s.project_rows([first, second, third])
        self.assertEqual(len({r["component_id"] for r in projected["records"]}), 1)
        self.assertGreaterEqual(projected["summary"]["near_duplicate_pairs"], 1)

    def test_prefix_candidate_filter_matches_exhaustive_jaccard(self):
        rng = random.Random(42)
        universe = list(range(30))
        sets = [frozenset(rng.sample(universe, rng.randrange(1, 26))) for _ in range(160)]
        sets += [frozenset(range(20)), frozenset(range(21)), frozenset(range(1, 21))]
        expected = {(left, right) for left, right in itertools.combinations(range(len(sets)), 2) if len(sets[left] & sets[right]) * 5 >= len(sets[left] | sets[right]) * 4}
        self.assertEqual(set(s.near_pairs(sets)), expected)

    def test_pair_size_filter_matches_all_nonempty_subsets(self):
        sets = [frozenset(combination) for size in range(1, 9) for combination in itertools.combinations(range(8), size)]
        expected = {(left, right) for left, right in itertools.combinations(range(len(sets)), 2) if len(sets[left] & sets[right]) * 5 >= len(sets[left] | sets[right]) * 4}
        self.assertEqual(set(s.near_pairs(sets)), expected)

    def test_cli_preserves_unicode_attribution_through_ascii_pipe(self):
        expected = {"attribution": s.attribution(), "training_ready": False}
        output = io.BytesIO()
        stream = io.TextIOWrapper(output, encoding="ascii", write_through=True)
        with patch.object(s, "prepare", return_value=expected), redirect_stdout(stream):
            self.assertEqual(s.main(["--source", "software-fixture-only.parquet", "--opt-in"]), 0)
        encoded = output.getvalue()
        self.assertTrue(encoded.isascii())
        self.assertEqual(json.loads(encoded), expected)
        stream.detach()

    def test_invalid_cli_arguments_do_not_echo_supplied_content(self):
        output, errors = io.StringIO(), io.StringIO()
        private_token = "software-fixture-do-not-echo"
        with patch.object(s, "prepare") as prepare, redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(s.main(["--source", "fixture.parquet", "--unrecognized", private_token]), 1)
        prepare.assert_not_called()
        self.assertNotIn(private_token, output.getvalue() + errors.getvalue())
        self.assertEqual(errors.getvalue(), "invalid_sinabis_arguments\n")

    def test_thread_component_and_family_splits_fail_closed(self):
        for inputs, expected in (([row(1, case=1, size=2, position=1), row(2, case=1, size=2, position=2)], "thread"),
                                 ([row(1), row(2, text=row(1)["text"][:-1] + "X")], "component"), ([row(1), row(2)], "family")):
            projected = s.project_rows(inputs)
            records = projected["records"]
            roles = {record["record_id"]: ("train" if index == 0 else "test") for index, record in enumerate(records)}
            with self.assertRaisesRegex(s.SinabisError, expected + "_leakage"):
                s.check_roles(projected, roles)
            report = s.check_roles(projected, {record["record_id"]: "train" for record in records})
            self.assertFalse(report["training_ready"])
            self.assertTrue(report["requires_current_split_and_consent_gate"])

    def test_forged_family_metadata_does_not_make_split_safe(self):
        projected = s.project_rows([row(1), row(2)])
        projected["records"][0]["source_family"] = "forged-independent-family"
        projected["summary"]["records_sha256"] = s.digest(projected["records"])
        with self.assertRaisesRegex(s.SinabisError, "projection_proof"):
            s.check_roles(projected, {record["record_id"]: "train" for record in projected["records"]})

    def test_inserted_labels_cannot_become_reviewed_projection_targets(self):
        projected = s.project_rows([row(1)])
        projected["records"][0]["dimensions"]["topics"] = dict(state="mapped", values=["work"], supervise=True)
        projected["summary"]["records_sha256"] = s.digest(projected["records"])
        with self.assertRaisesRegex(s.SinabisError, "projection_proof"):
            s.check_roles(projected, {record["record_id"]: "train" for record in projected["records"]})

    def test_projection_repeatability_and_resource_failures_preserve_inputs(self):
        inputs = [row(1), row(2)]
        before = deepcopy(inputs)
        self.assertEqual(s.project_rows(inputs), s.project_rows(inputs))
        for name in ("MAX_ROWS", "MAX_FEATURES", "MAX_TOTAL_FEATURES", "MAX_COMPARISONS"):
            with patch.object(s, name, 0), self.assertRaises(s.SinabisError):
                s.project_rows([row(1), row(2, text=row(1)["text"])])
        self.assertEqual(inputs, before)

    def test_legacy_license_guard_still_rejects_the_cc_by_profile(self):
        with self.assertRaises(Exception):
            b.ingestion.inclusion(s.IDENTITY["dataset_id"], s.IDENTITY["revision"], s.IDENTITY["artifact"], "commercial_training", "specialized-email-classifier", s.ROOT)


if __name__ == "__main__":
    unittest.main()
