# Feature Spec Scope: [FEAT-ID]

Human entry point for a feature workspace. Runtime reads `index.md` and `_plan.md`.

## Files

| file | purpose |
| :--- | :--- |
| `README.md` | human entry point |
| `index.md` | feature routing index |
| `_plan.md` | feature task ledger |
| `design_brief.md` | requirement input and clarification |
| `modules/{module}/` | overlay specs aligned with module baseline paths |
| `code_contract.md` | coding fact source after design |
| `tests/test_cases.md` | feature test specification |

## Scope Rule

Feature specs are working overlays. Long-lived facts enter project/module
baseline only after merge.
