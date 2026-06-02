# Execution Session

`/shiki-next` starts an adaptive execution session. A session may advance one or
more ready plan items, but each plan item remains the atomic ledger row with its
own task contract, workflow, output, evidence, and review result.

User commands do not ask for `single_agent` or `agent_team`. The coordinator
selects the topology from adapter metadata, plan state, direct context size, and
stop conditions.

## Concepts

| concept | meaning |
| :--- | :--- |
| `coordinator` | Root controller for plan state, dependency order, topology selection, review gates, and final reporting. |
| `execution_session` | One `/shiki-next` invocation, from preflight to stop report. |
| `execution_window` | Ordered claim of ready items that the current session may attempt. |
| `single_agent_session` | One agent/thread performs coordination, execution, review, verification, and plan updates. |
| `agent_team_session` | Root coordinator delegates bounded Design/Code item work to workers, then reviews and updates plan state itself. |
| `task_executor` | Executes exactly one assigned item from its task contract and direct context. |
| `review_gate` | Required check after item execution and before plan state is marked done. |
| `phase_gate` | Human-facing stop after a phase reaches a reviewable boundary. |

## Session Lifecycle

1. Load L0 state: adapter contract/manifest, `context_loading.md`,
   `active_task.md`, and the current plan.
2. Detect adapter capabilities from `.shiki/adapters/<tool>/manifest.json` when
   available. If the manifest is missing or ambiguous, fall back to
   `single_agent_session`.
3. Select the first ready item and build a candidate execution window in plan
   order.
4. Estimate direct context cost from required inputs, target files, dependent
   leaf specs, target source, and expected verification output. Use host context
   usage when the tool exposes it; otherwise use file size and dependency count
   as a conservative proxy.
5. Choose topology:
   - Use `single_agent_session` when subagents are unavailable, the window has
     one item, the phase is Init/Requirement/Merge, the task is sync/doctor, or
     root state must stay in one context.
   - Use `agent_team_session` only when the adapter manifest says isolated worker
     context or subagents are supported, every claimed item is Design or Code,
     dependencies and ownership are clear, and root can verify after workers
     return.
6. State the selected topology, claimed item ids, stop boundary, and review plan
   before edits.
7. Execute one item at a time. Load that item's task contract before workflow
   text, and load only direct context for that item.
8. Run the item review gate. The item may be marked done only after execution,
   task-contract checks, verification, and review pass.
9. If review returns a bounded change request, retry the same item within the
   task contract retry policy. Do not advance to later items before the current
   item passes or stops.
10. After each item, re-evaluate stop conditions, context budget, and phase gate.
11. Stop with a stable report: topology, completed items, stopped item if any,
    files changed, evidence, review result, verification, and next human action.

## Plan State

New or migrated plans should include these columns:

```text
status | output_files | evidence | review_result
```

Allowed status values:

```text
READY | RUNNING | DONE | STALE | BLOCKED | MANUAL_DECISION | VERIFICATION_FAILED
```

Compatibility:

- Older plans without `status`, `evidence`, or `review_result` remain valid.
- Empty `output_files` means unfinished when `status` is absent.
- `output_files` beginning with `STALE`, `BLOCKED`, or `MANUAL_DECISION` keeps
  its legacy meaning until doctor migrates the plan.
- `status=DONE` requires non-empty `output_files`, evidence, and passing review
  unless the task contract explicitly declares a read-only done condition.

## Review Gate

Every item completion must pass review before the coordinator marks it done.
Review checks:

- task contract `checks` and `done_condition`
- output files exist or were updated as declared
- evidence traces to direct source/spec facts
- spec-code alignment for Code items
- smallest meaningful verification result
- no downstream item should be marked complete when the current item failed

Review outcomes:

| outcome | coordinator action |
| :--- | :--- |
| `PASS` | Record evidence/review result, set `status=DONE`, update `output_files`, then decide whether to continue. |
| `CHANGE_REQUEST` | Retry the same item only when the change is bounded and retry policy allows it. |
| `BLOCKED` | Record blocker and stop. |
| `MANUAL_DECISION` | Record decision needed and stop for the user. |
| `VERIFICATION_FAILED` | Record failure and stop; do not continue to later items. |

## Stop Conditions

Stop before claiming or continuing when any condition applies:

- Merge phase, baseline write, or root-only maintenance step is next.
- `BLOCKED`, `MANUAL_DECISION`, `VERIFICATION_FAILED`, or stale item without a
  clear target appears.
- Required input, task contract, workflow, tech contract, direct source, or
  direct spec is missing.
- Target owner, module boundary, feature scope, or code/spec mapping is
  ambiguous.
- Continuing requires full prompt docs, full module tree, full source tree, or
  unrelated repository scan.
- Verification or review for the previous item fails.
- Context budget would leave too little room for direct dependencies, review,
  and verification output.
- A phase gate is reached and the phase result is ready for human review.

## Agent Team Boundaries

When `agent_team_session` is selected:

- The root coordinator selects items, checks dependencies, builds assignments,
  owns review, and updates plan state.
- Workers execute only assigned Design or Code items.
- Workers do not select plan items, edit `_plan.md`, mark items done, run Merge,
  or change `active_task.md`, `sync_plan.md`, or `doctor_plan.md`.
- Workers return changed files, evidence, verification they ran, and any
  blocker.
- Root verification and review still decide whether the item is done.

## Human Review Boundary

Humans should not need to review every plan item. Normal handoff points are:

- phase gate reached
- manual decision required
- review or verification failed
- context budget exhausted with meaningful progress completed
- Merge approval needed
