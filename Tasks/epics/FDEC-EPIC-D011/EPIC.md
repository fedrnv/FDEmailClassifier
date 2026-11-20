---
schema: fdtasks-epic/v4
id: FDEC-EPIC-D011
title: "Rights-safe training on available datasets"
initial_status: Planned
initial_dependencies: [FDEC-EPIC-D003]
created_at: 2026-11-20T16:45:00Z
created_by: "project-planning"
---

# Rights-safe training on available datasets

## Outcome
Build and document repeatable model training on admitted open datasets, with per-source license gating and automatic exclusion of unresolved optional sources without blocking the entire product.

## Accepted membership
- FDEC-074
- FDEC-075
- FDEC-076
- FDEC-077
- FDEC-078
- FDEC-079

## Gate and review
Targeted gate FDEC-078 depends on all functionality items; independent review FDEC-079 depends on the passing gate. Run focused and integration acceptance tests locally. The new Epics are enhancement workstreams: **do not add them as dependencies of existing D004–D010 Epics, of D002 gate, or of any active Goal**. They do not block the baseline release merely because external email rights or a voluntary real-email benchmark are missing. Individual inadmissible sources are excluded, never mislabelled as approved. A published quality claim is limited to cohorts actually tested.

## Scheduling
FDTasks v5.6: at most one development Epic Active at once. Plan these Epics after relevant existing work or at owner-authorized scheduling point. No mandatory outside source/credential to finish the executable infrastructure tasks. Source-specific corpus inclusion may be deferred without claiming commercial rights.
