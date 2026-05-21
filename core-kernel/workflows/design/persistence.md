# Persistence Design

> Role: Architect. Produce persistence design only.

## Load

- `features/{feature}/modules/{module}/designs/model.md`
- `features/{feature}/design_brief.md` capacity notes
- tech contracts: naming and persistence

## Steps

1. Confirm model design exists.
2. Read Entity and VO definitions.
3. Fill `_persistence_template.md`: PO definitions, mapping, indexes, ER diagram, DDL, capacity.
4. Use PO suffixes and module-prefixed table names.
5. Flatten VO fields into columns.
6. Do not write implementation code.

## Output

- `features/{feature}/modules/{module}/designs/persistence.md`

## Verification

1. Output file exists.
2. All tables have the module prefix.
3. PO classes have PO suffixes.
4. Capacity is not invented when brief says N/A.
