# Codex Adapter

## Scope

The Codex adapter installs a project-local Shiki command and skill surface:

- `.codex/prompts/shiki-*.md` command prompts for the canonical `/shiki-*` commands.
- `.codex/skills/shiki/SKILL.md` as the reusable Codex skill entry.
- `.shiki/adapters/codex/manifest.json` as generated adapter metadata.

This adapter follows `user-interface/adapters/tool_adapter_contract_v1.md`.
Command and skill bodies stay thin: they load Shiki runtime docs, task
contracts, workflows, and project rules instead of duplicating Core Kernel
logic.

Verification covers installed Codex adapter files and generated prompts.

## Project Rules

Codex must respect project-level instructions before running any Shiki command:

- Read applicable `AGENTS.md` files according to Codex scope rules.
- Keep Shiki framework files generic.
- Keep consumer-project facts in `shiki_context/`.
- Preserve unrelated user work.
- Treat Shiki Core Kernel as the source of truth for routing, task contracts,
  context loading, workflow binding, evidence, and gate state.

## Installed Commands

| command | installed file |
| :--- | :--- |
| `/shiki-init` | `.codex/prompts/shiki-init.md` |
| `/shiki-scan` | `.codex/prompts/shiki-scan.md` |
| `/shiki-new-feature <taskid>` | `.codex/prompts/shiki-new-feature.md` |
| `/shiki-status` | `.codex/prompts/shiki-status.md` |
| `/shiki-next` | `.codex/prompts/shiki-next.md` |
| `/shiki-apply` | `.codex/prompts/shiki-apply.md` |
| `/shiki-modify <target>` | `.codex/prompts/shiki-modify.md` |
| `/shiki-review` | `.codex/prompts/shiki-review.md` |
| `/shiki-sync` | `.codex/prompts/shiki-sync.md` |
| `/shiki-doctor` | `.codex/prompts/shiki-doctor.md` |
| `/shiki-fix <stacktrace>` | `.codex/prompts/shiki-fix.md` |
| `/shiki-web-spec [scope]` | `.codex/prompts/shiki-web-spec.md` |

If the host Codex build does not load project prompt files directly, the
project-local skill still provides equivalent native activation: ask Codex to
use the Shiki skill and the same canonical command name.

## Native Activation

Codex has two project-local entry points after install:

- Slash-style command prompts from `.codex/prompts/shiki-*.md`.
- The reusable project skill at `.codex/skills/shiki/SKILL.md`.

Both surfaces must dispatch to the same canonical command names and load
`user-interface/adapters/tool_adapter_contract_v1.md` before command-specific
runtime files. The skill is the fallback native surface when the host Codex
build does not expose project prompt files as slash commands.

Codex must read applicable `AGENTS.md` files before command execution and apply
those instructions alongside this adapter document. When instructions conflict,
project-level Shiki and Codex rules that preserve user work, dependency order,
and verification take precedence over generated prompt convenience text.

## Command Happy Paths

### `/shiki-scan`

Codex loads the adapter contract, this adapter document, `shiki.config.yaml`,
`tools-skills/scripts/scan.py`, `core-kernel/runtime/context_loading.md`, and
the Init plan. It runs Init baseline discovery through the deterministic script
when available, reports created or updated baseline specs, and stops on Core
Kernel blockers or verification failure.

### `/shiki-new-feature <taskid>`

Codex treats `$ARGUMENTS` as the required task id, runs
`tools-skills/scripts/new_feature.py`, confirms the feature workspace files
exist, and stops before `design_init`.

### `/shiki-status`

Codex loads the adapter contract, this adapter document,
`core-kernel/runtime/context_loading.md`,
`shiki_context/workspace/active_task.md`, and the current scope `_plan.md`.
It reports active scope, next runnable item, gate state, blockers, missing
files, adapter capability detection, candidate execution window, likely topology,
and confirms that no edits were made.

### `/shiki-next`

Codex loads the adapter contract, this adapter document,
`core-kernel/runtime/context_loading.md`,
`core-kernel/runtime/execution_session.md`,
`core-kernel/workflows/runner/next.md`, the active task, the current plan, and
selected task contracts before workflow text. Codex does not ask the user to
choose single-agent or agent-team mode. It auto-selects
`single_agent_session`, may claim a bounded execution window when Core Kernel
rules allow it, runs review after each item, updates plan state only after
verification and review pass, and stops on the adapter contract stop conditions.

### `/shiki-apply`

Codex runs the same adaptive execution session as `/shiki-next`, loads
`core-kernel/workflows/runner/apply.md`, and states that the apply compatibility
entry was used.

### `/shiki-modify <target>`

Codex treats `$ARGUMENTS` as the required target and requested change text. It
loads the adapter contract, this adapter document,
`core-kernel/runtime/context_loading.md`, the active task, the current plan, and
direct source/spec files related to the target. It returns `BLOCKED` when the
target is missing or ambiguous, edits only the requested bounded target, marks
downstream completed items `STALE` only when affected, and runs the smallest
meaningful verification.

### `/shiki-fix <stacktrace>`

Codex treats `$ARGUMENTS` as failure evidence, loads only related source and
current specs, diagnoses whether the write path is code -> code, code -> spec,
or feature -> spec, and routes writes to `/shiki-modify`, `/shiki-sync`, or an
explicit feature plan.

### `/shiki-web-spec [scope]`

Codex treats `$ARGUMENTS` as an optional scope, publishes Markdown specs through
`tools-skills/skills/spec-to-html/scripts/publish_docs.py`, reports the HTML
entry path and broken links, and leaves source Markdown unchanged unless asked.

## `/shiki-next` Adaptive Session

Codex runs `/shiki-next` as a `single_agent_session` because Codex has no Shiki
subagent surface in this adapter. The session still adapts how many items it
claims:

1. Read `shiki_context/workspace/active_task.md`.
2. Read the current scope `_plan.md`.
3. Load `core-kernel/runtime/execution_session.md`.
4. Select the first ready item and build a bounded execution window in plan
   order.
5. Estimate context cost from direct specs, source files, and verification
   output.
6. Load each item's task contract before loading its `workflow_ref`.
7. Execute one item at a time, run review and verification, then update
   `status`, `output_files`, `evidence`, and `review_result` when those columns
   exist.
8. Re-evaluate whether to continue after every reviewed item.

Codex may use `bounded_batch` inside the single-agent session only when all Core
Kernel execution-window rules in `core-kernel/workflows/runner/batch.md` hold.
The batch remains an internal strategy behind `/shiki-next`; users do not need a
separate primary command or a mode flag. Codex must state the selected topology
and internal mode before edits, list claimed item ids, load each item contract
separately, and stop before Merge, `BLOCKED`, `MANUAL_DECISION`, missing input,
ambiguous ownership, baseline writes, failed review, or failed verification.

When those conditions are not satisfied, Codex must stay in `single_item` mode
or return the adapter contract's `BLOCKED`, `MANUAL_DECISION`, or
`VERIFICATION_FAILED` report.

Codex must not select `agent_team_session`, `phase_wave`, or
`subagent_delegation`.

## Verification

Regression checks should install the Codex adapter into a sample project and
verify:

- `.codex/prompts/shiki-status.md`, `.codex/prompts/shiki-next.md`,
  `.codex/prompts/shiki-modify.md`, and the utility command prompts exist.
- `.codex/skills/shiki/SKILL.md` exists and lists the same canonical commands.
- Generated Codex files reference this adapter document, the adapter contract,
  applicable `AGENTS.md` rules, and Core Kernel runtime docs.
- `/shiki-modify <target>` generated content forwards `$ARGUMENTS` and blocks
  missing or ambiguous targets.
- `/shiki-next` generated content references `execution_session.md`, reports the
  automatically selected topology, and keeps Codex in `single_agent_session`.
