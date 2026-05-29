# OpenCode Adapter

## Scope

The OpenCode adapter installs project-local command files under
`.opencode/commands/` and project agent roles under `.opencode/agents/`.

This adapter follows `user-interface/adapters/tool_adapter_contract_v1.md`.
OpenCode command and agent files must call Shiki Core runtime docs, task
contracts, workflows, and gate rules instead of duplicating Core Kernel logic.

OpenCode discovers project commands from `.opencode/commands/`. The markdown
file name becomes the slash command name, so
`.opencode/commands/shiki-status.md` exposes `/shiki-status`. Command
frontmatter sets `description`, `agent`, and `subtask`; command bodies use
`$ARGUMENTS` for trailing user input.

OpenCode discovers project agents from `.opencode/agents/`. The markdown file
name becomes the agent name. Generated Shiki agents use OpenCode `permission`
frontmatter, not deprecated `tools` frontmatter, so reviewer and worker roles
can deny unsafe writes or task delegation.

OpenCode reads project `AGENTS.md` instructions. The adapter must respect those
rules before running Shiki commands, while keeping Shiki Core as the authority
for plan routing, task contracts, workflow binding, output files, and
verification.

## Installed Commands

| command | installed file | agent | subtask |
| :--- | :--- | :--- | :--- |
| `/shiki-init` | `.opencode/commands/shiki-init.md` | `shiki-runner` | `false` |
| `/shiki-status` | `.opencode/commands/shiki-status.md` | `shiki-runner` | `false` |
| `/shiki-next` | `.opencode/commands/shiki-next.md` | `shiki-runner` | `false` |
| `/shiki-modify <target>` | `.opencode/commands/shiki-modify.md` | `shiki-runner` | `false` |
| `/shiki-review` | `.opencode/commands/shiki-review.md` | `shiki-reviewer` | `true` |
| `/shiki-sync` | `.opencode/commands/shiki-sync.md` | `shiki-runner` | `false` |
| `/shiki-doctor` | `.opencode/commands/shiki-doctor.md` | `shiki-runner` | `false` |

OpenCode command files must not use `!` shell interpolation to preload Shiki
state. They should instruct the selected agent to read the required files and
run verification only when the loaded task contract or user request requires it.

## Native Activation

After install, OpenCode exposes the generated files as slash commands in the
current project:

- `/shiki-status` from `.opencode/commands/shiki-status.md`
- `/shiki-next` from `.opencode/commands/shiki-next.md`
- `/shiki-modify <target>` from `.opencode/commands/shiki-modify.md`

The generated markdown prompt is the native command body. It loads this adapter
document, the shared adapter contract, and the relevant Core Kernel runtime
files before selecting work. Command prompts must remain thin and must not
replace task contracts, runner workflows, verification expectations, or
stop-state reporting.

## Argument Forwarding

`/shiki-modify <target>` must include OpenCode's `$ARGUMENTS` placeholder.
OpenCode replaces `$ARGUMENTS` with the raw text typed after the command name,
so the adapter can pass the target and requested change through to Shiki's
modify strategy.

The generated prompt must treat `$ARGUMENTS` as untrusted user input, then:

- Load `core-kernel/runtime/context_loading.md`.
- Read `shiki_context/workspace/active_task.md`.
- Read the current scope `_plan.md`.
- Load direct specs and source files related to the target.
- Return `BLOCKED` when `$ARGUMENTS` is empty, missing a target, or ambiguous.
- Mark downstream completed items `STALE` only when the change affects them.
- Run the smallest meaningful verification.

## Command Happy Paths

### `/shiki-status`

OpenCode runs the command with `shiki-runner`. The runner loads the adapter
contract, this adapter document, `core-kernel/runtime/context_loading.md`,
`shiki_context/workspace/active_task.md`, and the current scope `_plan.md`.
It reports active scope, next runnable item, gate state, blockers, missing
files, and confirms that no edits were made.

### `/shiki-next`

OpenCode runs the command with `shiki-runner`. The runner loads the adapter
contract, this adapter document, `core-kernel/runtime/context_loading.md`,
`core-kernel/workflows/runner/next.md`, the active task, the current plan, and
the selected task contract before loading the contract `workflow_ref`.
It states the selected internal execution mode before edits, defaults to
`single_item`, updates `output_files` only after verification passes, and stops
on the adapter contract stop conditions.

### `/shiki-modify <target>`

OpenCode treats `$ARGUMENTS` as the required target and requested change text.
It loads the adapter contract, this adapter document,
`core-kernel/runtime/context_loading.md`, the active task, the current plan, and
direct source/spec files related to the target. It returns `BLOCKED` when the
target is missing or ambiguous, edits only the requested bounded target, marks
downstream completed items `STALE` only when affected, and runs the smallest
meaningful verification.

## Installed Agents

| agent | mode | permission profile | responsibility |
| :--- | :--- | :--- | :--- |
| `shiki-runner` | `primary` | Read/search allowed, edits and bash ask, task delegation limited to Shiki agents. | Root Shiki orchestration, plan selection, dependency order, output_files updates, and verification. |
| `shiki-reviewer` | `subagent` | Read/search allowed, edits denied, task delegation denied. | Read-only review of code/spec alignment and test gaps. |
| `shiki-phase-wave` | `subagent`, `hidden: true` | Read/search allowed, edits and bash ask, task delegation denied. | Optional Design/Code wave execution for explicitly assigned items only. |

## Root-Controlled State

The `shiki-runner` role owns plan state and verification. It may call the hidden
`shiki-phase-wave` subagent only after it has selected a bounded Design or Code
wave, checked dependencies, loaded task contracts, and confirmed all batch stop
conditions are clear.

Subagents must not update `_plan.md`, `output_files`, `active_task.md`,
`sync_plan.md`, `doctor_plan.md`, or Merge state. They return changed files,
verification evidence, and any `BLOCKED`, `MANUAL_DECISION`, or
`VERIFICATION_FAILED` result to `shiki-runner`.

Before using `shiki-phase-wave`, `shiki-runner` must provide a root assignment
with:

- Selected internal execution mode, limited to `phase_wave` or
  `subagent_delegation`.
- Item id, stage, and target output files for each selected item.
- Task contract path and `workflow_ref` for each item.
- Dependency check result and direct context files for each item.
- Batch stop-condition check result from `core-kernel/workflows/runner/batch.md`.
- Verification command or check that `shiki-runner` will run after the worker returns.

If any required assignment field is missing, `shiki-phase-wave` must return
`BLOCKED` without editing files.

## `/shiki-next` Mapping

OpenCode runs `/shiki-next` as `single_item` by default. It may use
`bounded_batch`, `phase_wave`, or `subagent_delegation` only when
`core-kernel/workflows/runner/batch.md` allows every claimed item and all stop
conditions are clear. Each item still loads its own task contract and updates
its own `output_files` only after root verification passes. Merge remains
root-controlled by default.

When those conditions are not satisfied, `/shiki-next` must stay in
`single_item` mode or return the adapter contract's `BLOCKED`,
`MANUAL_DECISION`, or `VERIFICATION_FAILED` report.

## Install Behavior

The installer writes only project-local `.opencode/commands/*.md`,
`.opencode/agents/*.md`, and `.shiki/adapters/opencode/manifest.json` files.
Re-running the installer updates Shiki-managed files, skips matching files, and
blocks existing user-owned command or agent files instead of overwriting them.

## Verification

Regression checks should install the OpenCode adapter into a sample project and
verify:

- `.opencode/commands/shiki-status.md`, `.opencode/commands/shiki-next.md`, and
  `.opencode/commands/shiki-modify.md` exist.
- `.opencode/agents/shiki-runner.md`, `.opencode/agents/shiki-reviewer.md`, and
  `.opencode/agents/shiki-phase-wave.md` exist.
- Generated command files reference this adapter document, the adapter contract,
  `core-kernel/runtime/context_loading.md`, and relevant Core Kernel workflows
  or task contract paths.
- `/shiki-modify <target>` generated content forwards `$ARGUMENTS` and blocks
  missing or ambiguous targets.
- Generated agent files use `permission` frontmatter, deny reviewer writes,
  hide `shiki-phase-wave`, and prevent subagents from changing plan state or
  Merge state.
- The OpenCode manifest records `opencode`, project-local install support,
  slash commands, skills, subagents, and the Phase 1 execution modes.
