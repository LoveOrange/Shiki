# Flow Design

> Role: Architect. Produce scenario flow design only.

## Load

- model, persistence, ACL, and component specs for the module
- `features/{feature}/design_brief.md`
- entrance spec when the scenario has an exposed entry
- baseline `modules/{module}/flows/[scenario].md` when present and read-only

## Steps

1. Confirm direct design dependencies exist.
2. Fill `_flow_template.md`: Baseline Delta, approval checklist, model summary, entrance summary, activity diagram, sequence diagram, exceptions, robustness.
3. For feature overlays, compare baseline flow when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
4. Ensure sequence participants match component inventory.
5. Mark new error codes that must be reflected in model.
6. Do not invent new components.

## Output

- `features/{feature}/modules/{module}/flows/[scenario].md`

## Verification

1. Output file exists.
2. Sequence participants match component design.
3. New ErrorCodes are traceable to model.
4. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
5. No undeclared components are introduced.
