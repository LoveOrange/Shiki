# Persistence Design

> Role: Architect. Produce persistence design only.

## Load

- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/design_brief.md` capacity notes
- baseline `modules/{module}/designs/persistence.md` when present and read-only
- `core-kernel/runtime/design_contract.md`
- tech contracts: naming and persistence

## Steps

1. Confirm model design exists.
2. Read Entity and VO definitions.
3. Run the Design Contract Reuse Gate for persistence scope: list checked baseline/source tables, mappings, indexes, and persistence rules.
4. Fill `_persistence_template.md`: Baseline Delta, Reuse Decision Gate, PO definitions, mapping, indexes, database ER diagram, DDL, capacity.
5. For feature overlays, compare baseline persistence when present and mark `reuse/add/extend/modify/deprecate` in `§0 Baseline Delta`.
6. Use PO suffixes and module-prefixed table names.
7. Flatten VO fields into columns.
8. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/persistence.md`

## Verification

1. Output file exists.
2. All tables have the module prefix.
3. PO classes have PO suffixes.
4. Capacity is not invented when brief says N/A.
5. Baseline Delta explains changes relative to baseline, or returns `MANUAL_DECISION` when uncertain.
6. Reuse Decision Gate records checked candidates and add justification.
