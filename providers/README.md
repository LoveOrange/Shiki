# Providers

This module owns execution backend adapters.

The CLI automatic track supports two explicit Providers:

- `CodexProvider` starts `codex exec --ephemeral` with a workspace-write Task
  sandbox or read-only Review sandbox.
- `ClaudeProvider` starts `claude --print --no-session-persistence` with
  `acceptEdits` for Tasks or `plan` for Review.

Choose one with `provider.name: codex|claude` in `shiki.config.yaml`,
`SHIKI_PROVIDER`, or `shiki next --provider codex|claude`. Optional
`provider.model` and `provider.executable` values select a model or CLI binary;
the equivalent environment variables are `SHIKI_PROVIDER_MODEL`,
`SHIKI_CODEX_EXECUTABLE`, and `SHIKI_CLAUDE_EXECUTABLE`.

Providers execute exactly one supplied Context Envelope. They do not route
Tasks, select batches, maintain the Plan ledger, or turn Review prose into edits.
Shiki Core owns routing and deterministic completion; the CLI Orchestrator owns
fresh-session and Review boundaries.
