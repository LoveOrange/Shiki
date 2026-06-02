# Runner Batch

> Role: Coordinator helper. Select a bounded execution window for an adaptive
> execution session.

## Load

- `core-kernel/runtime/context_loading.md`
- `core-kernel/runtime/execution_session.md`
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
3. Build an ordered execution window by plan order. Later items may depend on earlier items in the same window.
4. Keep the window in one scope and one feature. Prefer one phase; crossing from Design to Code requires all selected Design checks to pass first.
5. Keep the window small enough that the coordinator and any worker can load
   direct dependencies, review evidence, and verification output without loading
   the full module tree.
6. Prefer `single_agent_session` for one item, Init/Requirement/Merge, sync,
   doctor, unclear ownership, or small direct context.
7. Prefer `agent_team_session` only for bounded Design or Code windows when the
   adapter manifest supports subagents or isolated worker context.
8. Before editing, state the claimed item ids, selected topology, why the window
   is safe, and the verification/review gates that will close the session.

## Steps

1. Read active task and current plan.
2. Select the bounded execution window using the selection policy.
3. For each selected item, load its task contract and `workflow_ref`.
4. Execute items sequentially. Do not let a later item start until the prior item has passed review and updated plan state.
5. Run the item review gate before marking the item done.
6. Update current plan `status`, `output_files`, `evidence`, and
   `review_result` after each completed item when those columns exist.
7. Run the smallest meaningful verification that covers the whole window.
8. Stop and report completed item ids, blocked item id if any, modified files,
   review results, evidence, and verification.

## Output

- Current plan state updated after each completed and reviewed item.
- Any stopped item is left unfinished or marked with the explicit blocker when the workflow contract requires it.
- Final response lists completed item ids, blocked item id if any, modified files, review results, evidence, and verification.

## Verification

- Each selected item met its own task contract checks, done_condition, and review gate.
- Window-level verification covers all modified files and generated specs touched by the selected items.
- If review or verification fails, do not continue the window.

## Stop Conditions

Stop before claiming or executing an item when any condition applies:

- `MANUAL_DECISION`, `BLOCKED`, or missing required input appears.
- The item is Merge phase or writes to baseline paths.
- The target owner, module boundary, or feature scope is ambiguous.
- The item requires destructive operations, external credentials, or user approval.
- Required checks for the previous item fail.
- Review for the previous item fails.
- Continuing would require loading the full prompt docs, full module tree, or full source tree by default.
- Context budget would not leave room for direct dependencies, review evidence,
  and verification output.
- A phase gate is reached and ready for human review.

## Forbidden

- Do not merge plan rows or rewrite the plan to make a larger task.
- Do not skip a task contract, workflow, L2 spec, alignment check, or drift/test gate.
- Do not treat the agent's confidence as permission to cross stop conditions.
- Do not continue after a failed verification; mark the next affected item `BLOCKED` or leave it unfinished.
