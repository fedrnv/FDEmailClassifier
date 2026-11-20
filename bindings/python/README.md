# Python binding scaffold

This is a separate Rust workspace with its own committed lockfile. Build with
`cargo build --locked --manifest-path bindings/python/Cargo.toml --target-dir target/python`.
No Python runtime or PyO3 dependency is needed by the native workspace. No Python
module can be imported yet; FDEC-032 introduces the bindings and packaging.
