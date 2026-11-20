# FDEC-009 verification

Final source: b7ea834 (full revision and tree bound in closure-readiness.json).
Policy SHA256: ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Environment: Windows x64, CPython 3.14.5, isolated ignored ingestion venv,
hash-pinned PyArrow 26.0.1; dependency-pin.json and public dependency notice record
the wheel identity and license. No real dataset downloaded or redistributed.

Command: `powershell -NoProfile -File training/datasets/test-ingestion.ps1`.
Final monitored run c205b471-f2b1-45dc-a0e0-c67237298a29 exited 0.
All 20 synthetic ingestion tests passed, as did the existing allowlist positive
checks, 23 denial scenarios, and pip dependency consistency. See test-output.txt.

AC-01: actual pinned Parquet decoding, JSON/JSONL/EML loading, MIME alternatives,
charset decoding, attachment exclusion and inert visible HTML extraction pass.
Versioned checksums, deterministic normalized records/receipts and deduplication
retain all source-row annotations and mark label conflicts. Source round remains
provenance rather than a semantic label. Actual repository ignore checks pass.

AC-02: explicit opt-in and audited purpose precede artifact I/O. Corrupt hashes,
truncated/oversized artifacts, invalid rows/MIME/Parquet, unsafe outputs, denied
rights, failed transfers and failed receipt publication reject without changing
original files or previous runs. Newly owned incomplete runs are removed. Error
and CLI output checks do not expose message content. Redirect checks and download
fixtures are mocked; these tests do not claim an actual remote corpus transfer.

Earlier failed runs are retained in initial-test-output.txt,
alias-fix-test-output.txt and reader-fix-test-output.txt. They exposed Windows
8.3 path spelling and open reader handles during rollback. Source fixes normalize
ancestor spelling after link rejection and explicitly close suspended iterators
and the Parquet input even on constructor failure. The unchanged negative cases
then passed. No failure was hidden by skipping a test or weakening assertions.

Temporary synthetic fixtures are removed by guarded test cleanup; the pinned
ignored venv is retained for subsequent work. No raw emails, private data or
model artifacts were added to Git. Abrupt process termination can leave a private
incomplete run: consumers must require and verify the receipt written last.
Normalization is not PII sanitization. Label mapping, split construction and PII
policy remain separate tasks. No release, push, deployment or independent Epic
review is claimed by this task-local verification.
