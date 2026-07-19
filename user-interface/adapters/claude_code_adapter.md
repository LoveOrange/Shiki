# Claude Code Adapter

Claude Code exposes Shiki Prompt-track commands in
`.claude/commands/shiki-*.md`.

Each `/shiki-next` invocation executes one Kernel-prepared Task in the current
Claude Code session and returns control. Review is explicit and developer-owned.
The v4 Prompt track does not install or use a phase-wave worker; an old
Shiki-managed `.claude/agents/shiki-phase-wave.md` is removed during repair.

The generated `.shiki/adapters/claude/manifest.json` declares
`single_task_current_session`. Core behavior is defined by
`tool_adapter_contract_v1.md`.
