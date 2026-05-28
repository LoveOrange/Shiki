# Project Spec Scope

Human entry point for project-level specs. Runtime uses `index.md` to route to
leaf specs; this README is not a task fact source.

## Files

| file | purpose |
| :--- | :--- |
| `README.md` | human entry point |
| `index.md` | runtime routing index |
| `_plan.md` | project task and output ledger |
| `architecture.md` | system purpose, module topology, entry points, dependencies |
| `ubiquitous_language.md` | shared vocabulary and core states |
| `techstack.md` | stack overview and implementation constraints |
| `integration.md` | cross-module communication and external infrastructure |

## Scope Rule

This directory is the current valid project baseline. Task state belongs in
`_plan.md`; routing belongs in `index.md`; durable facts belong in leaf specs.
