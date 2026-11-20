---
schema: fdtasks-epic/v4
id: FDEC-EPIC-D006
title: "Optional service and deployment"
initial_status: Planned
initial_dependencies: [FDEC-EPIC-D005]
created_at: 2026-11-20T10:46:00Z
created_by: "project-planning"
---

# Optional service and deployment

## Outcome
Offer secure HTTP server and offline Docker deploy without making it mandatory for SDK consumers.

## Accepted membership
- FDEC-036
- FDEC-037
- FDEC-038
- FDEC-039
- FDEC-040
- FDEC-041
- FDEC-042

## Delivery and dependencies
Only one development Epic active at a time; D006 follows prior Epic closure. Each task is one independently accepted outcome. Gate FDEC-041 depends on functional items; independent review FDEC-042 depends on gate and exact frozen candidate.

## Gate and review
FDTasks v5.6 source: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure_v5_6.md . Pin upstream policy hash and task readiness evidence before dispatch. Gate runs changed-area integration tests locally; independent review checks the exact passing candidate. No release or Epic closure without accepted evidence.
