# Gemini CLI Adapter

## Scope

The Gemini CLI adapter installs project-local TOML command files under
`.gemini/commands/` for the canonical Shiki command surface.

This adapter follows `user-interface/adapters/tool_adapter_contract_v1.md`.
Gemini command files must stay thin: each command loads Shiki Core runtime docs,
task contracts, and workflow references instead of duplicating Core Kernel logic.

## Installed Commands

| command | installed file |
| :--- | :--- |
| `/shiki-init` | `.gemini/commands/shiki-init.toml` |
| `/shiki-status` | `.gemini/commands/shiki-status.toml` |
| `/shiki-next` | `.gemini/commands/shiki-next.toml` |
| `/shiki-modify <target>` | `.gemini/commands/shiki-modify.toml` |
| `/shiki-review` | `.gemini/commands/shiki-review.toml` |
| `/shiki-sync` | `.gemini/commands/shiki-sync.toml` |
| `/shiki-doctor` | `.gemini/commands/shiki-doctor.toml` |

The file path determines the slash command name, so `shiki-status.toml` exposes
`/shiki-status`.

## Argument Forwarding

`/shiki-modify <target>` must include Gemini's `{{args}}` placeholder in the TOML
prompt. Gemini CLI replaces that placeholder with the text typed after the
command name, so the adapter can pass the target and requested change through to
Shiki's modify strategy.

The generated prompt must treat `{{args}}` as user input, then:

- Load `core-kernel/runtime/context_loading.md`.
- Read `shiki_context/workspace/active_task.md`.
- Read the current scope `_plan.md`.
- Load direct specs and source files related to the target.
- Mark downstream completed items `STALE` only when the change affects them.
- Run the smallest meaningful verification.

## `/shiki-next` Mapping

Gemini runs `/shiki-next` in `single_item` mode by default. It may use
`bounded_batch` only when `core-kernel/workflows/runner/batch.md` permits every
claimed item and all stop conditions are clear. Each item still loads its own
task contract and updates its own `output_files` only after verification passes.

## Install Behavior

The installer writes only project-local `.gemini/commands/*.toml` files and
`.shiki/adapters/gemini/manifest.json`. Re-running the installer updates only
Shiki-managed files, skips matching files, and blocks existing user-owned command
files instead of overwriting them.
