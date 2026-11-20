"""Create all mail/data fixtures at runtime; never store corpus rows in Git."""

from contextlib import redirect_stderr, redirect_stdout
from email.message import EmailMessage
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

import pyarrow as pa
import pyarrow.parquet as pq

import ingest_dataset as ingestion
from normalize_email import IngestionError, canonical_json, deduplicate, mime_text, normalize_row


def digest(data):
    return hashlib.sha256(data).hexdigest()


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fdec-ingestion-")
        self.base = Path(self.temporary.name)
        self.addCleanup(self.cleanup_fixture)
        self.root = self.base / "policy"
        self.root.mkdir()
        result = subprocess.run(["git", "-C", str(self.root), "init", "--quiet"], capture_output=True)
        self.assertEqual(result.returncode, 0)
        (self.root / ".gitignore").write_text("/training/data/\n/training/outputs/\n", encoding="utf-8")
        self.arguments = dict(dataset_id="fixture/synthetic", revision="a" * 40, artifact="rows.jsonl", purpose="commercial_training", target="specialized-email-classifier", output_dir=self.root / "training/data/run", opt_in=True, policy_root=self.root)

    def cleanup_fixture(self):
        resolved = self.base.resolve()
        if not resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not resolved.name.startswith("fdec-ingestion-") or self.base.is_symlink() or self.base.is_junction():
            raise AssertionError("Unsafe fixture cleanup")
        self.temporary.cleanup()

    def write_json(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(value) + "\n", encoding="utf-8")

    def binding(self, relative):
        return {"path": relative, "sha256": digest((self.root / relative).read_bytes().replace(b"\r\n", b"\n"))}

    def admit(self, payload, suffix=".jsonl"):
        """A clearly synthetic isolated policy; production CLI cannot select it."""
        artifact = "rows" + suffix
        item = {"path": artifact, "git_blob_sha1": hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest(), "sha256": digest(payload), "size": len(payload)}
        source = {"id": "fixture/synthetic", "revision": "a" * 40, "declared_license": "MIT", "provenance": "uploader-declared-synthetic", "artifacts": [item]}
        self.write_json("docs/legal/datasets/observations.json", {"schema": "fdec-dataset-observations/v1", "datasets": [source]})
        (self.root / "docs/legal/datasets/report.md").write_text("Synthetic test policy only. No real source approval.\n", encoding="utf-8")
        decision = {**{key: source[key] for key in ("id", "revision", "declared_license", "artifacts")}, "status": "allowed", "scope": "specialized-email-classifier", "allowed_purposes": ["commercial_training", "evaluation"], "reason": "Owned synthetic acceptance fixture only"}
        self.write_json("docs/legal/datasets/audit.json", {"schema": "fdec-dataset-audit/v1", "reviewed_at": "2026-11-20T00:00:00Z", "reviewer": "fixture", "observations": self.binding("docs/legal/datasets/observations.json"), "report": self.binding("docs/legal/datasets/report.md"), "decisions": [decision]})
        self.write_json("training/datasets/allowlist.json", {"schema": "fdec-dataset-allowlist/v1", "audit": self.binding("docs/legal/datasets/audit.json"), "datasets": [{"id": source["id"], "revision": source["revision"]}]})
        self.input = self.base / ("input" + suffix)
        self.input.write_bytes(payload)
        self.arguments.update(artifact=artifact, input_path=self.input)
        return self.input

    @staticmethod
    def sample(index=1):
        return {"subject": "topic " + str(index), "body": "alpha " + "beta", "category": "business", "priority": "low", "action": "archive", "source_round": "r1"}

    def run_json(self, values):
        self.admit(("\n".join(canonical_json(value) for value in values) + "\n").encode())
        return ingestion.ingest(**self.arguments)

    def test_jsonl_dedup_preserves_annotations_and_is_reproducible(self):
        first = self.sample()
        second = {**first, "body": " alpha\r\n beta ", "source_round": "r2"}
        third = {**first, "priority": "high"}
        receipt = self.run_json([first, second, third, self.sample(2)])
        self.assertEqual((receipt["input_rows"], receipt["unique_rows"], receipt["duplicates"], receipt["annotation_conflicts"]), (4, 2, 2, 1))
        output = Path(self.arguments["output_dir"])
        records = [json.loads(line) for line in (output / "records.jsonl").read_text(encoding="utf-8").splitlines()]
        record = next(value for value in records if value["subject"] == "topic 1")
        self.assertEqual([value["source_row"] for value in record["annotations"]], [0, 1, 2])
        self.assertEqual(record["annotations"][1]["source_round"], "r2")
        self.assertNotIn("source_round", record["annotations"][1]["labels"])
        self.assertEqual(digest((output / "records.jsonl").read_bytes()), receipt["records_sha256"])
        self.assertEqual(digest((output / "source.jsonl").read_bytes()), receipt["input"]["sha256"])
        self.arguments["output_dir"] = output.with_name("repeat")
        repeated = ingestion.ingest(**self.arguments)
        self.assertEqual(repeated, receipt)
        self.assertEqual((output / "records.jsonl").read_bytes(), (output.with_name("repeat") / "records.jsonl").read_bytes())

    def test_parquet_actual_pinned_reader(self):
        buffer = pa.BufferOutputStream()
        pq.write_table(pa.Table.from_pylist([self.sample(), self.sample()]), buffer)
        self.admit(buffer.getvalue().to_pybytes(), ".parquet")
        receipt = ingestion.ingest(**self.arguments)
        self.assertEqual((receipt["input_rows"], receipt["unique_rows"]), (2, 1))

    def test_json_array_loader(self):
        self.admit(canonical_json([self.sample()]).encode(), ".json")
        self.assertEqual(ingestion.ingest(**self.arguments)["unique_rows"], 1)

    def test_mime_alternative_charset_attachment_and_eml_loader(self):
        message = EmailMessage()
        message["Subject"] = "caf" + "é"
        message.set_content("alpha " + "beta", charset="utf-8")
        message.add_alternative("<p>unused " + "alternative</p>", subtype="html")
        message.add_attachment(b"ignored-" + b"attachment", maintype="application", subtype="octet-stream", filename="ignored.bin")
        raw = message.as_bytes()
        self.assertEqual(normalize_row({"raw": raw})[1:3], ("café", "alpha beta"))
        self.admit(raw, ".eml")
        self.assertEqual(ingestion.ingest(**self.arguments)["unique_rows"], 1)

    def test_html_is_visible_text_only_without_network(self):
        row = {"subject": "topic", "body": "<p>alpha &amp; beta</p><script>hidden</script><style>hidden</style><img src='https://invalid.example/image'>", "body_format": "html"}
        with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("network forbidden")):
            self.assertEqual(normalize_row(row)[2], "alpha & beta")
        message = EmailMessage()
        message.set_content(row["body"], subtype="html", charset="utf-8")
        self.assertEqual(normalize_row({"raw": message.as_bytes()})[2], "alpha & beta")

    def test_unicode_and_round_provenance_not_false_label_conflict(self):
        first = {"subject": "caf" + "é", "body": "alpha", "source_round": "r1"}
        other = {"subject": "cafe" + "\u0301", "body": " alpha ", "source_round": "r2"}
        records, count = deduplicate([first, other], {})
        self.assertEqual((count, len(records), records[0]["annotation_conflict"]), (2, 1, False))

    def test_no_opt_in_has_no_guard_transfer_or_output(self):
        self.arguments.update(opt_in=False, input_path=self.base / "missing")
        with patch.object(ingestion, "inclusion") as guard, patch.object(ingestion, "transfer") as transfer:
            with self.assertRaisesRegex(IngestionError, "explicit_opt_in_required"):
                ingestion.ingest(**self.arguments)
            guard.assert_not_called()
            transfer.assert_not_called()
        self.assertFalse(Path(self.arguments["output_dir"]).exists())

    def test_real_production_audit_blocks_unresolved_source_before_io(self):
        self.arguments.update(dataset_id="talby/spamassassin", revision="a1b3371d2df15575f766c081cb329543955d27f6", artifact="spamassassin.py", policy_root=ingestion.ROOT, input_path=self.base / "missing")
        with patch.object(ingestion, "transfer") as transfer:
            with self.assertRaisesRegex(IngestionError, "rights_not_approved"):
                ingestion.ingest(**self.arguments)
            transfer.assert_not_called()

    def test_bad_hash_never_reaches_parser_and_rolls_back(self):
        self.admit((canonical_json(self.sample()) + "\n").encode())
        original = self.input.read_bytes()
        self.input.write_bytes(b"x" + original[1:])
        with patch.object(ingestion, "rows", side_effect=AssertionError("parser reached")):
            with self.assertRaisesRegex(IngestionError, "artifact_checksum_mismatch"):
                ingestion.ingest(**self.arguments)
        self.assertEqual(self.input.read_bytes(), b"x" + original[1:])
        self.assertFalse(Path(self.arguments["output_dir"]).exists())

    def test_truncation_and_oversize_preserve_original(self):
        for difference in (-1, 1):
            with self.subTest(difference=difference):
                self.admit((canonical_json(self.sample()) + "\n").encode())
                changed = self.input.read_bytes()[:-1] if difference == -1 else self.input.read_bytes() + b"x"
                self.input.write_bytes(changed)
                with self.assertRaisesRegex(IngestionError, "artifact_(checksum|size)_mismatch"):
                    ingestion.ingest(**self.arguments)
                self.assertEqual(self.input.read_bytes(), changed)
                self.assertFalse(Path(self.arguments["output_dir"]).exists())

    def test_invalid_records_and_parser_failures_rollback_without_content(self):
        sentinel = "PRIVATE" + "_SENTINEL"
        cases = [(b'{"body":' + sentinel.encode(), ".jsonl"), (b'{"subject":"x","subject":"y","body":"z"}\n', ".jsonl"), (canonical_json({"subject": "x"}).encode() + b"\n", ".jsonl"), (canonical_json({"subject": "x", "body": " "}).encode() + b"\n", ".jsonl"), (b"not-" + sentinel.encode(), ".parquet"), (b"", ".jsonl"), (b"[]", ".json"), (b"\xff" + sentinel.encode(), ".jsonl"), (b"Subject: a\r\nSubject: b\r\n\r\n" + sentinel.encode(), ".eml")]
        for payload, suffix in cases:
            with self.subTest(suffix=suffix, length=len(payload)):
                self.admit(payload, suffix)
                captured = io.StringIO()
                with redirect_stdout(captured), redirect_stderr(captured), self.assertRaises(IngestionError) as failure:
                    ingestion.ingest(**self.arguments)
                self.assertNotIn(sentinel, str(failure.exception))
                self.assertEqual(captured.getvalue(), "")
                self.assertEqual(self.input.read_bytes(), payload)
                self.assertFalse(Path(self.arguments["output_dir"]).exists())

    def test_invalid_mime_and_content_types_are_static_errors(self):
        with self.assertRaises(IngestionError):
            mime_text(b"Content-Type: multipart/mixed; boundary=missing\r\n\r\n" + b"alpha")
        for row in ({"subject": "x", "body": 4}, {"subject": "x", "body": "alpha", "unknown": "private"}, {"subject": "x", "body": "\0"}, {"raw": b"x", "body": "alpha"}, {"subject": "x", "body": "a" * 200001}):
            with self.subTest(keys=list(row)):
                with self.assertRaises(IngestionError):
                    normalize_row(row)

    def test_existing_run_and_unignored_repo_output_are_preserved(self):
        self.admit((canonical_json(self.sample()) + "\n").encode())
        existing = Path(self.arguments["output_dir"])
        existing.mkdir(parents=True)
        (existing / "marker").write_bytes(b"previous-run")
        with self.assertRaisesRegex(IngestionError, "output_already_exists"):
            ingestion.ingest(**self.arguments)
        self.assertEqual((existing / "marker").read_bytes(), b"previous-run")
        self.arguments["output_dir"] = self.root / "unsafe-run"
        with self.assertRaisesRegex(IngestionError, "output_not_private"):
            ingestion.ingest(**self.arguments)
        self.assertFalse((self.root / "unsafe-run").exists())

    def test_symlinked_output_is_rejected(self):
        self.admit((canonical_json(self.sample()) + "\n").encode())
        actual = self.base / "actual"
        actual.mkdir()
        link = self.base / "link"
        link.symlink_to(actual, target_is_directory=True)
        self.arguments["output_dir"] = link / "run"
        with self.assertRaisesRegex(IngestionError, "linked_path_unsupported"):
            ingestion.ingest(**self.arguments)
        self.assertEqual(list(actual.iterdir()), [])

    def test_download_explicit_pinned_request_and_failed_transfer_cleanup(self):
        payload = (canonical_json(self.sample()) + "\n").encode()
        self.admit(payload)
        self.arguments.pop("input_path")
        self.arguments["download"] = True
        opener = unittest.mock.Mock()
        opener.open.return_value = io.BytesIO(payload)
        with patch("urllib.request.build_opener", return_value=opener):
            receipt = ingestion.ingest(**self.arguments)
        self.assertEqual(opener.open.call_args.args[0].full_url, receipt["input"]["url"])
        self.arguments["output_dir"] = self.base / "failed-download"
        opener.open.side_effect = OSError("PRIVATE" + "_NETWORK_ERROR")
        with patch("urllib.request.build_opener", return_value=opener), self.assertRaisesRegex(IngestionError, "artifact_transfer_failed"):
            ingestion.ingest(**self.arguments)
        self.assertFalse((self.base / "failed-download").exists())

    def test_redirect_boundary_has_no_network(self):
        handler = ingestion.PinnedRedirect()
        request = urllib.request.Request("https://huggingface.co/initial")
        for target in ("http://huggingface.co/data", "https://huggingface.co.evil.invalid/data", "file:///private", "https://user:password@huggingface.co/data"):
            with self.subTest(target=target), self.assertRaisesRegex(IngestionError, "unapproved_artifact_redirect"):
                handler.redirect_request(request, None, 302, "", {}, target)
        redirected = handler.redirect_request(request, None, 302, "", {}, "https://cdn.hf.co/object")
        self.assertEqual(redirected.full_url, "https://cdn.hf.co/object")

    def test_parquet_row_limit_before_decoding_rows(self):
        buffer = pa.BufferOutputStream()
        pq.write_table(pa.table({"subject": ["topic"] * 100001, "body": ["alpha"] * 100001}), buffer)
        self.admit(buffer.getvalue().to_pybytes(), ".parquet")
        with self.assertRaisesRegex(IngestionError, "row_limit"):
            ingestion.ingest(**self.arguments)
        self.assertFalse(Path(self.arguments["output_dir"]).exists())

    def test_receipt_commit_failure_removes_only_owned_new_run(self):
        self.admit((canonical_json(self.sample()) + "\n").encode())
        previous = self.base / "previous"
        previous.mkdir()
        (previous / "marker").write_bytes(b"preserved")
        with patch.object(ingestion.os, "replace", side_effect=OSError("commit failed")), self.assertRaisesRegex(IngestionError, "ingestion_failed"):
            ingestion.ingest(**self.arguments)
        self.assertFalse(Path(self.arguments["output_dir"]).exists())
        self.assertEqual((previous / "marker").read_bytes(), b"preserved")

    def test_cli_no_opt_in_and_invalid_arguments_do_not_echo_content(self):
        script = Path(ingestion.__file__)
        token = "PRIVATE" + "_CLI_TOKEN"
        command = [str(Path(__import__("sys").executable)), str(script)]
        result = subprocess.run(command + ["--unknown", token], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(token, result.stdout + result.stderr)
        result = subprocess.run(command + ["--dataset-id", "fixture/synthetic", "--revision", "a" * 40, "--artifact", "rows.jsonl", "--purpose", "commercial_training", "--target", "specialized-email-classifier", "--output-dir", str(self.base / "no-run"), "--input", str(self.base / "missing")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr.strip(), "ingestion_error:explicit_opt_in_required")
        self.assertFalse((self.base / "no-run").exists())

    def test_real_repository_ignore_contract(self):
        for path in ("training/data/synthetic-run/source.parquet", "training/outputs/synthetic-run/records.jsonl", "training/data/synthetic-run/receipt.json"):
            result = ingestion.git(["check-ignore", "--no-index", "-q", "--", path], ingestion.ROOT)
            self.assertEqual(result.returncode, 0)
        tracked = ingestion.git(["ls-files", "--", "training/data", "training/outputs"], ingestion.ROOT)
        self.assertEqual((tracked.returncode, tracked.stdout.strip()), (0, ""))


if __name__ == "__main__":
    unittest.main()
