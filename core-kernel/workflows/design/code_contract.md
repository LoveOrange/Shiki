# Generate Code Contract

> Role: Architect. Extract implementation facts from accepted design artifacts.

## Load

- module model design
- module persistence design
- module ACL design
- module component design
- module entrances and flows when present

## Steps

1. Confirm all required design artifacts exist.
2. Extract facts into `code_contract.md`: Entities, DTOs, Interfaces, State Transitions, Error Codes, Non-functional Rules.
3. Add `[ ]` confirmation markers for each implementable fact.
4. Set `Contract Version: v1` unless a version is already required by the plan.
5. Do not add implementation detail not present in design specs.

## Output

- `features/{feature}/code_contract.md`

## Verification

1. Sections 1-6 are present.
2. Names match upstream design artifacts.
3. Confirmation cells start unchecked.
4. Contract Version is set.
