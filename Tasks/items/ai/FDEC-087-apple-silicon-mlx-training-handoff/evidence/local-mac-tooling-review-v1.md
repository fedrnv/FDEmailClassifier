# Local Mac tooling use, no redistribution approval

The 40 exact CPython 3.14/macOS 15+/arm64 wheel artifacts in
mac-wheel-observations-v1.json match publisher version APIs, filenames, sizes
and SHA-256. They were cross-downloaded for inspection on Windows, not installed
or executed. No PyTorch/PEFT/GPU VPS is in this dependency closure, and no
pretrained weights, training emails or category labels were downloaded.

MLX 0.32.4, mlx-metal 0.32.4 and MLX-LM 0.32.2 declare MIT and include their
versioned notices. Exact official source tag revisions and API document hashes
are preserved separately. The selected dependencies use MIT, BSD variants,
Apache-2.0, ISC, CNRI-Python, PSF-2.0 and MPL-2.0/MIT combinations. Null metadata
fields for safetensors, Jinja2, colorama, markdown-it and mdurl are resolved from
their actual wheel notices, not assumed to mean no license. tokenizers 0.23.3
and sentencepiece 0.2.3 lack embedded license files; the exact official-version
Apache-2.0 supplements already reviewed in FDEC-019 are recorded explicitly.

These documented licenses permit local software inspection/use with notices
retained. This authorizes only an exact offline, no-deps, require-hashes local
tooling installation after the owner's explicit Mac transition confirmation.
It does not approve package/native runtime redistribution, model/tokenizer
distribution, new dataset use or commercial training on unreviewed material.
The macOS system/Metal framework remains the owner's licensed installed OS;
this project neither bundles nor relicenses it. An actual Mac compatibility and
numerical smoke/resume pass remains unperformed and must be recorded there.
