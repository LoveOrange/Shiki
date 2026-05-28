# Project Spec Index

Agent/runtime routing entry. It records stable project spec files and load paths
only; do not put design body text here.

## Scope Files

| file | role |
| :--- | :--- |
| `README.md` | human entry point |
| `index.md` | context routing |
| `_plan.md` | project task and output ledger |

## Project Spec Files

| id | path | load when |
| :--- | :--- | :--- |
| `project_architecture` | `architecture.md` | project scan, module location, cross-module design |
| `project_ubiquitous` | `ubiquitous_language.md` | concept extraction, model design, state naming |
| `project_techstack` | `techstack.md` | implementation and tech-rule checks |
| `project_integration` | `integration.md` | external dependencies and infrastructure design |

## Module Registry

| module | path | index | status |
| :--- | :--- | :--- | :--- |
| *(scan or design task appends here)* | `modules/[module]/` | `modules/[module]/index.md` | `pending` |

## Loading Protocol

1. Read the current `_plan.md` first.
2. Read this index only when project-level routing is needed.
3. Load leaf specs from the paths listed here.
4. If this index conflicts with a leaf spec, trust the leaf spec and fix the index.
