---
schema: fdtasks-epic/v4
id: FDEC-EPIC-D004
title: "Rust inference library"
initial_status: Planned
initial_dependencies: [FDEC-EPIC-D003]
created_at: 2026-11-20T10:46:00Z
created_by: "project-planning"
---

# Rust inference library

## Outcome
Ship local reusable Rust inference and classification engine independent of FDFiles or a daemon.

## Accepted membership
- FDEC-022
- FDEC-023
- FDEC-024
- FDEC-025
- FDEC-026
- FDEC-027
- FDEC-028

## Delivery and dependencies
Only one development Epic active at a time; D004 follows prior Epic closure. Each task is one independently accepted outcome. Gate FDEC-027 depends on functional items; independent review FDEC-028 depends on gate and exact frozen candidate.

## Gate and review
FDTasks v5.6 source: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure_v5_6.md . Pin upstream policy hash and task readiness evidence before dispatch. Gate runs changed-area integration tests locally; independent review checks the exact passing candidate. No release or Epic closure without accepted evidence.
