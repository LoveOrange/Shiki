# Module Index: [ModuleName]

Routing index for stable module files. Do not put design body text here.

## Business Boundary

- **Core Responsibility**: TBD
- **Domain Entities**: TBD
- **Out of Scope**: TBD

## Module Summary

| field | value |
| :--- | :--- |
| status | pending / scanned / designed |

## Design Files

| id | path | purpose |
| :--- | :--- | :--- |
| `model` | `designs/model.md` | domain model, states, errors |
| `persistence` | `designs/persistence.md` | storage model, mapping, indexes, DDL |
| `acl` | `designs/acl.md` | boundaries, dependencies, anti-corruption interfaces |
| `component` | `designs/component.md` | components and interface contracts |

## Entrance Spec Files

| id | path | method | endpoint |
| :--- | :--- | :--- | :--- |
| `[entrance]` | `entrances/[entrance].md` | TBD | TBD |

## Flow Files

| id | path | entrance |
| :--- | :--- | :--- |
| `[scenario]` | `flows/[scenario].md` | TBD |

## Loading Protocol

1. Read active task and current plan first.
2. Load only direct leaf specs required by the current item.
3. Load existing draft targets when iterating on a file.
4. Do not load all module files by default.
5. Prefer plan item, target, direct dependencies, and test spec when context is tight.
