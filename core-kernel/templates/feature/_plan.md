# Feature Plan: [FEAT-ID]

Atomic Task routing and output ledger.

## Meta

- **Feature ID**: [FEAT-ID]
- **Base Module**: [TBD]
- **Spec Revision**: AS-IS
- **Created**: [date]

## Target Outputs

`target` is relative to the current feature root. `modules/{module}/...` means a feature overlay, not baseline `shiki_context/modules/{module}/...`.

| id | phase | target | depends_on | contract | output_files |
| :--- | :--- | :--- | :--- | :--- | :--- |
| D1 | Design | `modules/{module}/designs/model.md` | | `design/model.yaml` | |
| D2 | Design | `modules/{module}/designs/persistence.md` | D1 | `design/persistence.yaml` | |
| D3 | Design | `modules/{module}/designs/acl.md` | D1 | `design/acl.yaml` | |
| D4 | Design | `modules/{module}/designs/component.md` | D1,D2,D3 | `design/component.yaml` | |
| D5 | Design | `modules/{module}/entrances/{entrance}.md` | D1 | `design/entrance_spec.yaml` | |
| T1 | Design | `tests/test_cases.md` | D5 | `test/api_case_spec.yaml` | |
| C1 | Code | | D1 | `code/entity.yaml` | |
| C2 | Code | | D1,D4 | `code/interface_skeletons.yaml` | |
| C3 | Code | | C2,D3 | `code/feature_logic.yaml` | |
| C4 | Code | | C1,C2,D2,D3 | `code/infrastructure.yaml` | |
| C5 | Code | | C2,D4,D5 | `code/adapter.yaml` | |
| T2 | Code | `tests/test_cases.md` | C1,C2,C3,C4,C5 | `test/unit_case_spec.yaml` | |
| T3 | Code | | T2,C1,C2,C3,C4,C5 | `test/unit_test_code.yaml` | |
| T4 | Test | | T1,C5 | `test/api_integration_test_code.yaml` | |
| T5 | Test | test evidence | T3,T4 | `test/run.yaml` | |
| M1 | Merge | baseline | T5 | `merge/feature_merge.yaml` | |

Delete rows that do not apply. If there is no external entrance, omit T1 and T4.
