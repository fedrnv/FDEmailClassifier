"""Fresh pinned-source CPU build and hash-checked local GGUF runtime probe."""
import hashlib
import os
from pathlib import Path
import subprocess

from common import ExportError, digest_file, reject_links


def build(checkout, directory, source_revision):
    """Compile the already verified checkout; no arbitrary binary/approval input.

    The caller owns a fresh private temporary directory and verifies the exact
    clean upstream source revision before this operation. Build output is never
    included in a model candidate. Existing runtimes are not overwritten.
    """
    directory = reject_links(directory)
    if directory.exists(): raise ExportError("runtime_build_directory_exists")
    generator = ["-G", "Visual Studio 17 2022", "-A", "x64"] if os.name == "nt" else []
    commands = [["cmake", *generator, "-S", str(checkout), "-B", str(directory), "-DBUILD_SHARED_LIBS=OFF", "-DLLAMA_CURL=OFF", "-DLLAMA_OPENSSL=OFF", "-DGGML_NATIVE=OFF", "-DGGML_CUDA=OFF", "-DGGML_METAL=OFF", "-DLLAMA_BUILD_TESTS=OFF", "-DLLAMA_BUILD_TOOLS=ON", "-DLLAMA_BUILD_EXAMPLES=ON"],
                ["cmake", "--build", str(directory), "--config", "Release", "--target", "llama-completion", "--parallel", "2"]]
    environment = os.environ.copy()
    environment.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    for command in commands:
        result = subprocess.run(command, capture_output=True, timeout=1200, env=environment)
        if result.returncode: raise ExportError("pinned_runtime_build_failed")
    name = "llama-completion.exe" if os.name == "nt" else "llama-completion"
    options = [directory / "bin" / name, directory / "bin/Release" / name]
    executable = next((reject_links(path) for path in options if path.is_file()), None)
    if executable is None: raise ExportError("built_runtime_missing")
    return executable, dict(source_revision=source_revision, executable_sha256=digest_file(executable, 1_000_000_000)["sha256"],
                            cmake_cache_sha256=digest_file(directory / "CMakeCache.txt", 10_000_000)["sha256"],
                            build="fresh-cmake-cpu-static-completion; not a redistributed runtime")


def compare(directory, executable, build_record, current_check):
    hashes = []
    for name, extra in (("base-f16.gguf", ["--lora", str(directory / "adapter-f16.gguf")]), ("classifier-f16.gguf", [])):
        current_check()
        if digest_file(executable, 1_000_000_000)["sha256"] != build_record["executable_sha256"]: raise ExportError("built_runtime_changed")
        # Numerical load/adapter integration only. No emails, gold labels or
        # natural-language test dataset. Never log captured model responses.
        command = [str(executable), "-m", str(directory / name), "-p", "1", "-n", "2", "--temp", "0", "--seed", "0", "--no-conversation", "--simple-io", "--no-display-prompt", "--no-warmup", "--ignore-eos", *extra]
        environment = os.environ.copy()
        environment.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
        result = subprocess.run(command, capture_output=True, timeout=300, env=environment)
        if result.returncode or not result.stdout.strip(): raise ExportError("gguf_runtime_load_probe_failed")
        hashes.append(hashlib.sha256(result.stdout).hexdigest())
    if hashes[0] != hashes[1]: raise ExportError("merged_and_adapter_runtime_probe_differ")
    current_check()
    if digest_file(executable, 1_000_000_000)["sha256"] != build_record["executable_sha256"]: raise ExportError("built_runtime_changed")
    return dict(**build_record, model_load_and_two_token_probe_verified=True, merged_adapter_probe_equal=True,
                probe_output_sha256=hashes[0], scope="numerical-probe-only; no classifier-quality measurement")
