# Model Design

> Role: Architect. Produce domain model design only. Return BLOCKED when required inputs are missing.

## Load

- `shiki_context/features/{feature}/design_brief.md`
- `shiki_context/project/ubiquitous_language.md`
- existing feature or baseline model when iterating
- tech contract: naming

## Steps

1. Confirm `design_brief.md` exists.
2. Extract entities, value objects, states, invariants, and errors from the brief.
3. Fill `_model_template.md` sections: language, entities, VOs, transitions, ER diagram, error codes.
4. Keep Support signatures free of DTOs.
5. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/model.md`

## Verification

1. Output file exists.
2. Sections 1-6 are non-empty or explicitly N/A.
3. Names come from the brief or existing specs.
4. No implementation code is present.
