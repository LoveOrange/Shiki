# Flow Design

> Role: Architect. Produce scenario flow design only.

## Load

- model, persistence, ACL, and component specs for the module
- `features/{feature}/design_brief.md`
- entrance spec when the scenario has an exposed entry

## Steps

1. Confirm direct design dependencies exist.
2. Fill `_flow_template.md`: approval checklist, model summary, entrance summary, activity diagram, sequence diagram, exceptions, robustness.
3. Ensure sequence participants match component inventory.
4. Mark new error codes that must be reflected in model.
5. Do not invent new components.

## Output

- `features/{feature}/modules/{module}/flows/[scenario].md`

## Verification

1. Output file exists.
2. Sequence participants match component design.
3. New ErrorCodes are traceable to model.
4. No undeclared components are introduced.
