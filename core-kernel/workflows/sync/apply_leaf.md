# Sync Apply Leaf

> Role: Sync Executor. Execute exactly one ready item from `sync_plan.md`, then stop.

## Load

- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/sync_plan.md`
- first row whose `status` is `READY` or whose `output_files` is empty and whose contract points to `sync/apply_leaf.yaml`
- source files listed by that row
- target leaf spec listed by that row

Load additional direct specs only when needed:

- target entrance may load same-module `designs/model.md`
- target flow may load its related entrance spec
- cross-module calls may load the called module entrance and model specs

Do not load a whole module directory, whole source tree, or unrelated flow files.

## Steps

1. Select the first ready sync row; if none exists, return `BLOCKED: no sync item`.
2. Confirm `source_files` and `target` exist. If not, mark the row `BLOCKED: <reason>`.
3. Compare source to target spec only for the planned fact types: signatures, fields, states, error codes, flow branches, and dependency direction.
4. Update only the target leaf spec section directly supported by source evidence.
5. Preserve unrelated sections, historical constraints, and human notes.
6. If target mapping is not unique, source behavior is ambiguous, or product judgment is required:
   - do not edit the spec body
   - append a Manual Decision row in `sync_plan.md`
   - mark the current row `MANUAL_DECISION: <reason>`
7. On success, mark the current row `output_files` with the target spec path,
   set `status=DONE` when the column exists, and record source evidence plus
   `review_result=PASS`.
8. Stop without executing the next row.

## Verification

1. Only one sync item was processed.
2. Changed files are limited to the target leaf spec and `workspace/sync_plan.md`.
3. The diff summary maps to concrete source evidence.
4. Unchanged behavior is not rewritten.
