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

| id | phase | target | depends_on | contract | status | output_files | evidence | review_result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| D1 | Design | `modules/{module}/designs/model.md` | - | `core-kernel/runtime/task_contracts/design/model.yaml` | READY | | | |
| D2 | Design | `modules/{module}/designs/persistence.md` | D1 | `core-kernel/runtime/task_contracts/design/persistence.yaml` | READY | | | |
| D3 | Design | `modules/{module}/designs/acl.md` | D1 | `core-kernel/runtime/task_contracts/design/acl.yaml` | READY | | | |
| D4 | Design | `modules/{module}/designs/component.md` | D1,D2,D3 | `core-kernel/runtime/task_contracts/design/component.yaml` | READY | | | |
| D5 | Design | `modules/{module}/entrances/{entrance}.md` | D1 | `core-kernel/runtime/task_contracts/design/entrance_spec.yaml` | READY | | | |
| D6 | Design | `modules/{module}/flows/{scenario}.md` | D1,D2,D3,D4 | `core-kernel/runtime/task_contracts/design/flow.yaml` | READY | | | |
| T1 | Design | `tests/test_cases.md` | D5,D6 | `core-kernel/runtime/task_contracts/test/api_case_spec.yaml` | READY | | | |
| C1 | Code | - | D1,D6 | `core-kernel/runtime/task_contracts/code/entity.yaml` | READY | | | |
| C2 | Code | - | D1,D4 | `core-kernel/runtime/task_contracts/code/interface_skeletons.yaml` | READY | | | |
| C3 | Code | - | C2,D3,D6 | `core-kernel/runtime/task_contracts/code/feature_logic.yaml` | READY | | | |
| C4 | Code | - | C1,C2,D2,D3 | `core-kernel/runtime/task_contracts/code/infrastructure.yaml` | READY | | | |
| C5 | Code | - | C2,D4,D5 | `core-kernel/runtime/task_contracts/code/adapter.yaml` | READY | | | |
| T2 | Test | `tests/test_cases.md` | C1,C2,C3,C4,C5 | `core-kernel/runtime/task_contracts/test/unit_case_spec.yaml` | READY | | | |
| T3 | Test | - | T2,C1,C2,C3,C4,C5 | `core-kernel/runtime/task_contracts/test/unit_test_code.yaml` | READY | | | |
| T4 | Test | - | T1,C5 | `core-kernel/runtime/task_contracts/test/api_integration_test_code.yaml` | READY | | | |
| T5 | Test | test evidence | T3,T4 | `core-kernel/runtime/task_contracts/test/run_and_route.yaml` | READY | | | |
| M1 | Merge | baseline | T5 | `core-kernel/runtime/task_contracts/merge/feature_merge.yaml` | READY | | | |

Delete rows that do not apply.
When a Spec -> Spec update invalidates downstream completed work, mark the affected
item `status` as `STALE` and record the reason in `review_result`. Older plans
may continue to mark `output_files` as `STALE: <reason>` until doctor migrates
the plan.
If a feature has no entrance/API, omit T1 and T4; T5 then depends only on T3.
