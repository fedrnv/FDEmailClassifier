# Contributing

Use English for public code, documentation, issues and pull requests. Start with
AGENTS.md, DEVELOPMENT.md and the immutable task in Tasks/items. Admit the task
under the pinned FDTasks policy before changing its bounded scope. Append events
for state changes; never rewrite accepted specifications or evidence. Keep only
one development Epic active and follow dependency order.

Original contributions are submitted under Apache-2.0, as described in LICENSE,
unless a separate agreement explicitly applies. By submitting a contribution you
confirm that you have the right to contribute it under those terms. Keep existing
copyright, license and attribution notices. Identify third-party material and its
exact source, revision, license and required notices in docs/legal/THIRD_PARTY.md.
Do not submit material with uncertain rights as approved for redistribution.

Use Rust for production code; Python is limited to training and Python bindings.
Use synthetic fixtures. Never commit credentials, raw emails, personal information
or private training data. Report vulnerabilities through SECURITY.md.

Before submitting, inspect the diff, run the task's focused local checks and
changed-boundary negative tests, and record exact commands and results in immutable
task evidence. Governance checks: `powershell -NoProfile -File
docs/legal/test-governance.ps1`. Once a Cargo workspace exists, run
`cargo deny check licenses` locally as well. Do not treat unavailable checks as
passing. Hosted workflows are manually dispatched build/package/publication only;
acceptance and integration tests run locally.

Include the task ID, concrete behavior change, validation and material limitations
in the pull request. Follow CODE_OF_CONDUCT.md during review. Model or dataset
redistribution needs a documented license audit; release/model publication also
requires explicit operator authorization and integrity checks.
