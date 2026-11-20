# FDEC-003 verification and continuation

Source baseline: c625340756ae2bd4f64e94b5b404a2787b692560. Upstream policy source commit:
00a0d019c1e73d5ecf4c4e75c42c38497c154e50; policy SHA256:
ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Environment: Windows x86_64 MSVC, Rust/Cargo 1.98.0, PowerShell 5.1,
cargo-deny 0.20.2, Node 24.22.1, disposable ajv-cli 5.0.0.

AC-01 PASS: cargo test --locked --offline -p fdemailclassifier-core schema
Four tests pass: all output states round-trip; twelve topic labels agree with
JSON Schema; malformed fields/missing fields/duplicate keys rejected; unknown and
abstained invariants enforced on both decoding and typed serialization.
AC-02 PASS: mutation-based negative cases preserve input. Invalid versions,
unknown enum values, duplicate topics, extra fields, missing nested security,
empty classified topics and unsafe abstention fail explicitly. No mailbox,
filesystem or network execution APIs in schema module.
Independent JSON validation: powershell -NoProfile -File schemas/check-schema.ps1
uses ajv-cli 5.0.0 with draft2020. Three valid examples accepted; nine invalid
fixtures rejected with expected schema errors. No private fixtures or email text.
The initial CLI discovery used unsupported --help (exit 1); actual validation
commands are corrected and passed. No failed product acceptance or unchanged retry.

Direct compatibility PASS: cargo check --workspace --locked --offline;
cargo check --locked --offline --manifest-path bindings/python/Cargo.toml
--target-dir target/python. cargo fmt --all -- --check and git diff --check PASS.
License audit initially rejected Unicode-3.0 as expected by old allow-list;
reviewed exact package license files, preserved all notices, and admitted
MIT/Unicode-3.0 along with Apache-2.0 in deny.toml. After correction both:
cargo deny --offline check licenses;
cargo deny --offline --manifest-path bindings/python/Cargo.toml --config deny.toml
check licenses => licenses ok. Exact graph and licenses recorded in
 docs/api/dependency-inventory.json and dependency-audit.md. No model/data license
approval and no external publication. Original FDTasks redistribution restriction
remains in effect.

## Limitations and inspection
Actual types, docs, schemas, fixtures and dependency diff inspected. This is v1
advisory metadata, not model inference, calibration, language-quality reporting,
REST API, ABI or action automation. Duplicate object keys require strict parsing
before generic JSON Schema validation; direct Serde decode rejects them. Typed
validate errors are static, but third-party parser errors may quote input, so
callers are instructed not to log them. No quality guarantees inferred.
Independent Epic review remains FDEC-007. Build outputs reside in ignored target;
Ajv tooling resides in the external npm cache; no temporary repository artifacts.

## Candidate raw file hashes
- Cargo.lock: a7011e342c0d944f28e2ce33ea1c5bc2a54e73294b802c46cdddef646b8c272e
- bindings/python/Cargo.lock: 24d09e047d55668414c981a159779774818ead33beaf79797f089396d345de96
- crates/core/Cargo.toml: e78edc71c56c1c9bc81362c9a2ccb39223a52c2c135dd567ba2160b2436780a1
- crates/core/src/lib.rs: 8f855862fee0461009a66b085608c7171347ab00cd728a01c47e23dc9a09032f
- deny.toml: 4dc7c5e8a63aeb8aaaed860f13e53f3ad3d4f6555f9637bc05a0ec967241ff55
- crates/core/src/schema/mod.rs: 81ffec062b9ac73d1ad22b791b0bd9decb2712af55896dec367081cf496e0665
- crates/core/src/schema/tests.rs: a01372bee8ece6e6663a3a560b499bd8658386f502ce84ed8ff08ee0c5dcbfc2
- schemas/check-schema.ps1: 30aae6fa13a757780f334d8e014930075a1e4d70f67087aa2114ec5a31281269
- schemas/classification-v1.schema.json: 049add9a257a8fc5f9da370c3d61108434354c294205f025f4e06aab9577cf46
- schemas/examples/abstained.json: 150f301977ce3730cad2d04e30716e1f0f9ca2d586452e7b5ab9c3935ec15776
- schemas/examples/classified.json: d6544fb00a0ac80948280bf0ed4a46530f2fbec97cb1c76c6e518d234812b24f
- schemas/examples/unknown.json: d086d63fdb130e6746c3f6d5562e4a55b40c55af422a185552379f24713e922e
- schemas/invalid/abstained.json: fc28bc871704febab4c62d0aa9cf480e999392ee529954e7cd64605960ca0f68
- schemas/invalid/action.json: c668684bb260b977cbab3822e48643bdab5feeddd97d807fb68ef188baa7dc88
- schemas/invalid/duplicate.json: 9b3e041cc5a2db1fad1415625a12851d9ee17d5266bfa2ddac0c83af27a9b9ce
- schemas/invalid/empty.json: 8120c1a44256dc02dd859920fd244f9926ead65daaa3066a967aa5759cfe621c
- schemas/invalid/extra.json: d06c0ceed645be226ab90b1c4bfcd07aa33a7c07619c985d2e96952b35e9ef93
- schemas/invalid/security.json: f999ecb3ce2b484645f435789a60e4b5981e368ad4072fa567a767a537bb93f1
- schemas/invalid/topic.json: e9218ce5c6543ee8447d1f2af080d1ea03b2cee29d64496bfe16f52ef60f9096
- schemas/invalid/unknown.json: 0c953b8bf598cc2f60d4a6ed820fe896276e468d64c88a1881a50cde7d1018eb
- schemas/invalid/version.json: 10390572243ea59622f7bc9d582a6b98ca5e9e7417258c80082c9c486ea276da
- docs/api/classification-v1.md: ff963b48476e42bfd6e5108ad42108797c85662464f3ad49626118ef1afcaf92
- docs/api/dependency-audit.md: 8c7f8f3d881cfb7ff4f10d9dd7c03b2817933b447a5a2dd6519a762fccecb146
- docs/api/dependency-inventory.json: 2903c309a0ef1f88eadc6ad59358bd92000d85b4da023b1ce048919aabb4beb4
- docs/api/dependency-notices/itoa-1.0.18/LICENSE-APACHE: 62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a
- docs/api/dependency-notices/itoa-1.0.18/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3
- docs/api/dependency-notices/memchr-2.8.3/COPYING: 01c266bced4a434da0051174d6bee16a4c82cf634e2679b6155d40d75012390f
- docs/api/dependency-notices/memchr-2.8.3/LICENSE-MIT: 0f96a83840e146e43c0ec96a22ec1f392e0680e6c1226e6f3ba87e0740af850f
- docs/api/dependency-notices/proc-macro2-1.0.107/LICENSE-APACHE: 62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a
- docs/api/dependency-notices/proc-macro2-1.0.107/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3
- docs/api/dependency-notices/quote-1.0.47/LICENSE-APACHE: 62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a
- docs/api/dependency-notices/quote-1.0.47/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3
- docs/api/dependency-notices/serde-1.0.229/LICENSE-APACHE: 62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a
- docs/api/dependency-notices/serde-1.0.229/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3
- docs/api/dependency-notices/serde_core-1.0.229/LICENSE-APACHE: 62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a
- docs/api/dependency-notices/serde_core-1.0.229/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3
- docs/api/dependency-notices/serde_derive-1.0.229/LICENSE-APACHE: 62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a
- docs/api/dependency-notices/serde_derive-1.0.229/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3
- docs/api/dependency-notices/serde_json-1.0.151/LICENSE-APACHE: 62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a
- docs/api/dependency-notices/serde_json-1.0.151/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3
- docs/api/dependency-notices/syn-3.0.5/LICENSE-APACHE: 62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a
- docs/api/dependency-notices/syn-3.0.5/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3
- docs/api/dependency-notices/unicode-ident-1.0.24/LICENSE-APACHE: 62c7a1e35f56406896d7aa7ca52d0cc0d272ac022b5d2796e7d6905db8a3636a
- docs/api/dependency-notices/unicode-ident-1.0.24/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3
- docs/api/dependency-notices/unicode-ident-1.0.24/LICENSE-UNICODE: f7db81051789b729fea528a63ec4c938fdcb93d9d61d97dc8cc2e9df6d47f2a1
- docs/api/dependency-notices/zmij-1.0.23/LICENSE-MIT: 23f18e03dc49df91622fe2a76176497404e46ced8a715d9d2b67a7446571cca3

## Durable checkpoint
FDEC-003 verified for closure with one task_closed request. Next fresh turn:
revalidate FDEC-004 and implement the local repository policy/FDTasks guardrails,
preserving accepted history and the existing 073 adoption. D001 only Active.
No running process, server or external blocker. Preserve unrelated .idea files.
Standing user authority covers sequential local development; external release/model
publication needs explicit operator authorization. Goal remains active.
