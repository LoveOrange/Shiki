# Context Loading

Normal execution uses three layers. Fallback is explicit and only applies when
plan, contract, index, or evidence state is missing.

| layer | load |
| :--- | :--- |
| L0 | `active_task.md`, current `_plan.md`, and the current runner/workflow |
| L1 | selected task contract, target, direct dependencies, needed `index.md`, and test spec |
| L2 | workflow, template, and selected `shiki_context/constitution/tech_contracts/<stack_name>/` files |
| Fallback | `core-kernel/runtime/phase_contract.md` only when routing or gates are blocked |

## Rules

- Execute one plan item per apply run, then stop.
- Runner/status starts from L0 and does not inspect the whole repository.
- After selecting an item, load its task contract before loading workflow text.
- The task contract is the execution contract; the workflow is the readable procedure.
- Workflows declare the exact tech contract slices they need.
- `tech_stacks` comes from `shiki.config.yaml`.
- `init.py` copies default tech contracts into `shiki_context/constitution/tech_contracts/`.
- Runtime loads project-owned tech contracts, not the read-only defaults under `shiki/tech-stacks/`.
- README files are human entry points and are not normal task facts.
- Index files route to leaf specs; they do not carry task state or full design content.
- Cross-module callers load the callee entrance and model by default; load flow only when side effects matter.
- Do not load persistence, ACL, component, full CHEATSHEET, full module directories, or full source trees by default.
- When blocked, return `BLOCKED` with the missing file or decision instead of loading more context speculatively.
