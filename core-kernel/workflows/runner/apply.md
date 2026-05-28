# Runner Apply

> Role: Runner. Compatibility entry with the same current execution semantics as `next`.

## Load

- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/active_task.md`
- current scope plan:
  - Init stage: `shiki_context/workspace/_plan.md`
  - Feature stage: `shiki_context/features/{feature}/_plan.md`
  - temporary maintenance plan: `shiki_context/workspace/*_plan.md`
- selected task contract after item selection

## Steps

1. Read active task and current plan.
2. Find the first item whose depends_on values are satisfied and output_files are empty or start with `STALE`.
3. Load the item task contract from `core-kernel/runtime/task_contracts/`.
4. Load workflow_ref, required template, and tech contract slices.
5. Hand execution to the workflow executor.
6. After completion, update output_files.
7. Stop without advancing another item.

## Forbidden

- Do not execute multiple items in one run.
- Do not skip L2 specs, alignment checks, or drift/test gates.
- Do not make the runner perform workflow execution itself.
- Do not load the full prompt docs, full module tree, or full source tree by default.
