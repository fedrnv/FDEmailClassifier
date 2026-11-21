# Development contract

## Current developer rules — FDTasks 5.7

Read [Tasks/FDTasks_5_7_ADOPTION.md](Tasks/FDTasks_5_7_ADOPTION.md) and the complete
[Tasks/tasks_file_structure_v5_7.md](Tasks/tasks_file_structure_v5_7.md) before
selecting, claiming, resuming or closing work. This owner-requested developer
policy supersedes older generic developer-rule references below; exact source
identity and local status mapping are in `Tasks/developer-policy.json`.
Several developers may share one Epic, each task has one published owner.
Refresh GitHub/project state, publish the claim before implementation, and
immediately push every commit and verified closure. A losing claim refreshes
and reselects; it is never replayed over the winner. Preserve accepted history,
product safety and explicit owner exceptions. Native/automated activation is
separate and must retain its actual qualified version; see the adoption boundary.

Rust is the production implementation language. Python is limited to training and Python bindings. Use versioned contracts and stable C ABI. Run diff-focused local tests before committing changes; separate targeted local integration gates and independent review per development Epic. Confirm exact commands per task as implementation paths become available. No tests in hosted workflows; only explicitly dispatched build/package/publish/cleanup. Keep artifact retention cleanup manual and older than ten days. All release/model publishing requires license and integrity checks and explicit operator authorization. Never log raw emails; fail closed on uncertain security or licensing.

Canonical policy: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure_v5_6.md ; format: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure.md .
