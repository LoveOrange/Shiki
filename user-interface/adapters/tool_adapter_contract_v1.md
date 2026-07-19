# Shiki Tool Adapter Contract v1

This contract defines the Prompt-track boundary for project-local Coding Agent
adapters. It is intentionally thinner than the Core Kernel.

## Shared Kernel

Both collaboration tracks use the same:

- Plan and active scope files
- Canonical and Alias Task Contracts
- Workflow references and Context Envelope
- `shiki task next [item]`
- `shiki task complete ...`
- `shiki plan add-item ...`
- status-first result protocol

Adapters must not implement another Router, context loader, completion ledger,
batch selector, or hidden Review loop.

## Prompt-track ownership

In the Prompt track:

- the developer owns the current Coding Agent session;
- one command invocation executes at most one Kernel-prepared Task;
- the Task runs in the current session rather than a fresh provider session;
- Review runs only when the developer invokes `/shiki-review`;
- the adapter returns control after the Task result is recorded;
- task batching, phase waves, and automatic subagent delegation are forbidden.

This differs intentionally from the CLI automatic track, where Shiki owns
provider sessions and Review timing.

## Task protocol

For `/shiki-next [item]` and compatibility `/shiki-apply [item]`:

1. Call `shiki task next [item]`.
2. Treat the returned Context Envelope as the complete Task authority.
3. Execute exactly one Task in the current Coding Agent session.
4. Put `PASS`, `BLOCKED`, `FAILED`, or `MANUAL_DECISION` on the first result line.
5. On `PASS`, call the returned `shiki task complete ...` command with every
   produced output. Use `--noop <reason>` only when the contract permits no file
   output.
6. On any other status, do not write completion state.
7. Stop and return control to the developer.

Review uses the same protocol plus `CHANGE_REQUEST`, and never edits files.

## Generated manifest

Every adapter manifest records:

```json
{
  "collaboration_track": "prompt_manual",
  "execution_modes": ["single_task_current_session"],
  "session_owner": "developer",
  "review_owner": "developer"
}
```

## Managed files

The installer updates only files containing its Shiki managed marker. Existing
user-owned files are reported as blocked and never overwritten. Obsolete managed
phase-wave agent files may be removed during a v4 adapter repair.
