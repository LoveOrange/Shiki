# Claude Code Adapter

## Scope

The Claude Code adapter exposes the canonical Shiki commands as project slash
commands under `.claude/commands/` and installs an optional project subagent at
`.claude/agents/shiki-phase-wave.md`.

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

## Root-Controlled Orchestration

The root Claude Code session owns:

- Reading `shiki_context/workspace/active_task.md`.
- Selecting ready plan items.
- Checking dependencies and stop conditions.
- Loading each selected task contract.
- Deciding whether `/shiki-next` stays `single_item` or delegates a bounded wave.
- Updating `_plan.md` `output_files`.
- Running and reporting final verification.
- Holding Merge phase control.

The `shiki-phase-wave` subagent must not select its own plan items, change plan
state, mark items done, or run Merge. It may only execute item work explicitly
assigned by the root session and return evidence.

Merge phase remains root-controlled by default.

## Delegation Rules

Claude Code may delegate a Design or Code phase wave only when all of these are
true:

- The root session has selected the candidate items from the current plan.
- Every item is in Design or Code.
- Every item has satisfied dependencies.
- Every item has a task contract path under `core-kernel/runtime/task_contracts/`.
- The root session can provide each item target, workflow reference, and direct context.
- The wave does not cross Merge.
- No item is `BLOCKED`, `MANUAL_DECISION`, stale without a target, missing input, or ambiguous ownership.
- The wave can stop immediately after the first failed verification.

When any condition is false, `/shiki-next` must run as `single_item` or return
the appropriate `BLOCKED` or `MANUAL_DECISION` report.

## When Subagents Help

Use `shiki-phase-wave` when context limits matter: a Design or Code phase has
several independent ready items and the root context is already carrying enough
plan, dependency, and verification state that detailed item execution would risk
context loss.

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
- The worker would need to update `_plan.md`, `output_files`, or gate state itself.

In unsafe cases, keep `/shiki-next` in `single_item` mode and preserve the normal
Core Kernel stop behavior.
