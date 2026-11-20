---
schema: fdtasks-epic/v4
id: FDEC-EPIC-D003
title: "Training and evaluation"
initial_status: Planned
initial_dependencies: [FDEC-EPIC-D002]
created_at: 2026-11-20T10:46:00Z
created_by: "project-planning"
---

# Training and evaluation

## Outcome
Reproducibly train Qwen3-0.6B classifier, measure quality, calibrate results and export local models.

## Accepted membership
- FDEC-015
- FDEC-016
- FDEC-017
- FDEC-018
- FDEC-019
- FDEC-020
- FDEC-021

## Delivery and dependencies
Only one development Epic active at a time; D003 follows prior Epic closure. Each task is one independently accepted outcome. Gate FDEC-020 depends on functional items; independent review FDEC-021 depends on gate and exact frozen candidate.

## Gate and review
FDTasks v5.6 source: https://github.com/fedrnv/FDTasks/blob/main/Tasks/tasks_file_structure_v5_6.md . Pin upstream policy hash and task readiness evidence before dispatch. Gate runs changed-area integration tests locally; independent review checks the exact passing candidate. No release or Epic closure without accepted evidence.
