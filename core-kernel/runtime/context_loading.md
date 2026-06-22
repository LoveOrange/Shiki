# Context Loading

Normal execution uses three layers. Fallback is explicit and only applies when
plan, contract, index, or evidence state is missing.

| layer | load |
| :--- | :--- |
| L0 | `active_task.md`, current plan, and current runner/workflow |
| L1 | selected task contract, target, direct dependencies, needed `index.md`, and test spec |
| L2 | workflow, template, and selected `shiki_context/constitution/tech_contracts/<stack_name>/` files |
| Fallback | `core-kernel/runtime/phase_contract.md` only when routing or gates are blocked |

Design tasks also load `core-kernel/runtime/design_contract.md`. That contract
requires a reuse gate before writing feature overlay design facts.

## Core Concepts

Small models only need these stable concepts:

| concept | meaning |
| :--- | :--- |
| `scope` | current operation scope: workspace / project / module / feature |
| `stage` | current development stage: Init / Requirement / Design / Code / Test / Merge |
| `plan` | current task queue; usually `_plan.md`, or a workspace temporary plan for multi-step maintenance |
| `item` | one atomic row in a plan |
| `execution_session` | one `/shiki-next` invocation, from preflight to stop report |
| `execution_window` | a bounded ordered claim of ready items for one adaptive session |
| `batch` | compatibility name for an execution window inside a capable session |
| `index` | leaf spec routing table |
| `leaf spec` | current valid fact body |

Task contracts and workflows are loaded after an item is selected. Models do not
need to memorize a separate task-kind list. `STALE`, `BLOCKED`, and
`MANUAL_DECISION` are item states, not extra routing concepts.

## Command And Plan Rules

Commands first read `active_task.md`, the current plan, and the contract needed
by the current item. Any command that changes long-lived facts, source code,
Context Store structure, or naturally requires multiple steps must go through a
plan.

| command | plan strategy |
| :--- | :--- |
| `scan` | Use `workspace/_plan.md` to advance the Init queue. |
| `new feature` | Create a feature bootstrap `_plan.md`, then stop. |
| `next` | Start an adaptive execution session; the coordinator may advance one or more ready items through review gates. |
| `apply` | Compatibility entry, currently equivalent to `next`. |
| `batch` / `auto` | Compatibility/internal strategy for claiming a bounded execution window; each item still uses its own task contract and plan update. |
| `modify` | Use the current `_plan.md` for impact analysis and mark downstream completed items `STALE` when affected. |
| `sync` | Create a workspace temporary plan, then sync one leaf spec at a time. |
| `doctor` | Diagnose read-only by default; after confirmation create a workspace temporary plan, then repair one deterministic item at a time. |
| `status` | Read the plan only; do not create or modify plans. |
| `review` | Read plan/evidence/diff only; do not create or modify plans. |
| `fix` | Diagnose and route by default; code/spec writes must move to `modify`, `sync`, or an explicit feature plan. |
| `web spec` | Generate a derived view only; it is not a development ledger. |

## Rules

- Plan items are the atomic ledger. Do not merge plan rows just because a strong coding agent can do more in one session.
- `next` and `apply` start an adaptive execution session governed by `core-kernel/runtime/execution_session.md`.
- A session may claim multiple ready items only when the execution-window rules in `core-kernel/workflows/runner/batch.md` and the session stop conditions are satisfied.
- Every item in a session must load its own task contract before workflow execution and must pass review before plan state is marked done.
- A session stops before Merge, `MANUAL_DECISION`, `BLOCKED`, missing required inputs, ambiguous target ownership, baseline writes, failed verification, failed review, or a phase gate.
- Runner/status starts from L0 and does not inspect the whole repository.
- After selecting an item, load its task contract before loading workflow text.
- The task contract is the execution contract; the workflow is the readable procedure.
- New or migrated plans should include `status`, `evidence`, and `review_result` columns; older plans remain compatible through `output_files`.
- Do not maintain a separate task-kind field; read the current item `contract`.
- Workflows declare the exact tech contract slices they need.
- `tech_stacks` comes from `shiki.config.yaml`.
- `init.py` copies default tech contracts into `shiki_context/constitution/tech_contracts/`.
- Runtime loads project-owned tech contracts, not the read-only defaults under `shiki/tech-stacks/`.
- README files are human entry points and are not normal task facts.
- Index files route to leaf specs; they do not carry task state or full design content.
- User-facing next step must be a top-level prompt; item and contract ids are diagnostics only.
- Feature targets are feature-root relative; feature overlays are writable, baseline paths are not baseline write targets until merge or explicit maintenance.
- Design items must complete the Design Contract Reuse Gate before writing overlay facts; each `add` needs brief or upstream evidence plus a reason reuse/extension is not correct.
- Code/Test default to feature L2 AS-IS specs; explicit `reuse` refs may load baseline leaf snippets, and `code_contract.md` is only an optional implementation slice.
- Cross-module callers load the callee entrance and model by default; load flow only when side effects matter.
- Do not load persistence, ACL, component, full prompt docs, full module directories, or full source trees by default.
- Module-level `sync` must first create a workspace temporary plan; execution reads and updates one leaf spec at a time.
- `doctor` migration, recovery, and structure repair must first create a workspace temporary plan; unconfirmed or ambiguous cases return diagnosis, `MANUAL_DECISION`, or `BLOCKED`.
- When blocked, return `BLOCKED` with the missing file or decision instead of loading more context speculatively.
