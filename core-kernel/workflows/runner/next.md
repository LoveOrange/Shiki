# Runner Next

> Role: Coordinator. Start an adaptive execution session and advance the current
> plan through task execution, review gates, and a stable stop boundary.

## Load

- `core-kernel/runtime/context_loading.md`
- `core-kernel/runtime/execution_session.md`
- `.shiki/adapters/<tool>/manifest.json` when present
- `shiki_context/workspace/active_task.md`
- current scope plan:
  - Init stage: `shiki_context/workspace/_plan.md`
  - Feature stage: `shiki_context/features/{feature}/_plan.md`
  - temporary maintenance plan: `shiki_context/workspace/*_plan.md`

After selecting each item, load:

- task contract from `core-kernel/runtime/task_contracts/`
- workflow named by `workflow_ref`
- template and tech contract slices declared by the workflow
- only direct source/spec context required by the current item

## Preflight

1. Read adapter metadata. If the current adapter cannot be identified, use
   `single_agent_session`.
2. Read active task and the current plan.
3. Select the first unfinished item whose dependencies are satisfied.
4. Build a candidate execution window in plan order using `runner/batch.md`.
5. Estimate context budget from direct inputs, target files, source files,
   dependency count, and expected verification output. Use host context usage
   only when the tool exposes it.
6. Choose topology:
   - `single_agent_session` when subagents or isolated worker context are not
     available, the window has one item, the phase is Init/Requirement/Merge, or
     the work is sync/doctor/maintenance.
   - `agent_team_session` only when the manifest supports it, every claimed item
     is Design or Code, ownership is clear, and root can verify after workers
     return.
7. Before edits, state the selected topology, claimed item ids, stop boundary,
   review plan, and verification that will close the session.

## Steps

1. Execute selected items sequentially. Do not let a later item start until the
   previous item has passed review or stopped.
2. For each item, load its task contract before loading workflow text.
3. Execute the workflow through the chosen topology:
   - In `single_agent_session`, the same root context executes, reviews,
     verifies, and updates plan state.
   - In `agent_team_session`, the root coordinator assigns bounded Design/Code
     work to workers, then performs final verification, review, and plan updates.
4. Run the item review gate from `execution_session.md`.
5. Mark the item done only after task-contract checks, verification, evidence,
   and review all pass.
6. Record `status`, `output_files`, `evidence`, and `review_result` when the
   plan has those columns. For older plans, update `output_files` and preserve
   compatibility semantics.
7. After each item, re-evaluate stop conditions, context budget, phase gate, and
   whether a new ready item can be claimed.
8. Stop at the first review failure, verification failure, blocker, manual
   decision, phase gate, unsafe boundary, or context-budget boundary.

## Output

- Current plan state updated after each completed and reviewed item.
- Failed or blocked items remain unfinished or are marked with explicit
  `BLOCKED`, `MANUAL_DECISION`, or `VERIFICATION_FAILED` state.
- Final response lists topology, completed item ids, stopped item id if any,
  modified files, evidence, review result, verification, and next human action.

## Verification

- Each completed item met its task contract checks and done condition.
- Each completed item has passing review and verification evidence.
- Session-level verification covers all modified files and generated specs
  touched by the completed items.
- If review or verification fails, do not continue the session.

## Forbidden

- Do not ask the user to choose single-agent or agent-team mode.
- Do not merge plan rows or rewrite the plan to make a larger task.
- Do not skip a task contract, workflow, L2 spec, review gate, alignment check,
  or drift/test gate.
- Do not let workers select plan items, update `_plan.md`, or mark work done.
- Do not continue after failed review or verification.
- Do not load the full prompt docs, full module tree, or full source tree by
  default.
