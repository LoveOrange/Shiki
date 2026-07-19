# Gemini CLI Adapter

Gemini CLI exposes Shiki Prompt-track TOML commands in
`.gemini/commands/shiki-*.toml`.

Each `/shiki-next` invocation executes one Kernel-prepared Task in the current
Gemini CLI session, completes it only on `PASS`, and returns control. It does not
batch Tasks or trigger Review automatically.

The generated `.shiki/adapters/gemini/manifest.json` declares
`single_task_current_session`. Reload Gemini commands after installation. Core
behavior is defined by `tool_adapter_contract_v1.md`.
