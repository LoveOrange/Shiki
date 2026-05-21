# Entrance Spec: [EntranceName]

Defines a module entry contract for callers. Do not describe internal sequencing here.

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
