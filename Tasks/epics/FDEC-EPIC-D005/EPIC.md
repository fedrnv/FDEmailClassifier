---
schema: fdtasks-epic/v4
id: FDEC-EPIC-D005
title: "Language SDKs and ABI"
initial_status: Planned
initial_dependencies: [FDEC-EPIC-D004]
created_at: 2026-11-20T10:46:00Z
created_by: "project-planning"
---

# Language SDKs and ABI

## Outcome
Provide feature-equivalent Rust, C, C++ and Python in-process APIs with stable ownership/error semantics.

## Accepted membership
- FDEC-029
- FDEC-030
- FDEC-031
- FDEC-032
- FDEC-033
- FDEC-034
- FDEC-035

## Delivery and dependencies
Only one development Epic active at a time; D005 follows prior Epic closure. Each task is one independently accepted outcome. Gate FDEC-034 depends on functional items; independent review FDEC-035 depends on gate and exact frozen candidate.

## Gate and review
FDTasks v5.6 source: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure_v5_6.md . Pin upstream policy hash and task readiness evidence before dispatch. Gate runs changed-area integration tests locally; independent review checks the exact passing candidate. No release or Epic closure without accepted evidence.
