# Flow Design

> Role: Architect. Produce scenario flow design only.

## Load

- model, persistence, ACL, and component specs for the module
- `features/{feature}/design_brief.md`
- entrance spec when the scenario has an exposed entry
- baseline `modules/{module}/flows/[scenario].md` when present and read-only
- `core-kernel/runtime/design_contract.md`

## Steps

1. Confirm direct design dependencies exist.
2. Run the Design Contract Reuse Gate for scenario scope: list checked baseline/source flows, participants, branches, error paths, and robustness rules.
3. Fill `_flow_template.md`: Baseline Delta, Reuse Decision Gate, approval checklist, model summary, entrance summary, activity diagram, sequence diagram, exceptions, robustness.
4. For feature overlays, compare baseline flow when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
5. Ensure sequence participants match component inventory.
6. Mark new error codes that must be reflected in model.
7. Do not invent new components.

## Output

- `features/{feature}/modules/{module}/flows/[scenario].md`

## Verification

1. Output file exists.
2. Sequence participants match component design.
3. New ErrorCodes are traceable to model.
4. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
5. Reuse Decision Gate records checked candidates and add justification.
6. No undeclared components are introduced.
