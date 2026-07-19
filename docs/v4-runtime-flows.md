# Shiki v4 Runtime Flows

## Shared Task lifecycle

```text
Plan -> task next -> Contract -> Context Envelope -> Provider result
                                                    |
                      PASS -> task complete -> output_files
             other status -> stop, no ledger mutation
```

## CLI automatic

1. Route one Task through `task next`.
2. Start a fresh Codex or Claude process with the prepared prompt.
3. Require a status-first result.
4. On `PASS`, validate and record outputs.
5. At the configured Task or phase boundary, start a separate fresh Review
   process.
6. Stop on `CHANGE_REQUEST`, `BLOCKED`, `FAILED`, or `MANUAL_DECISION`.
7. Otherwise route the next Task until the CLI boundary is reached.

## Prompt manual

1. The developer invokes `/shiki-next [item]`.
2. The adapter calls `task next`.
3. The current Coding Agent session executes exactly one Context Envelope.
4. On `PASS`, the adapter calls `task complete`.
5. The adapter stops and returns control.
6. Review occurs only through a later explicit `/shiki-review` invocation.

The Prompt track never silently adopts the CLI session lifecycle.
