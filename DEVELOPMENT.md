# Development contract

Rust is the production implementation language. Python is limited to training and Python bindings. Use versioned contracts and stable C ABI. Run diff-focused local tests before committing changes; separate targeted local integration gates and independent review per development Epic. Confirm exact commands per task as implementation paths become available. No tests in hosted workflows; only explicitly dispatched build/package/publish/cleanup. Keep artifact retention cleanup manual and older than ten days. All release/model publishing requires license and integrity checks and explicit operator authorization. Never log raw emails; fail closed on uncertain security or licensing.

Canonical policy: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure_v5_6.md ; format: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure.md .
