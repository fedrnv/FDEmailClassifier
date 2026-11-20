"""Local software fixtures only; no real messages, consent or training corpus."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import split_data as s
from normalize_email import deduplicate, canonical_json

REAL_INCLUSION = s.inclusion


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stamp(value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


class SplitTests(unittest.TestCase):
    def setUp(self):
        parent = s.ROOT / "training/outputs"
        parent.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="splits-test-", dir=parent)
        self.base = Path(self.temporary.name).resolve()
        self.addCleanup(self.cleanup_fixture)
        self.root = self.base / "policy"
        self.root.mkdir()
        initialized = subprocess.run(["git", "-C", str(self.root), "init", "--quiet"], capture_output=True)
        self.assertEqual(initialized.returncode, 0)
        (self.root / ".gitignore").write_text("/training/data/\n/training/outputs/\n", encoding="utf-8")
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.key = secrets.token_bytes(32)
        self.descriptors = {}
        records = []
        near = "".join(sha(str(i).encode()) for i in range(3))
        bodies = [sha(b"different-zero") * 3, near, near[:80] + "z" + near[81:]] + [sha(str(i).encode()) * 3 for i in range(3, 9)]
        bodies[8] = bodies[7]
        sources = {}
        for index, body in enumerate(bodies):
            source_index = 5 if index == 6 else index
            sources.setdefault(source_index, []).append((index, {"subject": "token", "body": body, "category": "work"}))
        observations, decisions, selections = [], [], []
        for index, items in sources.items():
            payload = ("\n".join(canonical_json(item) for _, item in items) + "\n").encode()
            source_id = f"fixture/source-{index}"
            revision = "a" * 40
            artifact = {"path": "rows.jsonl", "git_blob_sha1": hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest(), "sha256": sha(payload), "size": len(payload)}
            source = dict(dataset_id=source_id, revision=revision, artifact="rows.jsonl", sha256=artifact["sha256"])
            observed = dict(id=source_id, revision=revision, declared_license="MIT", provenance="uploader-declared-synthetic", artifacts=[artifact])
            observations.append(observed)
            decisions.append({**{key: observed[key] for key in ("id", "revision", "declared_license", "artifacts")}, "status": "allowed", "scope": "specialized-email-classifier", "allowed_purposes": ["commercial_training", "evaluation"], "reason": "Isolated owned software fixture only; no real-source approval"})
            selections.append(dict(id=source_id, revision=revision))
            descriptor = dict(schema="fdec-dataset-inclusion/v1", dataset_id=source_id, revision=revision, artifact="rows.jsonl", sha256=artifact["sha256"], size=len(payload), url=f"https://huggingface.co/datasets/{source_id}/resolve/{revision}/rows.jsonl", license="MIT", purpose="commercial_training", target="specialized-email-classifier", attribution=f"https://huggingface.co/datasets/{source_id}/tree/{revision}", audit_sha256="b" * 64)
            self.descriptors[source_id] = descriptor
            normalized, count = deduplicate([item for _, item in items], source)
            receipt = dict(schema="fdec-ingestion-receipt/v1", normalization_version=s.NORMALIZATION_VERSION, input=descriptor, records_sha256=sha(("\n".join(canonical_json(row) for row in normalized) + "\n").encode()), input_rows=count)
            for row in normalized:
                original_index = next(number for number, item in items if item["body"] == row["body"])
                thread = s.digest("thread") if original_index in (0, 1) else None
                families = [s.digest("parallel-family")] if original_index in (3, 4) else []
                prepared = s.prepare_record(row, receipt, consent_id=s.digest(["consent", original_index]), thread_id=thread, family_ids=families)
                records.append((original_index, prepared))
        self.records = dict(records)
        self.inventory = dict(schema="fdec-split-inventory/v1", normalization_version=s.NORMALIZATION_VERSION, feature_policy=deepcopy(s.FEATURE_POLICY), records=[row for _, row in sorted(records)])
        self.write_json("docs/legal/datasets/observations.json", dict(schema="fdec-dataset-observations/v1", datasets=observations))
        report = self.root / "docs/legal/datasets/report.md"
        report.write_text("Isolated synthetic software fixture policy only.\n", encoding="utf-8")
        self.audit = dict(schema="fdec-dataset-audit/v1", reviewed_at=stamp(self.now), reviewer="software-fixture", observations=self.binding("docs/legal/datasets/observations.json"), report=self.binding("docs/legal/datasets/report.md"), decisions=decisions)
        self.selections = selections
        self.refresh_audit()
        self.signed = self.sign()
        s.activate_consent(self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now)
        self.guard = patch.object(s, "inclusion", side_effect=self.fixture_inclusion)
        self.guard.start()
        self.addCleanup(self.guard.stop)
        self.arguments = dict(key=self.key, seed=27, ratios=dict(train=60, validation=20, test=20), policy_root=self.root, now=self.now)

    def cleanup_fixture(self):
        if not self.base.is_relative_to(s.ROOT / "training/outputs") or not self.base.name.startswith("splits-test-") or self.base.is_symlink() or self.base.is_junction():
            raise AssertionError("unsafe_fixture_cleanup")
        self.temporary.cleanup()

    def write_json(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(value) + "\n", encoding="utf-8")

    def binding(self, relative):
        return dict(path=relative, sha256=sha((self.root / relative).read_bytes().replace(b"\r\n", b"\n")))

    def refresh_audit(self):
        self.write_json("docs/legal/datasets/audit.json", self.audit)
        self.write_json("training/datasets/allowlist.json", dict(schema="fdec-dataset-allowlist/v1", audit=self.binding("docs/legal/datasets/audit.json"), datasets=self.selections))

    def fixture_inclusion(self, dataset_id, revision, artifact, purpose, target, policy_root):
        self.assertEqual(Path(policy_root), self.root)
        self.assertEqual(purpose in ("commercial_training", "evaluation"), True)
        self.assertEqual(target, "specialized-email-classifier")
        result = deepcopy(self.descriptors[dataset_id])
        self.assertEqual((revision, artifact), (result["revision"], result["artifact"]))
        result["purpose"] = purpose
        return result

    def sign(self, inventory=None, *, changes=None, revision=1, previous=None):
        inventory = self.inventory if inventory is None else inventory
        grants = [dict(record_id=row["record_id"], consent_id=row["consent_id"], evidence_sha256=s.digest(["permission-fixture", row["record_id"]]), status="granted", purposes=["commercial_training", "evaluation"], expires_at=stamp(self.now + timedelta(days=1))) for row in inventory["records"]]
        payload = dict(schema="fdec-consent-ledger/v1", revision=revision, previous_snapshot_sha256=previous, inventory_sha256=s.digest(inventory), issued_at=stamp(self.now - timedelta(hours=1)), valid_until=stamp(self.now + timedelta(days=2)), grants=grants)
        if changes:
            changes(payload)
        return s.envelope(payload, self.key)

    def plan(self, inventory=None, signed=None, **changes):
        return s.plan_manifest(self.inventory if inventory is None else inventory, self.signed if signed is None else signed, **dict(self.arguments, **changes))

    def build(self, name="run", signed=None, **changes):
        return s.build(self.inventory, self.signed if signed is None else signed, output_dir=self.root / "training/outputs" / name, opt_in=True, **dict(self.arguments, **changes))

    def test_transitive_components_keep_source_thread_near_duplicate_family_and_exact_together(self):
        result = self.plan()
        actual = {row["record_id"]: row for row in result["assignments"]}
        for indexes in ((0, 1, 2), (3, 4), (5, 6), (7, 8)):
            self.assertEqual(len({actual[self.records[i]["record_id"]]["split"] for i in indexes}), 1)
            self.assertEqual(len({actual[self.records[i]["record_id"]]["group_id"] for i in indexes}), 1)
        self.assertEqual(set(result["counts"]), set(s.ROLES))
        self.assertTrue(all(result["counts"][role] > 0 for role in s.ROLES))
        self.assertEqual(sum(result["counts"].values()), 9)
        self.assertEqual(sum(result["ratio_error_hundredths"].values()), 0)

    def test_repeated_builds_are_byte_identical_and_do_not_alias_inputs(self):
        before = deepcopy((self.inventory, self.signed))
        first, second = self.build(), self.build("repeat")
        self.assertEqual(first, second)
        for name in ("manifest.json", "receipt.json"):
            self.assertEqual((self.root / "training/outputs/run" / name).read_bytes(), (self.root / "training/outputs/repeat" / name).read_bytes())
        self.assertEqual((self.inventory, self.signed), before)

    def test_real_rights_guard_integration_checks_both_purposes(self):
        with patch.object(s, "inclusion", wraps=REAL_INCLUSION) as actual:
            result = self.plan()
        self.assertEqual(actual.call_count, len(self.descriptors) * 2)
        self.assertEqual({grant["purpose"] for grant in result["source_grants"]}, {"commercial_training", "evaluation"})

    def test_current_source_rights_change_rejects_accepted_consent(self):
        self.build()
        path = self.root / "training/outputs/run/manifest.json"
        original = path.read_bytes()
        self.audit["decisions"][0].update(status="blocked", scope="", allowed_purposes=[])
        self.refresh_audit()
        with patch.object(s, "inclusion", wraps=REAL_INCLUSION), self.assertRaises(s.SplitError):
            s.verify(path.parent, self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now)
        self.assertEqual(path.read_bytes(), original)

    def test_immutable_manifest_verify_returns_validated_snapshot(self):
        receipt = self.build()
        result = s.verify(self.root / "training/outputs/run", self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now, include_manifest=True)
        self.assertEqual(result["receipt"], receipt)
        self.assertEqual(result["manifest"], self.plan())
        with self.assertRaises(s.SplitError):
            self.build()

    def test_contamination_rejected_even_with_recomputed_file_checksum(self):
        self.build()
        root = self.root / "training/outputs/run"
        manifest = s.read_json(root / "manifest.json")
        selected = next(row for row in manifest["assignments"] if row["record_id"] == self.records[0]["record_id"])
        selected["split"] = next(role for role in s.ROLES if role != selected["split"])
        data = (canonical_json(manifest) + "\n").encode()
        (root / "manifest.json").write_bytes(data)
        receipt = s.read_json(root / "receipt.json")
        receipt["manifest_sha256"] = sha(data)
        (root / "receipt.json").write_text(canonical_json(receipt), encoding="utf-8")
        with self.assertRaisesRegex(s.SplitError, "split_provenance_or_contamination_changed"):
            s.verify(root, self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now)

    def test_revocation_quarantines_linked_component_and_blocks_archive_replay(self):
        self.build()
        original = (self.root / "training/outputs/run/manifest.json").read_bytes()
        target = self.records[0]["record_id"]
        changed = self.sign(changes=lambda payload: next(grant for grant in payload["grants"] if grant["record_id"] == target).update(status="revoked"), revision=2, previous=s.digest(self.signed))
        s.activate_consent(self.inventory, changed, key=self.key, policy_root=self.root, now=self.now)
        with self.assertRaisesRegex(s.SplitError, "consent_snapshot_no_longer_current"):
            self.plan()
        with self.assertRaises(s.SplitError):
            s.verify(self.root / "training/outputs/run", self.inventory, changed, key=self.key, policy_root=self.root, now=self.now)
        result = self.plan(signed=changed)
        self.assertEqual(set(result["excluded_record_ids"]), {self.records[index]["record_id"] for index in (0, 1, 2)})
        self.assertEqual(sum(result["counts"].values()), 6)
        self.assertEqual((self.root / "training/outputs/run/manifest.json").read_bytes(), original)

    def test_missing_grant_or_wrong_purpose_quarantines_source_peers(self):
        target = self.records[5]["record_id"]
        for index, mutate in enumerate((lambda p: p.update(grants=[g for g in p["grants"] if g["record_id"] != target]), lambda p: next(g for g in p["grants"] if g["record_id"] == target).update(purposes=["evaluation"]))):
            previous = self.signed if index == 0 else changed
            changed = self.sign(changes=mutate, revision=index + 2, previous=s.digest(previous))
            s.activate_consent(self.inventory, changed, key=self.key, policy_root=self.root, now=self.now)
            result = self.plan(signed=changed)
            self.assertEqual(set(result["excluded_record_ids"]), {self.records[i]["record_id"] for i in (5, 6)})

    def test_per_record_expiry_and_ledger_expiry(self):
        target = self.records[3]["record_id"]
        changed = self.sign(changes=lambda payload: next(g for g in payload["grants"] if g["record_id"] == target).update(expires_at=stamp(self.now + timedelta(minutes=10))), revision=2, previous=s.digest(self.signed))
        s.activate_consent(self.inventory, changed, key=self.key, policy_root=self.root, now=self.now)
        result = self.plan(signed=changed, now=self.now + timedelta(minutes=20))
        self.assertEqual(set(result["excluded_record_ids"]), {self.records[i]["record_id"] for i in (3, 4)})
        with self.assertRaisesRegex(s.SplitError, "consent_ledger_not_current"):
            self.plan(signed=changed, now=self.now + timedelta(days=3))

    def test_wrong_key_tampering_and_duplicate_consent_are_rejected(self):
        for signed, key in ((self.signed, secrets.token_bytes(32)), (dict(self.signed, hmac_sha256="0" * 64), self.key), (self.sign(changes=lambda payload: payload["grants"].append(deepcopy(payload["grants"][0]))), self.key)):
            with self.assertRaises(s.SplitError):
                self.plan(signed=signed, key=key)
        changed = deepcopy(self.signed)
        changed["payload"]["grants"][0]["status"] = "revoked"
        with self.assertRaisesRegex(s.SplitError, "untrusted_consent_signature"):
            self.plan(signed=changed)

    def test_consent_activation_is_monotonic_and_prior_history_is_immutable(self):
        archive = next((self.root / "training/data/consent").glob("revision-1-*.json"))
        original = archive.read_bytes()
        for revision, previous in ((1, None), (3, s.digest(self.signed)), (2, "0" * 64)):
            changed = self.sign(revision=revision, previous=previous, changes=lambda p: p["grants"][0].update(status="revoked"))
            with self.assertRaises(s.SplitError):
                s.activate_consent(self.inventory, changed, key=self.key, policy_root=self.root, now=self.now)
        self.assertEqual(archive.read_bytes(), original)
        self.assertFalse((archive.parent / ".activate.lock").exists())
        self.assertEqual(s.activate_consent(self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now), s.digest(self.signed))

    def test_failed_authority_activation_preserves_anchor_and_allows_exact_retry(self):
        anchor = self.root / "training/data/consent/current.json"
        previous = anchor.read_bytes()
        changed = self.sign(revision=2, previous=s.digest(self.signed))
        with patch.object(s.os, "replace", side_effect=OSError("private sentinel")), self.assertRaises(s.SplitError):
            s.activate_consent(self.inventory, changed, key=self.key, policy_root=self.root, now=self.now)
        self.assertEqual(anchor.read_bytes(), previous)
        s.activate_consent(self.inventory, changed, key=self.key, policy_root=self.root, now=self.now)
        self.assertEqual(s.read_json(anchor), changed)

    def test_withdrawal_during_build_prevents_completion_receipt(self):
        changed = self.sign(revision=2, previous=s.digest(self.signed), changes=lambda p: p["grants"][0].update(status="revoked"))
        write = s._write
        def revoke_on_manifest(path, data):
            write(path, data)
            if path.name == "manifest.json":
                s.activate_consent(self.inventory, changed, key=self.key, policy_root=self.root, now=self.now)
        with patch.object(s, "_write", side_effect=revoke_on_manifest), self.assertRaises(s.SplitError):
            self.build()
        self.assertFalse((self.root / "training/outputs/run").exists())

    def test_no_opt_in_has_no_authority_or_source_effect(self):
        with patch.object(s, "plan_manifest") as admission, self.assertRaisesRegex(s.SplitError, "explicit_opt_in_required"):
            s.build(self.inventory, self.signed, output_dir=self.base / "none", key=self.key)
        admission.assert_not_called()

    def test_malformed_inventory_and_signed_provenance_mismatch_fail_statically(self):
        mutations = (lambda v: v.update(schema="future"), lambda v: v["records"].append(deepcopy(v["records"][0])), lambda v: v["records"][0].update(body="private sentinel"), lambda v: v["records"][0].update(thread_id="real@example.invalid"), lambda v: v["records"][0].update(shingles=[]), lambda v: v["records"][0]["provenance"].update(source_rows=[True]), lambda v: v["records"][0]["source"].update(sha256="0" * 64))
        for mutate in mutations:
            value = deepcopy(self.inventory)
            mutate(value)
            before = deepcopy(value)
            stream = io.StringIO()
            with redirect_stdout(stream), redirect_stderr(stream), self.assertRaises(s.SplitError) as error:
                self.plan(inventory=value)
            self.assertRegex(str(error.exception), r"^[a-z_]+$")
            self.assertEqual(value, before)
            self.assertEqual(stream.getvalue(), "")

    def test_impossible_splits_and_invalid_ratios_do_not_split_a_component(self):
        for ratios in (dict(train=100, validation=0, test=0), dict(train=80, validation=10, test=11), dict(train=True, validation=1, test=98)):
            with self.assertRaises(s.SplitError):
                self.plan(ratios=ratios)
        all_linked = deepcopy(self.inventory)
        for row in all_linked["records"]:
            row["family_ids"] = [s.digest("one-family")]
        signed = self.sign(all_linked, revision=2, previous=s.digest(self.signed))
        s.activate_consent(all_linked, signed, key=self.key, policy_root=self.root, now=self.now)
        with self.assertRaisesRegex(s.SplitError, "insufficient_independent_groups"):
            self.plan(inventory=all_linked, signed=signed)

    def test_near_duplicate_budget_failure_is_explicit(self):
        with patch.object(s, "MAX_COMPARISONS", 0), self.assertRaisesRegex(s.SplitError, "near_duplicate_comparison_budget_exceeded"):
            self.plan()

    def test_multiscript_fingerprints_normalize_case_width_and_punctuation(self):
        self.assertEqual(s.features("", "ＡＢＣＤＥ!"), s.features("", "abcde"))
        self.assertEqual(s.features("", "ПРИВЕТ, МИР"), s.features("", "привет мир"))
        self.assertTrue(s.features("", "中文测试文本"))
        self.assertTrue(s.features("", "اختبار نصي"))
        with self.assertRaises(s.SplitError):
            s.features("", "!!!")
        with self.assertRaises(s.SplitError):
            s.features("", "\ud800")

    def test_missing_and_corrupt_receipts_do_not_validate(self):
        self.build()
        root = self.root / "training/outputs/run"
        receipt = (root / "receipt.json").read_bytes()
        for value in (b"", b"not json", b'{"schema":"one","schema":"two"}'):
            (root / "receipt.json").write_bytes(value)
            with self.assertRaises(s.SplitError):
                s.verify(root, self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now)
        (root / "receipt.json").write_bytes(receipt)
        (root / "manifest.json").write_bytes(b"{}")
        with self.assertRaises(s.SplitError):
            s.verify(root, self.inventory, self.signed, key=self.key, policy_root=self.root, now=self.now)

    def test_failed_write_and_existing_or_linked_outputs_preserve_previous_runs(self):
        self.build()
        root = self.root / "training/outputs/run"
        before = (root / "manifest.json").read_bytes()
        with self.assertRaises(s.SplitError):
            self.build()
        with patch.object(s.os, "replace", side_effect=OSError("private sentinel")), self.assertRaises(s.SplitError):
            self.build("failed")
        self.assertFalse((root.parent / "failed").exists())
        link = root.parent / "linked"
        link.symlink_to(root, target_is_directory=True)
        with self.assertRaises(s.SplitError):
            self.build("linked/new")
        self.assertEqual((root / "manifest.json").read_bytes(), before)

    def test_cli_does_not_echo_arguments_or_secrets_and_signer_does_not_infer_grants(self):
        for script in (s.ROOT / "training/splits/split_cli.py", s.ROOT / "training/manifests/sign_consent.py"):
            result = subprocess.run([sys.executable, str(script), "private sentinel"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("sentinel", result.stdout + result.stderr)
        inventory_path = self.base / "inventory.json"
        payload_path = self.base / "payload.json"
        inventory_path.write_text(canonical_json(self.inventory), encoding="utf-8")
        payload_path.write_text(canonical_json(self.signed["payload"]), encoding="utf-8")
        env = {**os.environ, "FDEC_CONSENT_KEY": self.key.hex()}
        output = self.base / "signed.json"
        result = subprocess.run([sys.executable, str(s.ROOT / "training/manifests/sign_consent.py"), "--inventory", str(inventory_path), "--payload", str(payload_path), "--output", str(output)], capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(s.read_json(output), self.signed)
        self.assertNotIn(self.key.hex(), result.stdout + result.stderr)
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(s.SplitError, "consent_authority_key_missing"):
            s.authority_key()


if __name__ == "__main__":
    unittest.main()
