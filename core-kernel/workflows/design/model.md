# Model Design

> Role: Architect. Produce domain model design only. Return BLOCKED when required inputs are missing.

## Load

- `shiki_context/features/{feature}/design_brief.md`
- `shiki_context/project/ubiquitous_language.md`
- existing feature or baseline model when iterating
- `core-kernel/runtime/design_contract.md`
- tech contract: naming

## Steps

1. Confirm `design_brief.md` exists.
2. Run the Design Contract Reuse Gate for model scope: list checked baseline/source entities, VOs, enums, error codes, and state machines.
3. Extract entities, value objects, states, invariants, relationships, and errors from the brief.
4. Fill `_model_template.md` sections: Baseline Delta, Reuse Decision Gate, language, entities, VOs, transitions, domain relationship diagram, error codes.
5. For feature overlays, compare baseline model when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
6. Use `classDiagram` for domain relationships; do not use database `erDiagram`, table fields, PK/FK, indexes, or DDL in model specs.
7. Keep Support signatures free of DTOs.
8. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/model.md`

## Verification

1. Output file exists.
2. Sections 1-6 are non-empty or explicitly N/A.
3. Names come from the brief or existing specs.
4. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
5. Reuse Decision Gate records checked candidates and add justification.
6. Section 5 is a domain relationship `classDiagram`, not a database ER diagram.
7. No implementation code is present.
