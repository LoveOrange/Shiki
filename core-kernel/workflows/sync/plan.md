# Sync Plan

> Role: Sync Planner. Create a bounded Code-to-Spec Plan without editing spec bodies.

## Steps

1. Bound scope by user-named source files, module plus diff, or an explicit inconsistency. Return `BLOCKED: sync scope too broad` when candidates remain broad.
2. Collect lightweight signatures, fields, states, errors, and dependency evidence.
3. Map each candidate to one leaf spec using indexes and deterministic symbol/path searches.
4. Put ambiguous mappings in Manual Decision.
5. Create or update `shiki_context/workspace/sync_plan.md` with columns:
   `id | phase | target | source_files | depends_on | contract | output_files`.
6. Every executable row targets one leaf, uses `sync/apply_leaf.yaml`, and starts with empty `output_files`.
7. Stop without applying a row.

## Verification

- No feature/module spec body or source file changed.
- Contract plus target rows are unique.
- Ambiguity is not written as current-valid fact.
