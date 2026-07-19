# Sync Apply Leaf

> Role: Sync Executor. Execute exactly one ready row from `sync_plan.md`.

## Steps

1. Select the first ready row or return BLOCKED.
2. Require the row's source files and target.
3. Compare only planned signatures, fields, states, errors, branches, and dependency direction.
4. Update only the target section supported by source evidence.
5. Preserve unrelated content and human notes.
6. If mapping is not unique or product judgment is required, do not edit the spec; add a Manual Decision entry and return MANUAL_DECISION.
7. On success, record the target path in `output_files`.
8. Stop before the next row.

## Verification

- One sync row was processed.
- Changes are limited to the target leaf and `workspace/sync_plan.md`.
- The diff maps to concrete source evidence.
