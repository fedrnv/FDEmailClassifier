"""Local disk-backed split fixtures. No training inputs or real consent."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import os
from random import Random
import subprocess
import sys
import unittest
from unittest.mock import patch

import disk_inventory as disk
import split_cli
import split_data as splits
import test_splits


def projected_groups(groups):
    return sorted(tuple(row["record_id"] for row in group) for group in groups)


@unittest.skipUnless(os.name == "posix", "The compact inventory requires private POSIX storage")
class DiskInventoryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_splits.SplitTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()

    def pack(self, name="packed", records=None):
        rows = self.fixture.inventory["records"] if records is None else records
        output = self.fixture.base / name
        disk.pack(iter(rows), output_dir=output, opt_in=True)
        return disk.open_inventory(output)

    def signed(self, inventory, *, revoke=None):
        payload = deepcopy(self.fixture.signed["payload"])
        payload.update(revision=2, previous_snapshot_sha256=splits.digest(self.fixture.signed),
                       inventory_sha256=splits.inventory_digest(inventory))
        for grant in payload["grants"]:
            if grant["record_id"] == revoke:
                grant["status"] = "revoked"
        return splits.envelope(payload, self.fixture.key)

    def verify(self, output, inventory, signed):
        return splits.verify(output, inventory, signed, key=self.fixture.key, policy_root=self.fixture.root,
                             now=self.fixture.now, include_manifest=True)

    def test_exact_group_equivalence_including_cross_source_and_reversed_input(self):
        records = self.fixture.inventory["records"]
        expected = projected_groups(splits.components(records))
        for name, order in (("forward", records), ("reverse", reversed(records))):
            inventory = self.pack(name, order)
            groups, comparisons = disk.packed_components(inventory)
            self.assertEqual(projected_groups(groups), expected)
            self.assertGreater(comparisons, 0)
            self.assertTrue(all("shingles" not in row for row in inventory.rows()))

    def test_exact_threshold_and_length_filter_against_legacy(self):
        prototype = self.fixture.inventory["records"][0]
        draw = Random(27)
        tokens = [splits.digest(["token", i]) for i in range(32)]
        exact_threshold = (tokens[:4], tokens[:5], tokens[1:6], tokens[:6])
        rows = []
        pools = list(exact_threshold) + [draw.sample(tokens, draw.randrange(2, 30)) for _ in range(80)]
        for index, pool in enumerate(pools):
            row = deepcopy(prototype)
            row["source"]["dataset_id"] = f"fixture/unique-{index}"
            row["content_sha256"] = splits.digest(["content", index])
            row["thread_id"] = None
            row["shingles"] = sorted(pool)
            row["record_id"] = splits.digest([row["source"], row["content_sha256"], row["provenance"]["source_rows"]])
            rows.append(row)
        groups, _ = disk.packed_components(self.pack(records=rows))
        expected = splits.components(rows)
        self.assertEqual(projected_groups(groups), projected_groups(expected))
        actual = {row["record_id"]: group for group in groups for row in group}
        self.assertIs(actual[rows[0]["record_id"]], actual[rows[1]["record_id"]])

    def test_build_and_replay_agree_and_stale_authority_fails(self):
        fixture = self.fixture
        legacy = fixture.plan()
        inventory = self.pack()
        signed = self.signed(inventory)
        splits.activate_consent(inventory, signed, key=fixture.key, policy_root=fixture.root, now=fixture.now)
        output = fixture.root / "training/outputs/split-v2"
        receipt = splits.build(inventory, signed, output_dir=output, opt_in=True, **fixture.arguments)
        verified = self.verify(output, inventory, signed)
        self.assertEqual(verified["receipt"], receipt)
        self.assertEqual(legacy["assignments"], verified["manifest"]["assignments"])
        original = (output / "receipt.json").read_bytes()
        with self.assertRaises(splits.SplitError):
            self.verify(output, inventory, fixture.signed)
        with self.assertRaises(splits.SplitError):
            splits.build(inventory, signed, output_dir=output, opt_in=True, **fixture.arguments)
        self.assertEqual((output / "receipt.json").read_bytes(), original)

    def test_withdrawal_quarantines_whole_transitive_group(self):
        fixture = self.fixture
        inventory = self.pack()
        signed = self.signed(inventory, revoke=fixture.records[1]["record_id"])
        splits.activate_consent(inventory, signed, key=fixture.key, policy_root=fixture.root, now=fixture.now)
        manifest = fixture.plan(inventory=inventory, signed=signed)
        self.assertEqual(set(manifest["excluded_record_ids"]), {fixture.records[i]["record_id"] for i in (0, 1, 2)})

    def test_changed_fingerprints_or_row_metadata_fail_closed(self):
        inventory = self.pack()
        fixture = self.fixture
        signed = self.signed(inventory)
        splits.activate_consent(inventory, signed, key=fixture.key, policy_root=fixture.root, now=fixture.now)
        output = fixture.root / "training/outputs/must-not-exist"
        raw = inventory.path / "shingles.bin"
        with raw.open("r+b") as stream:
            byte = stream.read(1)
            stream.seek(0)
            stream.write(bytes([byte[0] ^ 1]))
        with self.assertRaisesRegex(splits.SplitError, "changed_disk_fingerprints|invalid_disk_fingerprint_order"):
            splits.build(inventory, signed, output_dir=output, opt_in=True, **fixture.arguments)
        self.assertFalse(output.exists())
        metadata = inventory.path / "records.jsonl"
        data = metadata.read_bytes()
        metadata.write_bytes(data + b"\n")
        with self.assertRaisesRegex(splits.SplitError, "changed_disk_inventory_records"):
            splits.read_inventory(inventory.path)

    def test_permissions_links_and_order_fail_closed(self):
        inventory = self.pack()
        payload = inventory.path / "shingles.bin"
        payload.chmod(0o644)
        with self.assertRaisesRegex(splits.SplitError, "disk_inventory_path_not_private"):
            splits.read_inventory(inventory.path)
        payload.chmod(0o600)
        moved = self.fixture.base / "external"
        payload.rename(moved)
        payload.symlink_to(moved)
        with self.assertRaises(splits.SplitError):
            splits.read_inventory(inventory.path)

    def test_packing_and_comparison_budgets_fail_without_publishing(self):
        first = self.fixture.inventory["records"][0]
        target = self.fixture.base / "over-budget"
        with patch.object(disk, "MAX_FINGERPRINTS", len(first["shingles"]) - 1):
            with self.assertRaisesRegex(splits.SplitError, "disk_inventory_budget_exceeded"):
                disk.pack([first], output_dir=target, opt_in=True)
        self.assertFalse(target.exists())
        inventory = self.pack()
        with patch.object(disk, "MAX_EXACT_COMPARISONS", 0):
            with self.assertRaisesRegex(splits.SplitError, "near_duplicate_comparison_budget_exceeded"):
                disk.packed_components(inventory)

    def test_cli_packs_text_free_projected_records_without_authority(self):
        source = self.fixture.base / "projected.jsonl"
        source.write_text("".join(splits.canonical_json(row) + "\n" for row in self.fixture.inventory["records"]))
        source.chmod(0o600)
        result = io.StringIO()
        output = self.fixture.base / "cli-inventory"
        with redirect_stdout(result):
            code = split_cli.main(["pack", "--inventory", str(source), "--output-dir", str(output), "--opt-in"])
        self.assertEqual(code, 0)
        inventory = splits.read_inventory(output)
        self.assertEqual(json.loads(result.getvalue())["inventory_sha256"], splits.inventory_digest(inventory))

    def test_consent_signer_binds_compact_bytes_before_output(self):
        inventory = self.pack()
        expected = self.signed(inventory)
        payload = self.fixture.base / "compact-payload.json"
        payload.write_text(splits.canonical_json(expected["payload"]) + "\n")
        signer = splits.ROOT / "training/manifests/sign_consent.py"
        command = [sys.executable, str(signer), "--inventory", str(inventory.path),
                   "--payload", str(payload), "--output"]
        environment = dict(os.environ, FDEC_CONSENT_KEY=self.fixture.key.hex())

        output = self.fixture.base / "compact-signed.json"
        signed = subprocess.run(command + [str(output)], env=environment, capture_output=True)
        self.assertEqual(signed.returncode, 0)
        self.assertEqual(splits.read_json(output), expected)
        original = output.read_bytes()

        fingerprints = inventory.path / "shingles.bin"
        with fingerprints.open("r+b") as stream:
            first = stream.read(1)
            stream.seek(0)
            stream.write(bytes([first[0] ^ 1]))
        rejected = self.fixture.base / "must-not-be-signed.json"
        result = subprocess.run(command + [str(rejected)], env=environment, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"consent_error:", result.stderr)
        self.assertFalse(rejected.exists())
        self.assertEqual(output.read_bytes(), original)

    def test_previous_v1_receipt_replays_after_implementation_upgrade(self):
        fixture = self.fixture
        with patch.object(splits, "implementation_hash", return_value=splits.GEMMA_SPLIT_IMPLEMENTATION_SHA256):
            original = fixture.build()
        receipt = self.verify(fixture.root / "training/outputs/run", fixture.inventory, fixture.signed)
        self.assertEqual(receipt["receipt"], original)
