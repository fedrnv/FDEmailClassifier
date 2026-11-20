# FDEC-003 dependency license audit

The initial schema introduces serde 1.0.229 (derive enabled) and serde_json
1.0.151 (local tests only). The committed Cargo lockfiles pin all transitive
versions and registry checksums. `dependency-inventory.json` records the resolved
workspace graph, original license expressions and local decision. Python's
isolated graph is a subset and is separately checked with cargo-deny.

Audit source: each exact crates.io package's Cargo.toml and unmodified bundled
LICENSE/COPYING files in `dependency-notices/<name>-<version>`. All packages are
unmodified. Apache-2.0 is selected for dual MIT/Apache packages; MIT is selected
for memchr (Unlicense OR MIT) and required by zmij. unicode-ident additionally
requires Unicode-3.0; retain its Unicode copyright and permission notice with
distributed documentation. Keep all bundled license notices in source packages;
carry applicable copyright/permission notices into binary distribution notices.
No additional NOTICE files were found in these package roots.

These license grants permit use/modification/redistribution subject to preserving
their notices; the terms are compatible with original Apache-2.0 project code.
Local admission accepts this exact locked graph and records the three allowed
licenses in deny.toml. Audit future additions and changes before expanding it.
This audit does not approve models, datasets or the unresolved FDTasks snapshot,
and does not authorize any external release. See docs/legal/THIRD_PARTY.md for
the original-source inventory baseline and continuing distribution restrictions.

Verification: `cargo deny --offline check licenses` and `cargo deny --offline
--manifest-path bindings/python/Cargo.toml --config deny.toml check licenses`.
Both must pass; unknown or incompatible terms block admission.
