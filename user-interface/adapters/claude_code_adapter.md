# Claude Code Adapter

## Scope

The Claude Code adapter exposes the canonical Shiki commands as project slash
commands under `.claude/commands/` and installs an optional project subagent at
`.claude/agents/shiki-phase-wave.md`.

Claude Code treats project command files as custom commands. Each generated
command includes frontmatter with a `description`; `/shiki-modify` also includes
`argument-hint: <target>` so the target argument is visible at invocation time.

This adapter follows `user-interface/adapters/tool_adapter_contract_v1.md`.
Shiki Core remains the source of truth for plan routing, task contracts,
workflow binding, context loading, evidence, and gate state.

## Installed Files

| file | purpose |
| :--- | :--- |
| `.claude/commands/shiki-init.md` | Initialize or repair the local Shiki context scaffold. |
| `.claude/commands/shiki-status.md` | Report the active plan and next runnable item without edits. |
| `.claude/commands/shiki-next.md` | Execute Shiki plan work through Core Kernel contracts. |
| `.claude/commands/shiki-modify.md` | Apply a bounded requested change to a target. |
| `.claude/commands/shiki-review.md` | Review implementation/spec alignment without edits. |
| `.claude/commands/shiki-sync.md` | Plan and apply bounded Code -> Spec sync. |
| `.claude/commands/shiki-doctor.md` | Diagnose or repair context-store structure. |
| `.claude/agents/shiki-phase-wave.md` | Optional Design/Code wave worker used only by the root session. |

The command files set `disable-model-invocation: true` because Shiki commands
should run only when the user or root session invokes the canonical command
explicitly.

## Command Happy Paths

### `/shiki-status`

The command loads the adapter contract, this adapter document,
`core-kernel/runtime/context_loading.md`,
`shiki_context/workspace/active_task.md`, and the current scope `_plan.md`.
It reports the active scope, next runnable item, gate state, blockers, missing
files, adapter capability detection, candidate execution window, likely topology,
and confirms that no edits were made.

### `/shiki-next`

The root session loads the adapter contract, this adapter document,
`core-kernel/runtime/context_loading.md`,
`core-kernel/runtime/execution_session.md`,
`core-kernel/workflows/runner/next.md`, the active task, the current plan, and
selected task contracts before any workflow text. Claude Code does not ask the
user to choose single-agent or agent-team mode. The root session auto-selects
topology from adapter metadata, plan state, direct context size, and stop
conditions.

When the root session considers `agent_team_session`, `bounded_batch`,
`phase_wave`, or `subagent_delegation`, it must also load
`core-kernel/workflows/runner/batch.md`, state the selected topology and
internal execution mode, and record the batch stop-condition check result before
edits. The root session may call `shiki-phase-wave` only after it has prepared
the complete root assignment described below. After the worker returns, the root
session runs verification and review, updates plan state only for verified and
reviewed items, and stops on `BLOCKED`, `MANUAL_DECISION`,
`VERIFICATION_FAILED`, or failed review.

### `/shiki-modify <target>`

The command requires the target argument from `$ARGUMENTS`, loads the adapter
contract, this adapter document, `core-kernel/runtime/context_loading.md`, the
active task, the current plan, and direct source/spec files related to the
target. It makes only the bounded requested change, marks downstream completed
items `STALE` only when the change affects them, and runs the smallest
meaningful verification.

## Root-Controlled Orchestration

The root Claude Code session owns:

- Reading `shiki_context/workspace/active_task.md`.
- Selecting ready plan items.
- Checking dependencies and stop conditions.
- Loading each selected task contract.
- Automatically deciding whether `/shiki-next` uses `single_agent_session` or
  `agent_team_session`.
- Updating `_plan.md` `status`, `output_files`, `evidence`, and
  `review_result`.
- Running and reporting final verification.
- Holding Merge phase control.

The `shiki-phase-wave` subagent must not select its own plan items, change plan
state, mark items done, or run Merge. It may only execute item work explicitly
assigned by the root session and return evidence.

Merge phase remains root-controlled by default.

Before using the subagent, the root session must produce a root assignment with:

- Selected topology, limited to `agent_team_session`.
- Selected internal execution mode, limited to `phase_wave` or
  `subagent_delegation`.
- Item id, stage, and target output files for each selected item.
- Task contract path and `workflow_ref` for each item.
- Dependency check result and direct context files for each item.
- Batch stop-condition check result from `core-kernel/workflows/runner/batch.md`.
- Verification command and review gate that the root session will run after the worker returns.

If any required assignment field is missing, the subagent must return `BLOCKED`
without editing files.

## Delegation Rules

Claude Code may choose `agent_team_session` and delegate a Design or Code phase
wave only when all of these are true:

- The root session has selected the candidate items from the current plan.
- The adapter manifest supports subagents or isolated worker context.
- The root session has loaded `core-kernel/workflows/runner/batch.md` and
  recorded a clean batch stop-condition check result.
- The selected topology is `agent_team_session`.
- The selected internal execution mode is `phase_wave` or
  `subagent_delegation`.
- Every item is in Design or Code.
- Every item has satisfied dependencies.
- Every item has a task contract path under `core-kernel/runtime/task_contracts/`.
- The root session can provide each item target, workflow reference, and direct context.
- The wave does not cross Merge.
- No item is `BLOCKED`, `MANUAL_DECISION`, stale without a target, missing input, or ambiguous ownership.
- The wave can stop immediately after the first failed review or verification.

When any condition is false, `/shiki-next` must run as `single_agent_session` or
return the appropriate `BLOCKED` or `MANUAL_DECISION` report.

After the worker returns, the root session verifies and reviews the changed
files, updates plan state only for verified and reviewed items, and reports any
`VERIFICATION_FAILED` or failed review state without continuing to later items.

## When Subagents Help

Use `shiki-phase-wave` when the adaptive coordinator selects
`agent_team_session`: a Design or Code phase has several ready items and the
root context is already carrying enough plan, dependency, and verification state
that detailed item execution would risk context loss.

Good uses:

- Several independent Design leaf specs for the same feature.
- Several independent Code items whose dependencies are complete.
- A large feature where the root session needs to preserve plan and gate state.

## When Subagents Are Unsafe

Do not use `shiki-phase-wave` when:

- The next item is Merge or affects baseline writes.
- Dependencies are incomplete or ambiguous.
- The target crosses unrelated modules or features.
- A user decision is needed.
- The root session cannot verify each item after the worker returns.
- The worker would need to update `_plan.md`, `status`, `output_files`,
  `evidence`, `review_result`, or gate state itself.

In unsafe cases, keep `/shiki-next` in `single_agent_session` and preserve the
normal Core Kernel stop behavior.
