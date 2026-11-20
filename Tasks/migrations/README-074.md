# Identity migration FDEC-074

Merged website FDEC-073 conflicts with the existing Done adoption Correction.
FDEC-075 replaces only the path-qualified Planned website task, with unchanged
outcome, dependency, parent and AC matrix. Both original specifications remain
immutable. FDEC-074.json binds their exact bytes, replacement and supersession
event. The retired path remains historical input and is excluded only from the
executable identity projection. Any incomplete or altered mapping fails closed.

New D009 membership-replaced and FDEC-063 dependency-replaced events re-link the
website prerequisite to FDEC-075. They require the matching parent-bound migration;
other references to completed adoption FDEC-073 remain intact. Admission resolves
from the same validated projection, not a second independent filesystem scan.
Current readiness must bind each migration manifest and its four source/evidence
paths in `migration_revisions`; otherwise all admission actions fail closed.

This implements existing FDTasks 5.6 replacement-first migration semantics;
upstream 5.6, original task/Epic/rule/adoption bytes and closure requests remain
unchanged. No new normative policy version is introduced. Reject future duplicate
IDs before publication; do not infer another migration from a duplicate name.
Only this bounded Planned-record recovery shape is supported. Already executed
collisions require a separately reviewed correction rather than silent reuse.
