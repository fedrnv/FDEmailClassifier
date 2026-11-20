# FDEC-002 verification and checkpoint

Baseline: 6a28646cab9083cf61562becf4cf16adb5080d9d. Policy SHA256:
ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403.
Environment: Windows x86_64 MSVC, Rust/Cargo 1.98.0, cargo-deny 0.20.2,
PowerShell 5.1. Pinned toolchain installed locally. No external downloads required.

AC-01 PASS: powershell -NoProfile -File crates/check-bootstrap.ps1
Command includes cargo check --workspace --locked --offline, individual cargo
build --locked --offline -p commands for core/ffi/server/example, separate binding
manifest build with --target-dir target/python, Rust example execution, server
help/version, cargo deny --offline check licenses and cargo fmt --all -- --check.
Initial run failed only at cargo-deny argument parsing (--config after check).
Corrected command and default root config; final script run exit 0. This is a
candidate correction, not an unchanged retry or infrastructure flake.
AC-02 PASS: no args, --serve, and --help unexpected return exit 2; unknown package
check fails without changing Cargo.lock. No service listener or raw input logging.
Additional direct compatibility: cargo deny --offline --manifest-path
bindings/python/Cargo.toml --config deny.toml check licenses => licenses ok.
powershell -NoProfile -File docs/legal/test-governance.ps1 => PASS, including the
now-applicable Cargo audit. No third-party runtime packages in either lockfile.
Git diff --check => PASS; actual source and manifest diff inspected.

## Scope and limitations
Core/FFI/server and Python are build scaffolds. No inference, C ABI exports,
REST listener or importable Python extension is claimed. Future tasks own these
contracts. Version 0.0.0 is an unpublished placeholder, not an allocated version.
Root deny.toml is explicitly included by append-only scope amendment to preserve
FDEC-001's default license command. No accepted specifications or rules changed.
FDTasks snapshot redistribution remains unresolved and external publication stays
blocked; this does not require an external action for local development.
Only root ignored target contains build outputs; no watcher/server remains live.

## Raw candidate hashes
- Cargo.toml: d3ff03adddb098e9e8b60163181ae6b9fe83884ab65eaaba95670912cd700137
- Cargo.lock: 68b33684e1c3b343b9c02501c666f38cb1e9ccc5e3ec5e605cc266df13e7abb2
- rust-toolchain.toml: e879701472a698533f43f54989bbf5f3101eb0503472159d32633f3bb8a13fdf
- deny.toml: fb5a200394cb4e4c0a23cc81f0cb8f0e1080ea4ada07cb885b61c37346f69f3d
- crates/check-bootstrap.ps1: 11f8eb8fb4b34e022310408ecda1b2d39ea8ff0ec9aeea79cd547b10ed54534c
- crates/README.md: d16c68810f65a57813adbb60d4cb4f0b6858a4939a3cdf50b30a9c8037ee822c
- crates/core/Cargo.toml: 6f4e46ec26d0ff07b09ffd7e500414cb5a10c03bc7cbc10a310b81dc2747928d
- crates/core/src/lib.rs: b2ba7211fb6a1c4ef180000b4b8f9d061ede3c3b7cca7c243a266a08c48d374b
- crates/ffi/Cargo.toml: f8532dec70a9c05ed6353ced87738e5791c77a087889310a0bc9b91dca8db070
- crates/ffi/src/lib.rs: f5e6b2764a9f46a2bab3967c43f0173fb4226a5dd84ed258222f2d131e5f1fd7
- crates/server/Cargo.toml: 4ed834be3f91f32eca925ab82b52d396c117adc64d2a8dcb20a0c5ae30633f2e
- crates/server/src/main.rs: c1d1102c9e98a391a22691d1c41ef8fdb8c72ef072f48cb84ca7ea61248562ee
- bindings/python/Cargo.lock: 48e64153a2501bfa0bdf85af9228ad04d14585f09496988178bb106baa59d789
- bindings/python/Cargo.toml: e1bc9946be149771e3c0066bba4093547a558c1d45a4328b9e30269a19e2a104
- bindings/python/README.md: 3833b0cb59f41722bc23dd842ed0eebf210d712b15b6d3edc4c79d15bd0c41b3
- bindings/python/src/lib.rs: a11f11936f1bb6a05c1af5883ad79307bf6ed53529de4ac9191f27ccec1c71ca
- examples/README.md: 7b9e580ef705ae124f4af8f53d9e7093545e9033c5675d02a8dff027f164d4d8
- examples/rust/Cargo.toml: 03a4236967aaa4ca12690350a617aab0bbd70ea75f9d1466b7548b3e93d574e1
- examples/rust/src/main.rs: 7d0659d62f6e4ea61160d5dd85ed597f5134be141ee860c54fcf3b0b83bc4272

## Continuation
Close FDEC-002 with one task_closed request. Next fresh turn: admit FDEC-003,
inspect its immutable taxonomy/schema contract and implement that single outcome.
D001 alone remains Active; revalidate readiness against new HEAD and dependency
state. Preserve unrelated untracked .idea. Standing local development authority
continues; no external blocker for the next task. Goal remains active.
