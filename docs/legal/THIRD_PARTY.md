# Third-party inventory and redistribution boundary

Inventory baseline: source commit 15d0bc8 (before FDEC-001). No Cargo.toml,
Cargo.lock, Python requirements, vendored runtime libraries, datasets or model
weights are present. Planned dependencies in README are not shipped dependencies.
This inventory is not a license approval for future downloads.

| Material | Exact source/version | Terms and notices | Distribution decision |
| --- | --- | --- | --- |
| Apache-2.0 license text, LICENSE | https://www.apache.org/licenses/LICENSE-2.0.txt; SHA256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30 | Standard license text; retain verbatim | Included as the original-source license |
| FDTasks lifecycle snapshot, Tasks/policy/upstream-5.6.md | fedrnv/FDTasks commit 00a0d019c1e73d5ecf4c4e75c42c38497c154e50; SHA256 ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403 | No LICENSE/COPYING file found in the pinned repository; explicit reuse rights unresolved | Already present process reference; excluded from Apache grant; external redistribution blocked pending documented permission |
| Qwen3-0.6B and GGUF backend | Planned only; no artifact/version admitted | Audit exact weights, tokenizer, conversion code and backend separately before use/distribution | Not included; not approved |
| Training and evaluation data | No dataset admitted | Record source, version, consent/privacy basis, license, attribution and derivatives rights in FDEC-008 | Not included; not approved |

An Apache license on original source does not relicense third-party material.
Before including a dependency, record the locked version, upstream license text,
compatibility assessment, required notices, modifications and distribution scope.
Once Cargo.toml exists, use the locked dependency graph and run
`cargo deny check licenses` locally; missing tool/configuration or unknown terms
must block approval rather than be recorded as PASS. Python training dependencies
and native/backend components require their own inventories when introduced.

Each model/dataset audit must also identify exact artifact hashes, source URLs,
commercial/derivative/redistribution restrictions and decision owner. Unknown or
conflicting rights fail closed. Document approval before changing an inventory
entry to approved; approval alone does not authorize external publication.

Governance validation is read-only and local. It checks the original license text
and requires every inventory entry marked included to have affirmative license
evidence. It does not grant rights, replace legal review or authorize publishing.
The unresolved FDTasks reference must be cleared or excluded by a separately
reviewed distribution plan before any external source package is published.
