# Flow: [ScenarioName]

Scenario-level behavior and call-chain design.

## 0. Baseline Delta (Feature Overlay Only)

Fill this section only when this file lives under
`features/{feature}/modules/{module}/...`. Baseline files should use
`N/A - baseline current valid`.

| change_type | baseline_ref | overlay_ref | change_summary | merge_action |
| :--- | :--- | :--- | :--- | :--- |
| `[reuse/add/extend/modify/deprecate]` | `modules/{module}/flows/[scenario].md#[section]` / `N/A` | `features/{feature}/modules/{module}/flows/[scenario].md#[section]` | change relative to baseline | no-op / add / merge / replace / remove |

### Reuse Decision Gate

| scope_slice | checked_candidates | reuse_decision | add_justification |
| :--- | :--- | :--- | :--- |
| scenario / entrance / model scope | baseline/source flows, participants, branches, error paths, and robustness rules checked | `reuse/extend/modify/add/MANUAL_DECISION` with reason | Every `add` names source evidence and why reuse/extension is not correct; use `N/A` when there are no additions. |

## 1. Approval Checklist

| check | result | note |
| :--- | :--- | :--- |
| external entrance reviewed | TBD | |
| transaction boundary reviewed | TBD | |
| idempotency reviewed | TBD | |
| capacity reviewed | TBD | |

## 2. Model Summary

| entity | fields used | states used |
| :--- | :--- | :--- |
| `Xxx` | TBD | TBD |

## 3. Entrance Summary

| field | value |
| :--- | :--- |
| exposed | yes / no |
| caller | TBD |
| auth | TBD |
| compatibility | TBD |

## 4. Business Activity Diagram

```mermaid
flowchart TD
    Start([Start]) --> Validate{Validate}
    Validate -- pass --> Execute[Execute business action]
    Validate -- fail --> Reject[Return business error]
    Execute --> End([Done])
    Reject --> End
```

## 5. Sequence Diagram

```mermaid
sequenceDiagram
    participant C as XxxController
    participant AS as XxxService
    participant DS as XxxDomainService
    participant Repo as XxxRepository
    C->>AS: command
    AS->>DS: apply business rule
    DS->>Repo: load/save entity
    AS-->>C: response
```

## 6. Exception Handling

| scenario | error code | location | handling |
| :--- | :--- | :--- | :--- |
| TBD | `XXX_INVALID` | AppService | throw AppException |

## 7. Robustness Constraints

| target | transaction | idempotency | concurrency | capacity |
| :--- | :--- | :--- | :--- | :--- |
| `XxxService.process()` | required | N/A | N/A | reuse existing |

## Done

- [ ] Entrance spec is created when the flow adds or changes an exposed entry.
- [ ] New model changes are reflected in `model.md`.
- [ ] New error codes are reflected in `model.md`.
- [ ] Sequence participants match `component.md`.
