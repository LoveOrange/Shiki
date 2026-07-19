# OpenCode Adapter

OpenCode exposes Shiki Prompt-track commands in `.opencode/commands/shiki-*.md`.
It also installs a primary `shiki-runner` and a read-only `shiki-reviewer` role.

The runner executes exactly one Kernel-prepared Task in the developer's current
session. The reviewer is used only by explicit developer Review and cannot edit
files or Plan state. The v4 Prompt track removes any old Shiki-managed
`shiki-phase-wave` role.

The generated `.shiki/adapters/opencode/manifest.json` declares
`single_task_current_session`. Core behavior is defined by
`tool_adapter_contract_v1.md`.
