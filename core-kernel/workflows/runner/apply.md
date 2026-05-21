# Runner Apply

> Role: Runner. Select the next executable plan item and route it to the workflow executor.

## Load

- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/active_task.md`
- current scope `_plan.md`
- selected task contract after item selection

## Steps

1. Read active task and current plan.
2. Find the first item whose depends_on values are satisfied and output_files are empty.
3. Load the item task contract from `core-kernel/runtime/task_contracts/`.
4. Load workflow_ref, required template, and tech contract slices.
5. Hand execution to the workflow executor.
6. After completion, update output_files.
7. Stop without advancing another item.

## Forbidden

- Do not execute multiple items in one run.
- Do not skip `code_contract.md` or other gate artifacts.
- Do not make the runner perform workflow execution itself.
- Do not load the full CHEATSHEET, full module tree, or full source tree by default.
