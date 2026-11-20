"""Explicit, rights-gated local training ingestion. No Hub code execution."""

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

from normalize_email import IngestionError, MAX_MESSAGE_BYTES, MAX_ROWS, MAX_TOTAL_TEXT_BYTES, VERSION, canonical_json, deduplicate

ROOT = Path(__file__).resolve().parents[2]
PYARROW_VERSION = "26.0.1"


def reject_links(path):
    path = Path(os.path.abspath(path))
    for item in (path, *path.parents):
        if item.is_symlink() or item.is_junction():
            raise IngestionError("linked_path_unsupported")
    return path


def git(args, cwd):
    try:
        environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=30, env=environment)
    except (OSError, subprocess.SubprocessError):
        raise IngestionError("git_inspection_failed") from None


def private_output(path, policy_root):
    # Resolve existing ancestors (including Windows 8.3 aliases) only after
    # rejecting links, so Git's canonical root and this path share spelling.
    path = reject_links(path).resolve()
    if path.exists():
        raise IngestionError("output_already_exists")
    parent = path.parent
    while not parent.exists():
        parent = parent.parent
    containing = git(["rev-parse", "--show-toplevel"], parent)
    if containing.returncode == 0:
        repository = Path(containing.stdout.strip()).resolve()
        policy_root = Path(policy_root).resolve()
        if repository != policy_root or not any(path.is_relative_to(repository / area) for area in ("training/data", "training/outputs")):
            raise IngestionError("output_not_private")
        relative = path.relative_to(repository).as_posix()
        tracked = git(["ls-files", "--", relative], repository)
        ignored = git(["check-ignore", "--no-index", "-q", "--", relative], repository)
        if tracked.returncode or tracked.stdout.strip() or ignored.returncode:
            raise IngestionError("output_not_private")
    elif containing.returncode != 128 or "not a git repository" not in containing.stderr.lower():
        raise IngestionError("git_inspection_failed")
    return path


def inclusion(dataset_id, revision, artifact, purpose, target, policy_root=ROOT):
    shell = shutil.which("powershell.exe") or shutil.which("pwsh")
    if not shell:
        raise IngestionError("rights_guard_unavailable")
    try:
        result = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-File", str(ROOT / "training/datasets/get-inclusion.ps1"), "-Root", str(policy_root), "-DatasetId", dataset_id, "-Revision", revision, "-ArtifactPath", artifact, "-Purpose", purpose, "-Target", target], capture_output=True, encoding="utf-8", errors="replace", timeout=60)
        if result.returncode:
            raise IngestionError("rights_not_approved")
        descriptor = json.loads(result.stdout.lstrip("\ufeff"))
        expected = {"schema", "dataset_id", "revision", "artifact", "sha256", "size", "url", "license", "purpose", "target", "attribution", "audit_sha256"}
        if not isinstance(descriptor, dict) or set(descriptor) != expected or descriptor["schema"] != "fdec-dataset-inclusion/v1":
            raise IngestionError("invalid_rights_descriptor")
        if [descriptor[key] for key in ("dataset_id", "revision", "artifact", "purpose", "target")] != [dataset_id, revision, artifact, purpose, target]:
            raise IngestionError("invalid_rights_descriptor")
        if not re.fullmatch(r"[a-f0-9]{64}", descriptor["sha256"]) or type(descriptor["size"]) is not int or not 0 < descriptor["size"] <= 100_000_000:
            raise IngestionError("invalid_artifact_bounds")
        if descriptor["url"] != f"https://huggingface.co/datasets/{dataset_id}/resolve/{revision}/{artifact}":
            raise IngestionError("invalid_artifact_url")
        return descriptor
    except IngestionError:
        raise
    except Exception:
        raise IngestionError("rights_guard_failed") from None


class PinnedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        host = parsed.hostname or ""
        if parsed.scheme != "https" or parsed.username or parsed.password or not (host == "huggingface.co" or host.endswith(".huggingface.co") or host == "hf.co" or host.endswith(".hf.co")):
            raise IngestionError("unapproved_artifact_redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def transfer(descriptor, destination, local_input=None):
    digest = hashlib.sha256()
    length = 0
    try:
        if local_input is not None:
            source_path = reject_links(local_input)
            if not source_path.is_file():
                raise IngestionError("input_not_regular_file")
            source = source_path.open("rb")
        else:
            opener = urllib.request.build_opener(PinnedRedirect())
            source = opener.open(urllib.request.Request(descriptor["url"], headers={"User-Agent": "FDEmailClassifier-ingestion/v1"}), timeout=30)
        with source, destination.open("xb") as output:
            while chunk := source.read(65536):
                length += len(chunk)
                if length > descriptor["size"]:
                    raise IngestionError("artifact_size_mismatch")
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if length != descriptor["size"] or digest.hexdigest() != descriptor["sha256"]:
            raise IngestionError("artifact_checksum_mismatch")
    except IngestionError:
        raise
    except Exception:
        raise IngestionError("artifact_transfer_failed") from None


def strict_json(value):
    def pairs(items):
        result = {}
        for key, item in items:
            if key in result:
                raise IngestionError("duplicate_json_field")
            result[key] = item
        return result

    def invalid_constant(value):
        raise IngestionError("invalid_json_constant")

    try:
        return json.loads(value, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except IngestionError:
        raise
    except Exception:
        raise IngestionError("invalid_json") from None


def rows(path):
    suffix = path.suffix.lower()
    if suffix == ".eml":
        yield {"raw": path.read_bytes()}
    elif suffix == ".jsonl":
        with path.open("rb") as source:
            while line := source.readline(MAX_MESSAGE_BYTES + 1):
                if len(line) > MAX_MESSAGE_BYTES or not line.strip():
                    raise IngestionError("invalid_jsonl_record")
                yield strict_json(line.decode("utf-8", errors="strict"))
    elif suffix == ".json":
        if path.stat().st_size > 20_000_000:
            raise IngestionError("json_size_limit")
        values = strict_json(path.read_text(encoding="utf-8", errors="strict"))
        if not isinstance(values, list):
            raise IngestionError("invalid_json_dataset")
        yield from values
    elif suffix == ".parquet":
        try:
            import pyarrow
            import pyarrow.parquet as parquet
            if pyarrow.__version__ != PYARROW_VERSION:
                raise IngestionError("unsupported_parquet_dependency")
            with parquet.ParquetFile(path, memory_map=False, pre_buffer=False, thrift_string_size_limit=1_000_000, thrift_container_size_limit=100_000, schema_depth_limit=20, page_checksum_verification=True, arrow_extensions_enabled=False) as source:
                if source.metadata.num_rows > MAX_ROWS:
                    raise IngestionError("row_limit")
                uncompressed = sum(source.metadata.row_group(group).column(column).total_uncompressed_size for group in range(source.metadata.num_row_groups) for column in range(source.metadata.num_columns))
                if uncompressed > MAX_TOTAL_TEXT_BYTES:
                    raise IngestionError("parquet_uncompressed_limit")
                for batch in source.iter_batches(batch_size=64, use_threads=False, use_pandas_metadata=False):
                    yield from batch.to_pylist()
        except IngestionError:
            raise
        except Exception:
            raise IngestionError("invalid_or_unavailable_parquet") from None
    else:
        raise IngestionError("unsupported_artifact_format")


def remove_owned(path, token):
    # Verify the exact exclusively-created directory before recursive cleanup.
    if reject_links(path) != path or not path.is_dir() or (path / ".owner").read_text(encoding="ascii") != token:
        raise IngestionError("cleanup_ownership_changed")
    shutil.rmtree(path)


def ingest(*, dataset_id, revision, artifact, purpose, target, output_dir, opt_in=False, download=False, input_path=None, policy_root=ROOT):
    if opt_in is not True:
        raise IngestionError("explicit_opt_in_required")
    if download == (input_path is not None):
        raise IngestionError("select_one_input_mode")
    descriptor = inclusion(dataset_id, revision, artifact, purpose, target, policy_root)
    suffix = Path(artifact).suffix.lower()
    if suffix not in {".parquet", ".json", ".jsonl", ".eml"}:
        raise IngestionError("unsupported_artifact_format")
    if input_path is not None:
        input_path = reject_links(input_path)
        if not input_path.is_file():
            raise IngestionError("input_not_regular_file")
    output = private_output(output_dir, policy_root)
    missing_parents = []
    created_parents = []
    parent = output.parent
    while not parent.exists():
        missing_parents.append(parent)
        parent = parent.parent
    owned = False
    token = secrets.token_hex(16)
    try:
        for parent in reversed(missing_parents):
            parent.mkdir(mode=0o700)
            created_parents.append(parent)
        # Exclusive mkdir never overwrites a previous run, even an empty one.
        output.mkdir(mode=0o700)
        owned = True
        (output / ".owner").write_text(token, encoding="ascii")
        local_source = output / ("source" + suffix)
        transfer(descriptor, local_source, input_path)
        source_identity = {key: descriptor[key] for key in ("dataset_id", "revision", "artifact", "sha256")}
        # Consumer validation may fail while the iterator is suspended in an
        # open file. Close it before rollback, including on Windows file locks.
        with closing(rows(local_source)) as source_rows:
            records, count = deduplicate(source_rows, source_identity)
        content = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
        with (output / "records.jsonl").open("xb") as destination:
            destination.write(content)
            destination.flush()
            os.fsync(destination.fileno())
        implementation = hashlib.sha256()
        for script in (Path(__file__), Path(__file__).with_name("normalize_email.py")):
            implementation.update(script.read_bytes().replace(b"\r\n", b"\n"))
        receipt = {"schema": "fdec-ingestion-receipt/v1", "normalization_version": VERSION, "implementation_sha256": implementation.hexdigest(), "python_version": sys.version.split()[0], "decoder": "pyarrow/" + PYARROW_VERSION if suffix == ".parquet" else "python-stdlib", "input": descriptor, "source_file": local_source.name, "records_file": "records.jsonl", "records_sha256": hashlib.sha256(content).hexdigest(), "input_rows": count, "unique_rows": len(records), "duplicates": count - len(records), "annotation_conflicts": sum(record["annotation_conflict"] for record in records)}
        # The completion marker is last. Consumers must require and verify it.
        with (output / ".receipt.part").open("xb") as destination:
            destination.write((canonical_json(receipt) + "\n").encode("utf-8"))
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(output / ".receipt.part", output / "receipt.json")
        return receipt
    except Exception as error:
        if owned:
            remove_owned(output, token)
        for parent in reversed(created_parents):
            if parent.exists():
                try:
                    parent.rmdir()
                except OSError:
                    pass
        if isinstance(error, IngestionError):
            raise
        raise IngestionError("ingestion_failed") from None


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "ingestion_error:invalid_arguments\n")


def main(argv=None):
    parser = PrivateArgumentParser(description="Opt-in, rights-gated private training ingestion")
    for name in ("dataset-id", "revision", "artifact", "purpose", "target", "output-dir"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--opt-in", action="store_true")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--download", action="store_true")
    mode.add_argument("--input", dest="input_path")
    arguments = parser.parse_args(argv)
    try:
        receipt = ingest(dataset_id=arguments.dataset_id, revision=arguments.revision, artifact=arguments.artifact, purpose=arguments.purpose, target=arguments.target, output_dir=arguments.output_dir, opt_in=arguments.opt_in, download=arguments.download, input_path=arguments.input_path)
        print(canonical_json({key: receipt[key] for key in ("schema", "input_rows", "unique_rows", "duplicates", "records_sha256")}))
        return 0
    except IngestionError as error:
        print("ingestion_error:" + error.args[0], file=sys.stderr)
        return 2
    except Exception:
        print("ingestion_error:ingestion_failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
