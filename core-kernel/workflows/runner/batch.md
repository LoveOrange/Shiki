# Runner Batch

> Role: Runner. Select and route a bounded sequence of safe plan items for a capable coding agent.

## Load

- `core-kernel/runtime/context_loading.md`
- `shiki_context/workspace/active_task.md`
- current scope plan:
  - Feature stage: `shiki_context/features/{feature}/_plan.md`
  - Init stage: `shiki_context/workspace/_plan.md` only when the command explicitly says batch scan

After selecting each item, load:

- task contract from `core-kernel/runtime/task_contracts/`
- workflow named by `workflow_ref`
- template and tech contract slices declared by that workflow

## Selection Policy

1. Start from L0: active task and the current plan.
2. Identify the first unfinished item whose dependencies are satisfied.
3. Build an ordered batch by plan order. Later items may depend on earlier items in the same batch.
4. Keep the batch in one scope and one feature. Prefer one phase; crossing from Design to Code requires all selected Design checks to pass first.
5. Keep the batch small enough that the agent can load each direct dependency and verification output without loading the full module tree.
6. Before editing, state the claimed item ids, why they are safe to batch, and the verification that will close the batch.

## Steps

1. Read active task and current plan.
2. Select the bounded batch using the selection policy.
3. For each selected item, load its task contract and `workflow_ref`.
4. Execute items sequentially. Do not let a later item start until the prior item has updated its declared outputs.
5. Update the current plan `output_files` after each completed item.
6. Run the smallest meaningful verification that covers the whole batch.
7. Stop and report completed item ids, blocked item id if any, modified files, and verification.

## Output

- Current plan `output_files` updated after each completed item.
- Any stopped item is left unfinished or marked with the explicit blocker when the workflow contract requires it.
- Final response lists completed item ids, blocked item id if any, modified files, and verification.

## Verification

- Each selected item met its own task contract checks and done_condition.
- Batch-level verification covers all modified files and generated specs touched by the selected items.
- If verification fails, do not continue the batch.

## Stop Conditions

Stop before claiming or executing an item when any condition applies:

- `MANUAL_DECISION`, `BLOCKED`, or missing required input appears.
- The item is Merge phase or writes to baseline paths.
- The target owner, module boundary, or feature scope is ambiguous.
- The item requires destructive operations, external credentials, or user approval.
- Required checks for the previous item fail.
- Continuing would require loading the full prompt docs, full module tree, or full source tree by default.

## Forbidden

- Do not merge plan rows or rewrite the plan to make a larger task.
- Do not skip a task contract, workflow, L2 spec, alignment check, or drift/test gate.
- Do not treat the agent's confidence as permission to cross stop conditions.
- Do not continue after a failed verification; mark the next affected item `BLOCKED` or leave it unfinished.
