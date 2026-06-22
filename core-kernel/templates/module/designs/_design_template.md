# Design File: [FileName]

> `type`: `[model/persistence/component/acl]`

## 0. Baseline Delta (Feature Overlay Only)

Fill this section only when this file lives under
`features/{feature}/modules/{module}/...`. Baseline files should use
`N/A - baseline current valid`.

| change_type | baseline_ref | overlay_ref | change_summary | merge_action |
| :--- | :--- | :--- | :--- | :--- |
| `[reuse/add/extend/modify/deprecate]` | `modules/{module}/designs/[file].md#[section]` / `N/A` | `features/{feature}/modules/{module}/designs/[file].md#[section]` | change relative to baseline | no-op / add / merge / replace / remove |

### Reuse Decision Gate

| scope_slice | checked_candidates | reuse_decision | add_justification |
| :--- | :--- | :--- | :--- |
| current task scope | baseline/source facts checked | `reuse/extend/modify/add/MANUAL_DECISION` with reason | Every `add` names source evidence and why reuse/extension is not correct; use `N/A` when there are no additions. |

## Purpose

- [what this file is responsible for]

## Definition

- [model: fields, invariants, states]
- [component: interfaces, methods, returns]
- [acl: support interfaces and boundaries]

## Depends

- [dependent files, or `None`]

## Done

- [ ] Satisfies `done_when`
