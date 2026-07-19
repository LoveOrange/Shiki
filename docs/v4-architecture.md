# Shiki v4 Architecture

```text
CLI automatic track                     Prompt manual track
shiki next / scan                       /shiki-next
        |                                    |
        +---------- Core Kernel -------------+
                   task next
                   Context Envelope
                   task complete
                   plan add-item
                         |
              Plan + Task Contracts
              Workflows + tech rules
                         |
                project/spec outputs
```

## Core Kernel

- Router: chooses one ready Task and enforces dependencies.
- Contract resolver: expands Alias to Canonical and validates ownership.
- Context builder: loads direct inputs and references once.
- Task tools: prepare, complete, and expand deterministic Plan state.

## CLI automatic track

The CLI starts one fresh configured Codex or Claude process per Task. It parses
the status-first result, validates outputs, then starts a separate fresh Review
process when the configured granularity requires Review. Codex Review uses a
read-only sandbox; Claude Review uses `plan` permission mode.

## Prompt manual track

Generated tool adapters call the same Task tools. Execution remains in the
developer's current Coding Agent session, and Review is a separate explicit
developer command.

Provider-specific prompts and manifests cannot change Kernel routing or Task
completion semantics.
