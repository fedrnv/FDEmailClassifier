# Workspace bootstrap

Rust/Cargo 1.98.0 is pinned in rust-toolchain.toml. Package version 0.0.0 is a
development placeholder, not an allocated FDTasks version or release. Packages
cannot be published by Cargo. The local closure allocator owns future versions.

The core, native library and server crates build independently. The root workspace
contains the Rust example, while the Python scaffold is a separate workspace.
There are no registry dependencies, model downloads, Python runtime requirements,
network listeners or hosted workflows at this baseline.

Run `powershell -NoProfile -File crates/check-bootstrap.ps1` for the focused local
gate, including each package build, binding isolation, example, argument rejection
and license checks. Build products use the ignored root target directory.
The native library has no stable exported C API yet. The server supports only
help/version and fails closed for every service invocation until FDEC-036.
