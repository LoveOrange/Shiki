# Context Loading

Runtime uses three progressive steps. L0/L1/L2 describe Spec levels, not loading phases.

| step | minimum context |
| :--- | :--- |
| locate | `active_task.md` and one parsed active Plan |
| task input | current item, direct dependencies, Canonical Contract, and required artifact bodies |
| execution rules | Contract `workflow_ref`, plus optional tech-contract and Team Norm paths |

## Kernel Task Tools

- `next_task` routes one Task and builds a Context Envelope.
- `complete_task` validates fixed or declared outputs and updates `output_files` plus `active_task.next`.
- `plan_add_items` adds validated Canonical rows without rewriting the Plan.

CLI automatic mode calls these Python APIs. Prompt manual mode uses `shiki task next`, `shiki task complete`, and `shiki plan add-item`. Neither interface owns a second Router.

## Routing Rules

- Parse the active Plan once and prefer `active_task.next`, an explicit item, then the first ready row.
- Resolve Alias directly to Canonical; reject Alias chains.
- When a required input is missing, route one unique ready producer. Return MANUAL_DECISION for multiple producers and BLOCKED when none exists.
- Required bodies are inlined once. Optional inputs, project tech contracts, and Team Norm are path manifests.
- The Context Envelope does not repeat the full Plan, history, whole module directories, or the source tree.
- Provider or Prompt Agent executes exactly one selected Task and must not reroute it.
- `_plan.md.output_files` is completion truth. `active_task.md` and `last_run.md` are focus/recovery hints only.

## Brownfield Design

Design begins with baseline/source evidence and a reuse check. Missing baseline backed by source should be repaired through Init/Sync before idealized feature specs are written. Feature targets are overlay-relative; baseline writes wait for Merge or explicit maintenance.

## Command Rules

- `scan` bootstraps or advances `workspace/_plan.md` through the same Task Tools.
- `next` routes one feature Task per Agent session.
- `sync` and `doctor` use bounded workspace Plans and process one row per call.
- `status` and `review` are read-only.
- Uncertainty returns BLOCKED or MANUAL_DECISION instead of broad speculative loading.
