# Codex Adapter

Codex exposes Shiki Prompt-track commands in `.codex/prompts/shiki-*.md` and a
matching skill in `.codex/skills/shiki/SKILL.md`.

Each `/shiki-next` invocation calls the shared Kernel, executes one prepared
Task in the developer's current Codex session, records completion only on
`PASS`, and returns control. Codex must not batch Tasks or trigger Review
automatically.

The generated `.shiki/adapters/codex/manifest.json` declares
`single_task_current_session`, with both session and Review timing owned by the
developer. Core behavior is defined by `tool_adapter_contract_v1.md`.
