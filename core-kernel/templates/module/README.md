# Module Spec Scope: [ModuleName]

Human entry point for this module. Runtime uses `index.md` to route to leaf specs.

## Files

| file | purpose |
| :--- | :--- |
| `README.md` | human entry point |
| `index.md` | runtime routing index |
| `_plan.md` | module task ledger |
| `designs/` | model, persistence, ACL, and component design |
| `entrances/` | external entrance contracts |
| `flows/` | scenario flows and call chains |

## Scope Rule

This directory is the current valid baseline for `[ModuleName]`. Detailed facts
belong in leaf specs, not in this README.
