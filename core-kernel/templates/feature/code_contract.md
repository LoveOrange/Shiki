# Code Contract: [FEAT-ID]

The single coding fact source after design. Coder agents may only implement what
this file declares. All `[ ]` confirmations must be checked before coding.

## 0. Metadata

- **Feature ID**: [FEAT-ID]
- **Contract Version**: [TBD]

## 1. Entities

| type | name | field | field type | constraint | invariant | confirmed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Entity | `[Name]` | `field` | `String` | required | TBD | [ ] |

## 2. DTOs

| DTO | field | type | required | constraint | description | confirmed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `[XxxDTO]` | `field` | `String` | yes | maxLength=64 | TBD | [ ] |

## 3. Interfaces

| layer | interface | method | parameters | return | contract | confirmed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| App/Domain/Repo/Support | `[Xxx]` | `doAction` | `XxxDTO` | `Long` | TBD | [ ] |

## 4. State Transitions

| object | source state | trigger | target state | precondition | side effect | confirmed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `[Entity]` | `INIT` | `submit()` | `PROCESSING` | TBD | N/A | [ ] |

## 5. Error Codes

| error code | trigger | external message | confirmed |
| :--- | :--- | :--- | :--- |
| `XXX_INVALID` | TBD | TBD | [ ] |

## 6. Non-functional Rules

| target | transaction | idempotency | concurrency | confirmed |
| :--- | :--- | :--- | :--- | :--- |
| `[Class.method]` | yes/no | key/N/A | lock/version/N/A | [ ] |

## 7. Change Log

| version | summary |
| :--- | :--- |
| v1 | initial draft |
