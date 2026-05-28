# Feature Spec Index: [FEAT-ID]

Agent/runtime routing entry for this feature. It records feature spec files and
load paths only; do not put design body text here.

## Scope Files

| file | role |
| :--- | :--- |
| `README.md` | human entry point |
| `index.md` | context routing |
| `_plan.md` | feature task and output ledger |

## Feature Spec Files

| id | path | load when |
| :--- | :--- | :--- |
| `design_brief` | `design_brief.md` | requirement and design initialization |
| `code_contract` | `code_contract.md` | optional temporary implementation slice when direct specs exceed context budget |
| `test_cases` | `tests/test_cases.md` | test design and acceptance coverage |

## Generated Spec Files

After design_init, record only leaf specs declared by `_plan.md`.
Feature module specs use overlay paths relative to the current feature root.
`modules/{module}/...` means `shiki_context/features/{feature}/modules/{module}/...`,
not baseline `shiki_context/modules/{module}/...`.
Each feature overlay leaf spec must mark `§0 Baseline Delta` with
`reuse/add/extend/modify/deprecate`.

| id | path | source item |
| :--- | :--- | :--- |
| *(design_init appends here)* | | |

## Loading Protocol

1. Read `_plan.md` first.
2. Read this index only when feature leaf-spec routing is needed.
3. Load direct dependencies from the current item `target` and `depends_on` fields.
4. If this index conflicts with a leaf spec, trust the leaf spec and fix the index.
