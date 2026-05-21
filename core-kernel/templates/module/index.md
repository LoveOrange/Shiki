# Module Index: [ModuleName]

Routing index for stable module artifacts. Do not put design body text here.

## Business Boundary

- **Core Responsibility**: TBD
- **Domain Entities**: TBD
- **Out of Scope**: TBD

## Module Summary

| field | value |
| :--- | :--- |
| status | pending / scanned / designed |

## Design Artifacts

| kind | id | path | purpose |
| :--- | :--- | :--- | :--- |
| `model` | `model` | `designs/model.md` | domain model, states, errors |
| `persistence` | `persistence` | `designs/persistence.md` | storage model, mapping, indexes, DDL |
| `acl` | `acl` | `designs/acl.md` | boundaries, dependencies, anti-corruption interfaces |
| `component` | `component` | `designs/component.md` | components and interface contracts |

## Entrance Spec Artifacts

| kind | id | path | method | endpoint |
| :--- | :--- | :--- | :--- | :--- |
| `entrance_spec` | `[entrance]` | `entrances/[entrance].md` | TBD | TBD |

## Flow Artifacts

| kind | id | path | entrance |
| :--- | :--- | :--- | :--- |
| `flow` | `[scenario]` | `flows/[scenario].md` | TBD |

## Loading Protocol

1. Read active task and current plan first.
2. Load only direct leaf specs required by the current item.
3. Load existing draft targets when iterating on an artifact.
4. Do not load all module artifacts by default.
5. Prefer plan item, target, direct dependencies, and test spec when context is tight.
