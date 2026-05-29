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
| `/shiki-status` | `.codex/prompts/shiki-status.md` |
| `/shiki-next` | `.codex/prompts/shiki-next.md` |
| `/shiki-modify <target>` | `.codex/prompts/shiki-modify.md` |
| `/shiki-review` | `.codex/prompts/shiki-review.md` |
| `/shiki-sync` | `.codex/prompts/shiki-sync.md` |
| `/shiki-doctor` | `.codex/prompts/shiki-doctor.md` |

If the host Codex build does not load project prompt files directly, the
project-local skill still provides equivalent native activation: ask Codex to
use the Shiki skill and the same canonical command name.

## `/shiki-next` Selection

Codex runs `/shiki-next` in `single_item` mode by default:

1. Read `shiki_context/workspace/active_task.md`.
2. Read the current scope `_plan.md`.
3. Select the first ready item.
4. Load that item's task contract.
5. Load the contract `workflow_ref`.
6. Execute one item and update `output_files` only after verification passes.

Codex may switch `/shiki-next` to `bounded_batch` only when all Core Kernel batch
rules in `core-kernel/workflows/runner/batch.md` hold. The batch remains an
internal strategy behind `/shiki-next`; users do not need a separate primary
command. Codex must state the selected mode before edits, list claimed item ids,
load each item contract separately, and stop before Merge, `BLOCKED`,
`MANUAL_DECISION`, missing input, ambiguous ownership, baseline writes, or
failed verification.

When those conditions are not satisfied, Codex must stay in `single_item` mode
or return the adapter contract's `BLOCKED`, `MANUAL_DECISION`, or
`VERIFICATION_FAILED` report.
