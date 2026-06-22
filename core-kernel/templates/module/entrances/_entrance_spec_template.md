# Entrance Spec: [EntranceName]

Defines a module entry contract for callers. Do not describe private sequencing here.

## 0. Baseline Delta (Feature Overlay Only)

Fill this section only when this file lives under
`features/{feature}/modules/{module}/...`. Baseline files should use
`N/A - baseline current valid`.

| change_type | baseline_ref | overlay_ref | change_summary | merge_action |
| :--- | :--- | :--- | :--- | :--- |
| `[reuse/add/extend/modify/deprecate]` | `modules/{module}/entrances/[entrance].md#[section]` / `N/A` | `features/{feature}/modules/{module}/entrances/[entrance].md#[section]` | change relative to baseline | no-op / add / merge / replace / remove |

### Reuse Decision Gate

| scope_slice | checked_candidates | reuse_decision | add_justification |
| :--- | :--- | :--- | :--- |
| entrance section / upstream flow | baseline/source entrances, endpoints, methods, request/response contracts, and error codes checked | `reuse/extend/modify/add/MANUAL_DECISION` with reason | Every `add` names source evidence and why reuse/extension is not correct; use `N/A` when there are no additions. |

## 1. Summary

| field | value |
| :--- | :--- |
| name | [EntranceName] |
| type | REST / MQ / Job / RPC |
| caller | TBD |
| related flow | `flows/[scenario].md` |

## 2. Access

| field | value |
| :--- | :--- |
| method | GET / POST / PUT / DELETE / TCP / Scheduled Task |
| endpoint | TBD |
| auth | TBD |
| idempotency key | N/A |

## 3. Request

| location | field | type | required | rule |
| :--- | :--- | :--- | :--- | :--- |
| Body | `field` | `String` | yes | TBD |

## 4. Response

| field | type | description |
| :--- | :--- | :--- |
| `code` | `String` | result code |
| `data` | `Object` | response payload |

## 5. Error Codes

| code | condition | message |
| :--- | :--- | :--- |
| `XXX_INVALID` | TBD | TBD |

## 6. Examples

```http
POST /api/example
Content-Type: application/json

{}
```
