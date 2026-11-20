# Training ingestion dependency audit

FDEC-009 uses Python only for training preprocessing. No Python runtime is added
to the Rust production workspace. Verified environment: CPython 3.14.5, Windows
x64, isolated `.venv/ingestion`. Other platform wheels require their own verified
hash before extending this environment lock.

| Material | Pin and evidence | Decision |
| --- | --- | --- |
| PyArrow | [26.0.1 PyPI metadata](https://pypi.org/pypi/pyarrow/26.0.1/json); `pyarrow-26.0.1-cp314-cp314-win_amd64.whl`, 29,757,743 bytes; SHA256 `492dc499097968e51cac46e03e0054c68dd3c5f39d75098343f5ad05ec79f7df` | Local training-only install from a hash-checked binary wheel |
| Project license and bundled notices | PyPI declares Apache-2.0; [upstream release license](https://github.com/apache/arrow/blob/apache-arrow-26.0.1/LICENSE.txt). Installed `dist-info/licenses/LICENSE.txt` SHA256 `2a255e0ef5946efdb2e01a4861460ce4a3333734666d256e75f9c1731a5097da`; `NOTICE.txt` SHA256 `2ccca1e730e671f55b8028facf2261a6f74b561a4d96a2ccd743be19c5619236` | Preserve installed project/component notices; no wheel redistribution or bundling approved here |
| Python dependencies | Pinned release metadata and installed distribution report no `Requires-Dist`; `pip check` passes | No extra training Python package admitted |
| CPython standard library | Existing CPython 3.14.5; email, HTML, JSON, hashing, HTTPS and filesystem APIs | Local installed runtime; no copied interpreter or third-party generator code |

The requirements file uses `--require-hashes` installation with binary-only wheels.
No dataset payload, native model or trained weight is a dependency of this test
environment. Package installation is distinct from opt-in dataset download.
The native Parquet reader is used only after the audited artifact's byte checksum
matches. It disables extension decoding, bounds metadata/row/uncompressed sizes
and reads bounded batches without Hub scripts, pandas or pickle.

API references: [ParquetFile](https://arrow.apache.org/docs/python/generated/pyarrow.parquet.ParquetFile.html),
[Python 3.14 email parsing](https://docs.python.org/3.14/library/email.parser.html)
and [owned-directory cleanup](https://docs.python.org/3.14/library/shutil.html).
The installed license files include additional component notices; Apache-2.0
metadata is not a replacement for those notices or an artifact publication audit.
