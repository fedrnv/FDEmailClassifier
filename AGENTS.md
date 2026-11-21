# FDEmailClassifier agent rules

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

Follow the [FDTasks v5.6 normative lifecycle](https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure_v5_6.md), this repository's DEVELOPMENT.md, and each immutable Tasks/items/<area>/<ID>/TASK.md. New Epics D001+, process S001, isolated maintenance S002. Only one development Epic active at a time. Every Task has a narrowly bounded single outcome and local AC-to-test matrix. All hosted Actions are workflow_dispatch only and may build/package/publish but never run acceptance or integration tests. No model/dataset redistribution without a documented license audit. Public code/documentation in English. No credentials, email bodies, secrets or private training data in git. Do not alter accepted tasks; append events.
