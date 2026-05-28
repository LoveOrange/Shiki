# Feature Plan: [FEAT-ID]

Task routing, output tracking, and stale-state ledger.

## Meta

- **Feature ID**: [FEAT-ID]
- **Base Module**: [TBD]
- **Spec Revision**: AS-IS
- **Created**: [date]

## Target Outputs

`target` is relative to the current feature root. `modules/{module}/...` means
`shiki_context/features/{feature}/modules/{module}/...`, not baseline
`shiki_context/modules/{module}/...`.

| id | phase | target | depends_on | contract | output_files |
| :--- | :--- | :--- | :--- | :--- | :--- |
| D1 | Design | `modules/{module}/designs/model.md` | - | `core-kernel/runtime/task_contracts/design/model.yaml` | |
| D2 | Design | `modules/{module}/designs/persistence.md` | D1 | `core-kernel/runtime/task_contracts/design/persistence.yaml` | |
| D3 | Design | `modules/{module}/designs/acl.md` | D1 | `core-kernel/runtime/task_contracts/design/acl.yaml` | |
| D4 | Design | `modules/{module}/designs/component.md` | D1,D2,D3 | `core-kernel/runtime/task_contracts/design/component.yaml` | |
| D5 | Design | `modules/{module}/entrances/{entrance}.md` | D1 | `core-kernel/runtime/task_contracts/design/entrance_spec.yaml` | |
| D6 | Design | `modules/{module}/flows/{scenario}.md` | D1,D2,D3,D4 | `core-kernel/runtime/task_contracts/design/flow.yaml` | |
| C1 | Code | - | D1,D6 | `core-kernel/runtime/task_contracts/code/entity.yaml` | |
| C2 | Code | - | D1,D4 | `core-kernel/runtime/task_contracts/code/interface_skeletons.yaml` | |
| C3 | Code | - | C2,D3,D6 | `core-kernel/runtime/task_contracts/code/feature_logic.yaml` | |
| C4 | Code | - | C1,C2,D2,D3 | `core-kernel/runtime/task_contracts/code/infrastructure.yaml` | |
| C5 | Code | - | C2,D4,D5 | `core-kernel/runtime/task_contracts/code/adapter.yaml` | |
| M1 | Merge | baseline | C5 | `core-kernel/runtime/task_contracts/merge/feature_merge.yaml` | |

Delete rows that do not apply.
When a Spec -> Spec update invalidates downstream completed work, mark the affected
item `output_files` as `STALE: <reason>` so the runner treats it as unfinished.
