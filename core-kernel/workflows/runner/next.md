# Runner Next

> Role: Runner. Select the next executable plan item and route it to the workflow executor.

## Load

- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/active_task.md`
- current scope plan:
  - Init stage: `shiki_context/workspace/_plan.md`
  - Feature stage: `shiki_context/features/{feature}/_plan.md`
  - temporary maintenance plan: `shiki_context/workspace/*_plan.md`

After selecting the item, load:

- task contract from `core-kernel/runtime/task_contracts/`
- workflow named by `workflow_ref`
- template and tech contract slices declared by the workflow

## Steps

1. Read active task and current plan.
2. Check each item in plan order for satisfied `depends_on` and unfinished `output_files`.
3. Treat empty `output_files` and `STALE: ...` as unfinished.
4. In Feature stage, resolve item `target` relative to the feature root. If target points at `shiki_context/modules/**` baseline, return `BLOCKED`.
5. Load the item task contract and its `workflow_ref`.
6. Hand execution to the workflow executor.
7. After completion, update the current plan `output_files`.
8. Stop without advancing another item.

## Forbidden

- Do not execute multiple items in one `next` run; use `runner/batch.md` when an explicit batch is requested.
- Do not skip L2 specs, alignment checks, or drift/test gates.
- Do not make the runner perform workflow execution itself.
- Do not load the full prompt docs, full module tree, or full source tree by default.
