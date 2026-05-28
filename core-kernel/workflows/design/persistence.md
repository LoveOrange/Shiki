# Persistence Design

> Role: Architect. Produce persistence design only.

## Load

- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/design_brief.md` capacity notes
- baseline `modules/{module}/designs/persistence.md` when present and read-only
- tech contracts: naming and persistence

## Steps

1. Confirm model design exists.
2. Read Entity and VO definitions.
3. Fill `_persistence_template.md`: Baseline Delta, PO definitions, mapping, indexes, ER diagram, DDL, capacity.
4. For feature overlays, compare baseline persistence when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
5. Use PO suffixes and module-prefixed table names.
6. Flatten VO fields into columns.
7. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/persistence.md`

## Verification

1. Output file exists.
2. All tables have the module prefix.
3. PO classes have PO suffixes.
4. Capacity is not invented when brief says N/A.
5. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
