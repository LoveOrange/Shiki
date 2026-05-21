# Feature Spec Index: [FEAT-ID]

Agent/runtime routing entry for this feature. Do not put design body text here.

## Scope Files

| file | role |
| :--- | :--- |
| `README.md` | human entry point |
| `index.md` | context routing |
| `_plan.md` | feature task ledger |

## Feature Spec Artifacts

| kind | id | path | load when |
| :--- | :--- | :--- | :--- |
| `design_input` | `design_brief` | `design_brief.md` | requirement and design initialization |
| `contract_spec` | `code_contract` | `code_contract.md` | code and test work |
| `test_spec` | `test_cases` | `tests/test_cases.md` | test design and acceptance coverage |

## Generated Spec Artifacts

| kind | id | path | source item |
| :--- | :--- | :--- | :--- |
| *(design_init appends here)* | | | |

## Loading Protocol

1. Read `_plan.md` first.
2. Read this index only when feature leaf-spec routing is needed.
3. Load direct dependencies from the current item.
4. If this index conflicts with a leaf spec, trust the leaf spec and fix the index.
