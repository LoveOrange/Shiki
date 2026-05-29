# User Interface

This module owns Shiki user entry surfaces.

- `docs/CHEATSHEET.md` remains the prompt entry panel.
- `adapters/tool_adapter_contract_v1.md` defines the shared tool-native command contract.
- `adapters/codex_adapter.md` defines the Codex command and skill surface.
- `adapters/claude_code_adapter.md` defines the Claude Code command and subagent surface.
- `adapters/gemini_cli_adapter.md` defines the Gemini CLI project command surface.
- `adapters/opencode_adapter.md` defines the OpenCode command and agent role surface.
- Future CLI/API/UI entry logic should live here or delegate here.
- User Interface must call Core Kernel contracts and must not define separate phase, task, workflow, or evidence truth.
