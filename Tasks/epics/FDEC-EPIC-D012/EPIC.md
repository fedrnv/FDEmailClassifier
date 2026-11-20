---
schema: fdtasks-epic/v4
id: FDEC-EPIC-D012
title: "Independent benchmarking and public quality reports"
initial_status: Planned
initial_dependencies: [FDEC-EPIC-D011]
created_at: 2026-11-20T16:45:00Z
created_by: "project-planning"
---

# Independent benchmarking and public quality reports

## Outcome
Ship a reusable public benchmarking harness and versioned, reproducible quality reports using source-isolated permitted evaluation fixtures; real-world private/consented corpora may be added when legally available, without stalling benchmark tooling.

## Accepted membership
- FDEC-080
- FDEC-081
- FDEC-082
- FDEC-083
- FDEC-084
- FDEC-085
- FDEC-086

## Gate and review
Targeted gate FDEC-085 depends on all functionality items; independent review FDEC-086 depends on the passing gate. Run focused and integration acceptance tests locally. The new Epics are enhancement workstreams: **do not add them as dependencies of existing D004–D010 Epics, of D002 gate, or of any active Goal**. They do not block the baseline release merely because external email rights or a voluntary real-email benchmark are missing. Individual inadmissible sources are excluded, never mislabelled as approved. A published quality claim is limited to cohorts actually tested.

## Scheduling
FDTasks v5.6: at most one development Epic Active at once. Plan these Epics after relevant existing work or at owner-authorized scheduling point. No mandatory outside source/credential to finish the executable infrastructure tasks. Source-specific corpus inclusion may be deferred without claiming commercial rights.
