# [ModuleName] - Domain Model

## 0. Baseline Delta (Feature Overlay Only)

Fill this section only when this file lives under
`features/{feature}/modules/{module}/...`. Baseline files should use
`N/A - baseline current valid`.

| change_type | baseline_ref | overlay_ref | change_summary | merge_action |
| :--- | :--- | :--- | :--- | :--- |
| `[reuse/add/extend/modify/deprecate]` | `modules/{module}/designs/model.md#[section]` / `N/A` | `features/{feature}/modules/{module}/designs/model.md#[section]` | change relative to baseline | no-op / add / merge / replace / remove |

### Reuse Decision Gate

| scope_slice | checked_candidates | reuse_decision | add_justification |
| :--- | :--- | :--- | :--- |
| `design_brief §...` / upstream spec | baseline/source entities, VOs, enums, error codes, and states checked | `reuse/extend/modify/add/MANUAL_DECISION` with reason | Every `add` names source evidence and why reuse/extension is not correct; use `N/A` when there are no additions. |

## 1. Ubiquitous Language

| code term | business term | definition | source |
| :--- | :--- | :--- | :--- |
| TBD | TBD | TBD | TBD |

## 2. Entities

This file describes the domain model only. Database tables, columns, primary
keys, foreign keys, indexes, and DDL belong in `persistence.md`.

| entity | field | type | constraint | invariant |
| :--- | :--- | :--- | :--- | :--- |
| `Xxx` | `id` | `Long` | required | immutable identity |

## 3. Value Objects

| value object | field | type | constraint |
| :--- | :--- | :--- | :--- |
| `XxxVO` | `value` | `String` | required |

## 4. State Transitions

| object | source state | trigger | target state | rule |
| :--- | :--- | :--- | :--- | :--- |
| `Xxx` | `INIT` | `submit()` | `ACTIVE` | TBD |

## 5. Domain Relationship Diagram

Use Mermaid `classDiagram`. Show aggregates, entities, value objects, external
domain references, and domain methods. Do not use database `erDiagram`, table
names, column definitions, PK/FK markers, indexes, or DDL.

```mermaid
classDiagram
    direction LR
    class Xxx {
        +Long id
        +XxxStatusEnum status
        +submit()
    }
    class XxxVO {
        +String value
    }
    class ExternalRef {
        +Long id
    }
    Xxx "1" *-- "1" XxxVO : owns
    Xxx "0..*" --> "1" ExternalRef : references
```

## 6. Error Codes

| error code | trigger | message |
| :--- | :--- | :--- |
| `XXX_INVALID` | TBD | TBD |
