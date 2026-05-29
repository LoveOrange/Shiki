# OpenCode Adapter

## Scope

The OpenCode adapter installs project-local command files under
`.opencode/commands/` and project agent roles under `.opencode/agents/`.

This adapter follows `user-interface/adapters/tool_adapter_contract_v1.md`.
OpenCode command and agent files must call Shiki Core runtime docs, task
contracts, workflows, and gate rules instead of duplicating Core Kernel logic.

## Installed Commands

| command | installed file | default role |
| :--- | :--- | :--- |
| `/shiki-init` | `.opencode/commands/shiki-init.md` | `shiki-runner` |
| `/shiki-status` | `.opencode/commands/shiki-status.md` | `shiki-runner` |
| `/shiki-next` | `.opencode/commands/shiki-next.md` | `shiki-runner` |
| `/shiki-modify <target>` | `.opencode/commands/shiki-modify.md` | `shiki-runner` |
| `/shiki-review` | `.opencode/commands/shiki-review.md` | `shiki-reviewer` |
| `/shiki-sync` | `.opencode/commands/shiki-sync.md` | `shiki-runner` |
| `/shiki-doctor` | `.opencode/commands/shiki-doctor.md` | `shiki-runner` |

## Installed Agents

| agent | mode | responsibility |
| :--- | :--- | :--- |
| `shiki-runner` | `primary` | Root Shiki orchestration, plan selection, dependency order, output_files updates, and verification. |
| `shiki-reviewer` | `subagent` | Read-only review of code/spec alignment and test gaps. |
| `shiki-phase-wave` | `subagent` | Optional Design/Code wave execution for explicitly assigned items only. |

## Root-Controlled State

The `shiki-runner` role owns plan state and verification. It may call
`shiki-phase-wave` only after it has selected a bounded Design or Code wave,
checked dependencies, loaded task contracts, and confirmed all batch stop
conditions are clear.

Subagents must not update `_plan.md`, `output_files`, `active_task.md`,
`sync_plan.md`, `doctor_plan.md`, or Merge state. They return changed files,
verification evidence, and any `BLOCKED`, `MANUAL_DECISION`, or
`VERIFICATION_FAILED` result to `shiki-runner`.

## `/shiki-next` Mapping

OpenCode runs `/shiki-next` as `single_item` by default. It may use
`bounded_batch` or `phase_wave` only when `core-kernel/workflows/runner/batch.md`
allows every claimed item and all stop conditions are clear. Merge remains
root-controlled by default.

## Install Behavior

The installer writes only project-local `.opencode/commands/*.md`,
`.opencode/agents/*.md`, and `.shiki/adapters/opencode/manifest.json` files.
Re-running the installer updates Shiki-managed files, skips matching files, and
blocks existing user-owned command or agent files instead of overwriting them.
