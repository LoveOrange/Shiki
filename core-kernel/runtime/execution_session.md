# Collaboration Tracks

Shiki V4 supports two collaboration tracks over one deterministic Kernel. The
CLI automatic track gives every Task a fresh Provider session; the Prompt
manual track keeps execution in the developer's current Coding Agent session.

| track | execution | session ownership | Review |
| :--- | :--- | :--- | :--- |
| CLI automatic | The Orchestrator routes a Task and starts a fresh Provider process for every Task. | Shiki owns Worker session boundaries. | The Orchestrator starts a separate Review process at the configured task or phase boundary. |
| Prompt manual | An installed `/shiki-*` prompt runs in the developer's current Coding Agent session. | The developer owns the interactive session. | The developer decides when to invoke `/shiki-review` or edit the result. |

Both tracks call the same `next_task`, `complete_task`, and `plan_add_items` implementation and share Plan, Contract, Workflow, Context Envelope, and result statuses. They do not share Provider access, session lifecycle, or Review timing.

## CLI Automatic Track

1. The Orchestrator calls `next_task` for one Plan item.
2. Context Builder creates the minimal Context Envelope.
3. The configured Codex or Claude Provider starts a new process/session and executes exactly one Workflow.
4. Provider output starts with a supported status line.
5. Kernel post-checks the Plan ledger and output files.
6. At a configured Review boundary, the Orchestrator starts another Provider process with a read-only Review prompt.
7. `CHANGE_REQUEST` stops automatic progress. Shiki never parses Review prose into an automatic modify action.

`orchestrate.granularity` controls the stop boundary: `task`, `phase`, or `feature`. Every Task remains one Worker session even when the Orchestrator continues.

## Prompt Manual Track

1. The installed prompt calls `shiki task next [item]`.
2. The current Coding Agent executes exactly the returned Context Envelope.
3. The Agent calls `shiki task complete ...` after Workflow verification.
4. The command returns control to the developer.
5. The developer decides when Review runs; Review or correction happens only
   when explicitly requested.

Prompt files must not implement a second Router, completion ledger, batch selector, or hidden Review loop.

## Result Protocol

Task statuses are `PASS`, `BLOCKED`, `FAILED`, and `MANUAL_DECISION`. Review additionally supports `CHANGE_REQUEST`.

Only `PASS` can advance a Plan. `output_files` contains existing paths or `NOOP: <reason>`; it never contains blocker or Review state.
