# Feature Plan: [FEAT-ID]

Task routing, output tracking, and contract version ledger.

## Meta

- **Feature ID**: [FEAT-ID]
- **Base Module**: [TBD]
- **Contract Version**: [TBD]
- **Created**: [date]

## Target Artifacts

| id | phase | kind | target | depends_on | contract | output_files |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| D1 | Design | model | `modules/{module}/designs/model.md` | - | `core-kernel/runtime/task_contracts/design/model.yaml` | |
| D2 | Design | persistence | `modules/{module}/designs/persistence.md` | D1 | `core-kernel/runtime/task_contracts/design/persistence.yaml` | |
| D3 | Design | acl | `modules/{module}/designs/acl.md` | D1 | `core-kernel/runtime/task_contracts/design/acl.yaml` | |
| D4 | Design | component | `modules/{module}/designs/component.md` | D1,D2,D3 | `core-kernel/runtime/task_contracts/design/component.yaml` | |
| D5 | Design | entrance_spec | `modules/{module}/entrances/{entrance}.md` | D1 | `core-kernel/runtime/task_contracts/design/entrance_spec.yaml` | |
| D6 | Design | flow | `modules/{module}/flows/{scenario}.md` | D1,D2,D3,D4 | `core-kernel/runtime/task_contracts/design/flow.yaml` | |
| CP | Design | code_contract | `code_contract.md` | D1-D6 | `core-kernel/runtime/task_contracts/design/code_contract.yaml` | |
| C1 | Code | entity | - | CP | `core-kernel/runtime/task_contracts/code/entity.yaml` | |
| C2 | Code | interface_skeletons | - | C1 | `core-kernel/runtime/task_contracts/code/interface_skeletons.yaml` | |
| C3 | Code | feature_logic | - | C2 | `core-kernel/runtime/task_contracts/code/feature_logic.yaml` | |
| C4 | Code | infrastructure | - | C3 | `core-kernel/runtime/task_contracts/code/infrastructure.yaml` | |
| C5 | Code | adapter | - | C4 | `core-kernel/runtime/task_contracts/code/adapter.yaml` | |
| M1 | Merge | feature_merge | baseline | C5 | `core-kernel/runtime/task_contracts/merge/feature_merge.yaml` | |

Delete rows that do not apply.
