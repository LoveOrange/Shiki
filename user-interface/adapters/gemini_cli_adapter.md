# Gemini CLI Adapter

## Scope

The Gemini CLI adapter installs project-local TOML command files under
`.gemini/commands/` for the canonical Shiki command surface:

- `.gemini/commands/shiki-*.toml` command files.
- `.shiki/adapters/gemini/manifest.json` generated adapter metadata.

This adapter follows `user-interface/adapters/tool_adapter_contract_v1.md`.
Gemini command files must stay thin: each command loads Shiki Core runtime docs,
task contracts, and workflow references instead of duplicating Core Kernel logic.

Gemini CLI discovers project commands from `<project>/.gemini/commands/`.
Project-local commands override same-named user commands. Each command file uses
the TOML file format with a required `prompt` field and optional `description`
field. After command files change in a running Gemini CLI session, run
`/commands reload` before invoking the Shiki commands.

## Installed Commands

| command | installed file |
| :--- | :--- |
| `/shiki-init` | `.gemini/commands/shiki-init.toml` |
| `/shiki-scan` | `.gemini/commands/shiki-scan.toml` |
| `/shiki-new-feature <taskid>` | `.gemini/commands/shiki-new-feature.toml` |
| `/shiki-status` | `.gemini/commands/shiki-status.toml` |
| `/shiki-next` | `.gemini/commands/shiki-next.toml` |
| `/shiki-apply` | `.gemini/commands/shiki-apply.toml` |
| `/shiki-modify <target>` | `.gemini/commands/shiki-modify.toml` |
| `/shiki-review` | `.gemini/commands/shiki-review.toml` |
| `/shiki-sync` | `.gemini/commands/shiki-sync.toml` |
| `/shiki-doctor` | `.gemini/commands/shiki-doctor.toml` |
| `/shiki-fix <stacktrace>` | `.gemini/commands/shiki-fix.toml` |
| `/shiki-web-spec [scope]` | `.gemini/commands/shiki-web-spec.toml` |

The file path determines the slash command name, so `shiki-status.toml` exposes
`/shiki-status`.

## Native Activation

After install, Gemini CLI exposes the generated files as slash commands in the
current project:

- `/shiki-status` from `.gemini/commands/shiki-status.toml`
- `/shiki-next` from `.gemini/commands/shiki-next.toml`
- `/shiki-modify <target>` from `.gemini/commands/shiki-modify.toml`
- Utility commands such as `/shiki-scan`, `/shiki-new-feature <taskid>`,
  `/shiki-fix <stacktrace>`, and `/shiki-web-spec [scope]` from their matching
  `.gemini/commands/shiki-*.toml` files

The generated TOML prompt is the native command body. It loads this adapter
document, the shared adapter contract, and the relevant Core Kernel runtime
files before selecting work. The command body must not replace task contracts,
runner workflows, verification expectations, or stop-state reporting.

## Argument Forwarding

Commands with trailing user input must include Gemini's `{{args}}` placeholder
in the TOML prompt. Gemini CLI replaces that placeholder with the text typed
after the command name, so the adapter can pass task ids, targets, failure
evidence, or web-spec scope through to Shiki.

For `/shiki-modify <target>`, the generated prompt must treat `{{args}}` as
untrusted user input, then:

- Load `core-kernel/runtime/context_loading.md`.
- Read `shiki_context/workspace/active_task.md`.
- Read the current scope `_plan.md`.
- Load direct specs and source files related to the target.
- Return `BLOCKED` when `{{args}}` is empty, missing a target, or ambiguous.
- Mark downstream completed items `STALE` only when the change affects them.
- Run the smallest meaningful verification.

## Command Happy Paths

### `/shiki-scan`

Gemini loads the adapter contract, this adapter document, `shiki.config.yaml`,
`tools-skills/scripts/scan.py`, `core-kernel/runtime/context_loading.md`, and
the Init plan. It runs Init baseline discovery, reports created or updated
baseline specs, and stops on Core Kernel blockers or verification failure.

### `/shiki-new-feature <taskid>`

Gemini treats `{{args}}` as the required task id, runs
`tools-skills/scripts/new_feature.py`, confirms the feature workspace files
exist, and stops before `design_init`.

### `/shiki-status`

Gemini loads the adapter contract, this adapter document,
`core-kernel/runtime/context_loading.md`,
`shiki_context/workspace/active_task.md`, and the current scope `_plan.md`.
It reports active scope, next runnable item, gate state, blockers, missing
files, adapter capability detection, candidate execution window, likely topology,
and confirms that no edits were made.

### `/shiki-next`

Gemini loads the adapter contract, this adapter document,
`core-kernel/runtime/context_loading.md`,
`core-kernel/runtime/execution_session.md`,
`core-kernel/workflows/runner/next.md`, the active task, the current plan, and
selected task contracts before loading each contract `workflow_ref`. Gemini does
not ask the user to choose single-agent or agent-team mode. It auto-selects
`single_agent_session`, states the selected topology and internal execution mode
before edits, updates plan state only after verification and review pass, and
stops on the adapter contract stop conditions.

### `/shiki-apply`

Gemini runs the same adaptive execution session as `/shiki-next`, loads
`core-kernel/workflows/runner/apply.md`, and states that the apply compatibility
entry was used.

### `/shiki-modify <target>`

Gemini treats `{{args}}` as the required target and requested change text. It
loads the adapter contract, this adapter document,
`core-kernel/runtime/context_loading.md`, the active task, the current plan, and
direct source/spec files related to the target. It returns `BLOCKED` when the
target is missing or ambiguous, edits only the requested bounded target, marks
downstream completed items `STALE` only when affected, and runs the smallest
meaningful verification.

### `/shiki-fix <stacktrace>`

Gemini treats `{{args}}` as failure evidence, loads only related source and
current specs, diagnoses the route, and sends writes to `/shiki-modify`,
`/shiki-sync`, or an explicit feature plan.

### `/shiki-web-spec [scope]`

Gemini treats `{{args}}` as an optional scope, publishes Markdown specs through
`tools-skills/skills/spec-to-html/scripts/publish_docs.py`, reports the HTML
entry path and broken links, and leaves source Markdown unchanged unless asked.

## `/shiki-next` Adaptive Session

Gemini runs `/shiki-next` as `single_agent_session` because Gemini CLI has no
Shiki subagent surface. It may use `bounded_batch` inside that session only when
`core-kernel/workflows/runner/batch.md` permits every claimed item and all stop
conditions are clear. Each item still loads its own task contract, runs review,
and updates its own `status`, `output_files`, `evidence`, and `review_result`
only after verification and review pass. This adapter must not select
`agent_team_session`, `phase_wave`, or `subagent_delegation`.

## Install Behavior

The installer writes only project-local `.gemini/commands/*.toml` files and
`.shiki/adapters/gemini/manifest.json`. Re-running the installer updates only
Shiki-managed files, skips matching files, and blocks existing user-owned command
files instead of overwriting them.

## Verification

Regression checks should install the Gemini adapter into a sample project and
verify:

- `.gemini/commands/shiki-status.toml`, `.gemini/commands/shiki-next.toml`,
  `.gemini/commands/shiki-modify.toml`, and the utility command files exist.
- Generated Gemini command files are valid TOML with `description` and `prompt`
  fields.
- Generated prompts reference this adapter document, the adapter contract,
  `core-kernel/runtime/context_loading.md`, and relevant Core Kernel workflows
  or task contract paths.
- `/shiki-modify <target>` generated content forwards `{{args}}` and blocks
  missing or ambiguous targets.
- The Gemini manifest records `gemini-cli`, project-local install support, and
  only `single_agent_session` execution topology plus single-agent execution
  modes.
