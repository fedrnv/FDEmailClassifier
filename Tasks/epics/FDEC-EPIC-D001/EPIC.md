---
schema: fdtasks-epic/v4
id: FDEC-EPIC-D001
title: "Foundation and open-source governance"
initial_status: Planned
initial_dependencies: []
created_at: 2026-11-20T10:46:00Z
created_by: "project-planning"
---

# Foundation and open-source governance

## Outcome
Deliver reproducible public Rust workspace, stable classification contract, project rules and licensing.

## Accepted membership
- FDEC-001
- FDEC-002
- FDEC-003
- FDEC-004
- FDEC-005
- FDEC-006
- FDEC-007

## Delivery and dependencies
Only one development Epic active at a time; D001 follows prior Epic closure. Each task is one independently accepted outcome. Gate FDEC-006 depends on functional items; independent review FDEC-007 depends on gate and exact frozen candidate.

## Gate and review
FDTasks v5.6 source: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure_v5_6.md . Pin upstream policy hash and task readiness evidence before dispatch. Gate runs changed-area integration tests locally; independent review checks the exact passing candidate. No release or Epic closure without accepted evidence.
