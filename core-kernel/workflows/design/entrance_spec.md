# Entrance Spec Design

> Role: Architect. Produce exposed entrance contract only.

## Load

- `features/{feature}/design_brief.md` entrance section
- `features/{feature}/modules/{module}/designs/model.md`
- baseline `modules/{module}/entrances/[entrance].md` when present and read-only

## Steps

1. Confirm model design exists.
2. Confirm the brief declares a new or changed exposed entrance; otherwise skip with N/A.
3. Fill `_entrance_spec_template.md`: Baseline Delta, summary, access, request, response, errors, examples.
4. For feature overlays, compare baseline entrance when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
5. Use only known methods: GET, POST, PUT, DELETE, TCP, Scheduled Task.
6. Mark unknown endpoints as TBD instead of inventing domains.

## Output

- `features/{feature}/modules/{module}/entrances/[entrance].md`

## Verification

1. Output file exists when entrance is required.
2. Only entrance contract is described.
3. No invented external domain is present.
4. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
5. No implementation code is present.
