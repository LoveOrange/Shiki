# Feature Spec Scope: [FEAT-ID]

Human entry point for a feature workspace. Runtime reads `index.md` and `_plan.md`.

## Files

| file | purpose |
| :--- | :--- |
| `README.md` | human entry point |
| `index.md` | feature routing index |
| `_plan.md` | feature task and output ledger |
| `design_brief.md` | requirement input and clarification |
| `modules/{module}/` | overlay specs aligned with module baseline paths |
| `code_contract.md` | optional implementation slice for small-context coding tasks |
| `tests/test_cases.md` | feature test specification |

## Scope Rule

- Feature specs are working overlays. Long-lived facts enter project/module baseline only after merge.
- Every leaf spec under `modules/{module}/...` must use `§0 Baseline Delta` to mark `reuse/add/extend/modify/deprecate` against baseline.
- Code/Test tasks default to current L2 AS-IS leaf specs. `code_contract.md` is temporary and must not override leaf specs.
- Task state and dependencies belong only in `_plan.md`, not in this README.
