# Inspect Controller Workflow

Inspect one Controller/API group and expand the Init Plan with entrance leaf tasks.

## Steps

1. Read only the current Plan item's target and module.
2. Identify class-level routes, method entrances, triggers, and source references.
3. Add or reuse one `init/entrance_spec.yaml` row per entrance group. It depends on the current item and targets `modules/{module}/entrances/{api_group}.md`.
4. Deduplicate by Canonical Contract plus target.
5. Do not add Flow rows; Flow is an explicitly requested review artifact in V4.
6. Change only `workspace/_plan.md`; do not create entrance, flow, or module index content.
7. Use `NOOP: no entrance discovered` only with sufficient evidence. Otherwise return BLOCKED and leave the ledger empty.

## Verification

- Added rows have deterministic ids, targets, modules, and dependencies.
- Added rows use `init/entrance_spec.yaml`.
- Contract plus target is unique.
- The current item's output records the Plan only after a dependent entrance row exists.
