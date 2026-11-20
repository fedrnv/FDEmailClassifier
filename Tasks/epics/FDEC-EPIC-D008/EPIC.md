---
schema: fdtasks-epic/v4
id: FDEC-EPIC-D008
title: "CI and public distribution with FDUpdate"
initial_status: Planned
initial_dependencies: [FDEC-EPIC-D007]
created_at: 2026-11-20T10:46:00Z
created_by: "project-planning"
---

# CI and public distribution with FDUpdate

## Outcome
Package public binaries/libraries/models and publish releases to GitHub and FDUpdate with explicit safe gates.

## Accepted membership
- FDEC-050
- FDEC-051
- FDEC-052
- FDEC-053
- FDEC-054
- FDEC-055
- FDEC-056
- FDEC-057

## Delivery and dependencies
Only one development Epic active at a time; D008 follows prior Epic closure. Each task is one independently accepted outcome. Gate FDEC-056 depends on functional items; independent review FDEC-057 depends on gate and exact frozen candidate.

## Gate and review
FDTasks v5.6 source: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure_v5_6.md . Pin upstream policy hash and task readiness evidence before dispatch. Gate runs changed-area integration tests locally; independent review checks the exact passing candidate. No release or Epic closure without accepted evidence.
